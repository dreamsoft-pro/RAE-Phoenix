# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Feniks API - RESTful interface for the Feniks system.
"""
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from feniks.config.settings import settings
from feniks.core.models.domain import FeniksReport, SessionSummary
from feniks.core.models.types import MetaReflection
from feniks.core.policies.manager import PolicyManager
from feniks.core.reflection.engine import MetaReflectionEngine
from feniks.infra.logging import get_logger
from feniks.infra.metrics import get_metrics_collector
from feniks.infra.metrics_prometheus import get_prometheus_collector
from feniks.security.auth import AuthenticationError, User, get_auth_manager
from feniks.security.rbac import Permission, RBACManager

log = get_logger("apps.api")
security = HTTPBearer(auto_error=False)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="Feniks API",
    description="""
# Feniks: Meta-Reflective Code Analysis Engine

Enterprise-grade system for analyzing code quality, detecting reasoning patterns, and generating actionable recommendations.

## Features

- **Post-Mortem Analysis**: Analyze completed sessions for failures, inefficiencies, and patterns
- **Longitudinal Trend Detection**: Track quality and cost trends over time
- **Cost & Quality Policies**: Enforce guardrails and budgets
- **RAE Integration**: Store meta-reflections for long-term learning
- **Prometheus Metrics**: Export operational metrics for monitoring

## Authentication

All endpoints (except `/health` and `/metrics/prometheus`) require authentication using:
- **JWT Bearer Token**: `Authorization: Bearer <token>`
- **API Key**: `Authorization: <api-key>`

Set `auth_enabled=false` in configuration to disable authentication (not recommended for production).

## Permissions

- **VIEWER**: View reports and metrics
- **ANALYST**: View + analyze sessions
- **REFACTORER**: Analyst + execute refactorings
- **ADMIN**: Full access

## Quick Start

```bash
# Analyze a session
curl -X POST https://api.feniks.io/sessions/analyze \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"project_id": "my-project", "session_summary": {...}}'

# Get report
curl https://api.feniks.io/report/rep-session-123 \\
  -H "Authorization: Bearer $TOKEN"

# Get metrics (Prometheus format)
curl https://api.feniks.io/metrics/prometheus
```

## Rate Limits

- **Default**: 100 requests/minute per IP
- **Analyze endpoint**: 10 requests/minute (compute-intensive)

## Support

