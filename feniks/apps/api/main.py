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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional
from pydantic import BaseModel

from feniks.core.models.domain import SessionSummary, FeniksReport
from feniks.core.models.types import MetaReflection
from feniks.core.reflection.engine import MetaReflectionEngine
from feniks.core.policies.manager import PolicyManager
from feniks.infra.metrics import get_metrics_collector
from feniks.infra.logging import get_logger
from feniks.security.auth import get_auth_manager, User, AuthenticationError, AuthorizationError
from feniks.security.rbac import RBACManager, Permission
from feniks.config.settings import settings

log = get_logger("apps.api")
security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="Feniks API",
    description="Enterprise-grade Code Analysis and Reflection Engine",
    version="0.1.0"
)

# --- Dependencies ---
reflection_engine = MetaReflectionEngine()
policy_manager = PolicyManager()
metrics = get_metrics_collector()
auth_manager = get_auth_manager(jwt_secret=settings.jwt_secret)
rbac_manager = RBACManager()

# In-memory storage for reports (replace with DB in production)
_reports_db: Dict[str, FeniksReport] = {}
_reflections_db: Dict[str, List[MetaReflection]] = {}

# --- Authentication Dependencies ---

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token or API key.
    Returns None if authentication is disabled or no credentials provided.
    """
    if not settings.auth_enabled:
        # Auth disabled - return mock admin user
        from feniks.security.auth import UserRole
        return User(
            user_id="system",
            username="system",
            email="system@feniks.local",
            role=UserRole.ADMIN,
            projects=["*"]
        )

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        token = credentials.credentials
        user = auth_manager.authenticate(token)
        log.debug(f"Authenticated user: {user.username}")
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_permission(permission: Permission):
    """
    Dependency factory for requiring specific permission.
    """
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not rbac_manager.has_permission(user.role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value} required"
            )
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

@app.post("/sessions/analyze", response_model=AnalyzeSessionResponse)
async def analyze_session(
    request: AnalyzeSessionRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission(Permission.ANALYZE_CODE))
):
    """
    Submit a session for Post-Mortem analysis.
    Requires: ANALYZE_CODE permission
    """
    log.info(f"User {user.username} analyzing session for project {request.project_id}")
    report_id = f"rep-{request.session_summary.session_id}"
    
    # Run analysis synchronously for now (can be backgrounded)
    try:
        # 1. Post-Mortem Analysis
        reflections = reflection_engine.run_post_mortem(
            request.session_summary, 
            project_id=request.project_id
        )
        
        # Store results
        _reflections_db[report_id] = reflections
        
        # Count violations
        violations = [r for r in reflections if r.impact.value in ["critical", "refactor-recommended"]]
        
        log.info(f"Analysis complete for {report_id}: {len(reflections)} reflections, {len(violations)} violations")
        
        return AnalyzeSessionResponse(
            report_id=report_id,
            status="completed",
            violation_count=len(violations)
        )
        
    except Exception as e:
        log.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/{report_id}", response_model=List[MetaReflection])
async def get_report(
    report_id: str,
    user: User = Depends(require_permission(Permission.VIEW_REPORTS))
):
    """
    Get the analysis report (meta-reflections) for a session.
    Requires: VIEW_REPORTS permission
    """
    if report_id not in _reflections_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return _reflections_db[report_id]

@app.get("/patterns/errors")
async def get_error_patterns(user: User = Depends(require_permission(Permission.VIEW_REPORTS))):
    """
    Get aggregated error patterns (Longitudinal).
    Requires: VIEW_REPORTS permission
    """
    # Mock implementation for MVP
    # In real world, query DB/Vector Store for common patterns
    return {
        "patterns": [
            {"pattern": "Empty Reasoning", "count": 15, "severity": "medium"},
            {"pattern": "Loop Action", "count": 5, "severity": "high"}
        ]
    }

@app.get("/metrics")
async def get_metrics(user: User = Depends(require_permission(Permission.VIEW_METRICS))):
    """
    Get system metrics.
    Requires: VIEW_METRICS permission
    """
    return metrics.get_metrics()

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
