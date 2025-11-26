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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel

from feniks.core.models.domain import SessionSummary, FeniksReport
from feniks.core.models.types import MetaReflection
from feniks.core.reflection.engine import MetaReflectionEngine
from feniks.core.policies.manager import PolicyManager
from feniks.infra.metrics import get_metrics_collector
from feniks.infra.logging import get_logger

log = get_logger("apps.api")

app = FastAPI(
    title="Feniks API",
    description="Enterprise-grade Code Analysis and Reflection Engine",
    version="0.1.0"
)

# --- Dependencies ---
reflection_engine = MetaReflectionEngine()
policy_manager = PolicyManager()
metrics = get_metrics_collector()

# In-memory storage for reports (replace with DB in production)
_reports_db: Dict[str, FeniksReport] = {}
_reflections_db: Dict[str, List[MetaReflection]] = {}

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
async def analyze_session(request: AnalyzeSessionRequest, background_tasks: BackgroundTasks):
    """
    Submit a session for Post-Mortem analysis.
    """
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
async def get_report(report_id: str):
    """
    Get the analysis report (meta-reflections) for a session.
    """
    if report_id not in _reflections_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return _reflections_db[report_id]

@app.get("/patterns/errors")
async def get_error_patterns():
    """
    Get aggregated error patterns (Longitudinal).
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
async def get_metrics():
    """
    Get system metrics.
    """
    return metrics.get_metrics()

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