- Documentation: https://docs.feniks.io
- GitHub: https://github.com/your-org/feniks
- Issues: https://github.com/your-org/feniks/issues
    """,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "sessions",
            "description": "Session analysis operations. Submit sessions for post-mortem analysis and retrieve results.",
        },
        {
            "name": "reports",
            "description": "Report retrieval and management. Access meta-reflections and analysis results.",
        },
        {
            "name": "patterns",
            "description": "Error pattern analysis. View aggregated patterns from longitudinal analysis.",
        },
        {
            "name": "metrics",
            "description": "System metrics and observability. Access operational metrics in JSON or Prometheus format.",
        },
        {"name": "health", "description": "Health checks and system status."},
    ],
    contact={"name": "Feniks Team", "email": "support@feniks.io", "url": "https://feniks.io"},
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"},
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Dependencies ---
reflection_engine = MetaReflectionEngine()
policy_manager = PolicyManager()
metrics = get_metrics_collector()
prometheus_metrics = get_prometheus_collector()
auth_manager = get_auth_manager(jwt_secret=settings.jwt_secret)
rbac_manager = RBACManager()

# In-memory storage for reports (replace with DB in production)
_reports_db: Dict[str, FeniksReport] = {}
_reflections_db: Dict[str, List[MetaReflection]] = {}

# --- Authentication Dependencies ---


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[User]:
    """
    Get current authenticated user from JWT token or API key.
    Returns None if authentication is disabled or no credentials provided.
    """
    if not settings.auth_enabled:
        # Auth disabled - return mock admin user
        from feniks.security.auth import UserRole

        return User(
            user_id="system", username="system", email="system@feniks.local", role=UserRole.ADMIN, projects=["*"]
        )

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})

    try:
        token = credentials.credentials
        user = auth_manager.authenticate(token)
        log.debug(f"Authenticated user: {user.username}")
        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})


def require_permission(permission: Permission):
    """
    Dependency factory for requiring specific permission.
    """

    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not rbac_manager.has_permission(user.role, permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission.value} required")
        return user

    return permission_checker


# --- Models ---


class AnalyzeSessionRequest(BaseModel):
    project_id: str
    session_summary: SessionSummary


class AnalyzeSessionResponse(BaseModel):
    report_id: str
    status: str
    violation_count: int


# --- Endpoints ---


@app.post(
    "/sessions/analyze",
    response_model=AnalyzeSessionResponse,
    tags=["sessions"],
    summary="Analyze a session",
    responses={
        200: {"description": "Analysis completed successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Analysis failed"},
    },
)
@limiter.limit("10/minute")  # Stricter limit for compute-intensive operation
async def analyze_session(
    req: Request,
    request: AnalyzeSessionRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission(Permission.ANALYZE_CODE)),
):
    """
    Submit a session for Post-Mortem analysis.

    Analyzes a completed agent session to detect:
    - Reasoning failures and loops
    - Cost overruns
    - Quality issues (empty thoughts, forbidden patterns)

    **Requires**: ANALYZE_CODE permission

    **Example**:
    ```json
    {
      "project_id": "my-project",
      "session_summary": {
        "session_id": "sess-123",
        "duration": 120.5,
        "success": true,
        "reasoning_traces": [...],
        "cost_profile": {
          "total_tokens": 5000,
          "cost_usd": 0.15
        }
      }
    }
    ```
    """
    log.info(f"User {user.username} analyzing session for project {request.project_id}")
    report_id = f"rep-{request.session_summary.session_id}"

    # Run analysis synchronously for now (can be backgrounded)
    try:
        # 1. Post-Mortem Analysis
        reflections = reflection_engine.run_post_mortem(request.session_summary, project_id=request.project_id)

        # Store results
        _reflections_db[report_id] = reflections

        # Count violations
        violations = [r for r in reflections if r.impact.value in ["critical", "refactor-recommended"]]

        log.info(f"Analysis complete for {report_id}: {len(reflections)} reflections, {len(violations)} violations")

        return AnalyzeSessionResponse(report_id=report_id, status="completed", violation_count=len(violations))

    except Exception as e:
        log.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/report/{report_id}",
    response_model=List[MetaReflection],
    tags=["reports"],
    summary="Get analysis report",
    responses={
        200: {"description": "Report retrieved successfully"},
        404: {"description": "Report not found"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    },
)
async def get_report(report_id: str, user: User = Depends(require_permission(Permission.VIEW_REPORTS))):
    """
    Get the analysis report (meta-reflections) for a session.

    Returns a list of meta-reflections generated from post-mortem analysis.

    **Requires**: VIEW_REPORTS permission

    **Report ID Format**: `rep-{session_id}`
    """
    if report_id not in _reflections_db:
        raise HTTPException(status_code=404, detail="Report not found")

    return _reflections_db[report_id]


@app.get(
    "/patterns/errors",
    tags=["patterns"],
    summary="Get error patterns",
    responses={
        200: {"description": "Error patterns retrieved"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    },
)
async def get_error_patterns(user: User = Depends(require_permission(Permission.VIEW_REPORTS))):
    """
    Get aggregated error patterns from longitudinal analysis.

    Returns common patterns detected across multiple sessions.

    **Requires**: VIEW_REPORTS permission
    """
    # Mock implementation for MVP
    # In real world, query DB/Vector Store for common patterns
    return {
        "patterns": [
            {"pattern": "Empty Reasoning", "count": 15, "severity": "medium"},
            {"pattern": "Loop Action", "count": 5, "severity": "high"},
        ]
    }


@app.get(
    "/metrics",
    tags=["metrics"],
    summary="Get system metrics (JSON)",
    responses={
        200: {"description": "Metrics retrieved"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    },
)
async def get_metrics(user: User = Depends(require_permission(Permission.VIEW_METRICS))):
    """
    Get system metrics in JSON format.

    Returns operational metrics including uptime, operations count, and quality scores.

    **Requires**: VIEW_METRICS permission
    """
    return metrics.get_metrics()


@app.get(
    "/metrics/prometheus",
    tags=["metrics"],
    summary="Get Prometheus metrics",
    responses={200: {"description": "Prometheus metrics in text format", "content": {"text/plain": {}}}},
)
async def prometheus_metrics_endpoint():
    """
    Prometheus metrics endpoint in standard text/plain format.

    **Public endpoint** - No authentication required (designed for Prometheus scraping).

    **Metrics exported**:
    - `feniks_cost_total`: Total cost in USD
    - `feniks_quality_score`: Current quality score (0.0 - 1.0)
    - `feniks_recommendations_count`: Total recommendations generated
    - `feniks_operations_total`: Total operations executed
    - `feniks_errors_total`: Total errors encountered
    - `feniks_operation_duration_seconds`: Operation duration histogram
    - `feniks_uptime_seconds`: Service uptime
    """
    metrics_data = prometheus_metrics.export_prometheus()
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get(
    "/health",
    tags=["health"],
    summary="Health check with dependency status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is degraded (one or more dependencies unhealthy)"},
    },
)
async def health_check():
    """
    Health check endpoint with dependency status.

    Checks health of:
    - Qdrant vector database
    - RAE (Reflective Agent Engine) if enabled

    Returns 200 if all dependencies are healthy, 503 if degraded.

    **Public endpoint** - No authentication required.
    """
    health_status = {"status": "ok", "version": "0.1.0", "dependencies": {}}

    # Check Qdrant
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        collections = client.get_collections()
        health_status["dependencies"]["qdrant"] = {
            "status": "healthy",
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "collections": len(collections.collections),
        }
        log.debug(f"Qdrant health check: OK ({len(collections.collections)} collections)")
    except Exception as e:
        health_status["dependencies"]["qdrant"] = {"status": "unhealthy", "error": str(e)}
        log.warning(f"Qdrant health check failed: {e}")

    # Check RAE if enabled
    if settings.rae_enabled:
        try:
            from feniks.adapters.rae_client import create_rae_client

            rae = create_rae_client()
            if rae:
                rae_health = rae.health_check()
                health_status["dependencies"]["rae"] = {
                    "status": "healthy",
                    "base_url": settings.rae_base_url,
                    "response": rae_health.get("status", "ok"),
                }
                log.debug("RAE health check: OK")
            else:
                health_status["dependencies"]["rae"] = {"status": "disabled", "message": "RAE client not initialized"}
        except Exception as e:
            health_status["dependencies"]["rae"] = {"status": "unhealthy", "error": str(e)}
            log.warning(f"RAE health check failed: {e}")
    else:
        health_status["dependencies"]["rae"] = {"status": "disabled"}

    # Determine overall status
    unhealthy_deps = [dep for dep, info in health_status["dependencies"].items() if info.get("status") == "unhealthy"]

    if unhealthy_deps:
        health_status["status"] = "degraded"
        health_status["unhealthy_dependencies"] = unhealthy_deps
        log.warning(f"Service degraded: {unhealthy_deps}")
        return Response(content=str(health_status), status_code=503, media_type="application/json")

    return health_status
