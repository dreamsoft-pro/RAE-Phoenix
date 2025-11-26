# PLAN NAPRAWY BRAKÓW ENTERPRISE - FENIKS

**Data utworzenia:** 26 Listopada 2025
**Dokument referencyjny:** `docs/AUDYT_IMPLEMENTACJI_PLANU_REFAKTORYZACJI.md`
**Cel:** Doprowadzenie projektu Feniks do pełnego poziomu Enterprise-Grade (5/5 ⭐)

---

## 📊 Podsumowanie Braków

Z audytu wynika, że projekt osiągnął **85% planu refaktoryzacji** i ocenę **4.25/5 ⭐**.

Aby osiągnąć **5/5 ⭐ (World-Class Enterprise)**, należy uzupełnić **12 zidentyfikowanych luk**.

---

## 🎯 Strategia Naprawy

Plan podzielony jest na **3 Sprinty** wg priorytetu:
- **Sprint 1:** Krytyczne (blocking production deployment)
- **Sprint 2:** Wysokie (enterprise-grade standard)
- **Sprint 3:** Średnie (production hardening)

---

## 🔥 SPRINT 1: Krytyczne (1-2 tygodnie)

### 1.1. Zwiększenie pokrycia testów do 80%+

**Aktualny stan:** ~50% coverage
**Cel:** 80%+ coverage dla `core/` i `adapters/`

**Zadania:**

#### 1.1.1. Dodać testy dla SessionSummary transformacji
**Plik:** `feniks/tests/unit/core/models/test_domain.py`

Dodać test cases:
```python
def test_session_with_1000_reasoning_steps():
    """Test dla dużej sesji (>1000 steps)."""
    traces = [ReasoningTrace(step_id=f"s{i}", thought=f"t{i}", action="a", result="r", timestamp="ts") for i in range(1500)]
    session = SessionSummary(session_id="large", duration=300, success=True, reasoning_traces=traces)
    assert len(session.reasoning_traces) == 1500

def test_session_without_reasoning():
    """Test dla sesji bez reasoning traces."""
    session = SessionSummary(session_id="empty", duration=10, success=True, reasoning_traces=[])
    assert session.reasoning_traces == []

def test_session_with_loops():
    """Test dla sesji z pętlami."""
    traces = [
        ReasoningTrace(step_id="1", thought="t1", action="read_file", result="ok", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="t2", action="read_file", result="ok", timestamp="ts2"),  # Loop!
        ReasoningTrace(step_id="3", thought="t3", action="write_file", result="ok", timestamp="ts3"),
    ]
    session = SessionSummary(session_id="loop", duration=30, success=False, reasoning_traces=traces)
    # PostMortemAnalyzer powinien wykryć pętlę
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer
    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)
    assert any("Loop" in r.title for r in reflections)
```

**Effort:** 2-3 godziny

---

#### 1.1.2. Dodać testy dla Evaluation Pipeline
**Plik:** `feniks/tests/unit/core/evaluation/test_pipeline.py`

Dodać test cases:
```python
def test_scoring_quality():
    """Test dla scoring quality metric."""
    # TODO: Zaimplementować quality scoring w pipeline
    pass

def test_scoring_efficiency():
    """Test dla scoring efficiency metric (cost per token)."""
    # TODO: Zaimplementować efficiency scoring
    pass

def test_loop_detection():
    """Test dla wykrywania pętli reasoning."""
    # Już częściowo w post_mortem, ale dodać dedykowany test
    pass
```

**Effort:** 3-4 godziny

---

#### 1.1.3. Dodać testy dla Policies
**Plik:** `feniks/tests/unit/core/policies/test_cost_policy.py`

```python
def test_cost_policy_max_session_exceeded():
    """Test dla przekroczenia max session cost."""
    from feniks.core.policies.cost_policy import CostPolicyEnforcer, CostPolicyConfig
    config = CostPolicyConfig(max_session_cost=0.5)
    enforcer = CostPolicyEnforcer(config)

    session = create_session_with_cost(1.0)  # Helper function
    reflections = enforcer.check_session_cost(session)

    assert len(reflections) > 0
    assert reflections[0].impact.value == "critical"

def test_budget_alert_threshold():
    """Test dla osiągnięcia progu budżetu."""
    # Podobnie jak powyżej
    pass
```

**Effort:** 2-3 godziny

---

#### 1.1.4. Dodać pytest.ini z coverage target
**Plik:** `pytest.ini` (już istnieje, uzupełnić)

```ini
[tool:pytest]
testpaths = feniks/tests tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=feniks
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    golden: Golden fixture tests
```

**Effort:** 30 minut

---

### 1.2. Dodanie CI/CD Pipeline

**Plik:** `.github/workflows/ci.yml`

```yaml
name: Feniks CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Lint with ruff
      run: |
        ruff check .

    - name: Type check with mypy
      run: |
        mypy feniks/ --ignore-missing-imports

    - name: Run tests
      run: |
        pytest --cov=feniks --cov-fail-under=80
      env:
        QDRANT_HOST: localhost
        QDRANT_PORT: 6333

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Bandit security scan
      run: |
        pip install bandit
        bandit -r feniks/ -f json -o bandit-report.json

    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: bandit-report
        path: bandit-report.json
```

**Effort:** 2-3 godziny (z testowaniem)

---

### 1.3. Implementacja Auth i RBAC (podstawowa)

**Cel:** Zastąpić stuby w `feniks/security/` działającym kodem.

#### 1.3.1. Implementacja Auth (JWT)
**Plik:** `feniks/security/auth.py`

```python
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    username: str
    scopes: list[str] = []

class AuthManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            scopes: list = payload.get("scopes", [])
            return TokenData(username=username, scopes=scopes)
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
```

**Effort:** 3-4 godziny

---

#### 1.3.2. Implementacja RBAC
**Plik:** `feniks/security/rbac.py`

```python
from enum import Enum
from typing import List

class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(str, Enum):
    READ_SESSIONS = "read:sessions"
    WRITE_SESSIONS = "write:sessions"
    READ_REPORTS = "read:reports"
    ADMIN_ACCESS = "admin:*"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.ADMIN_ACCESS],
    Role.ANALYST: [Permission.READ_SESSIONS, Permission.WRITE_SESSIONS, Permission.READ_REPORTS],
    Role.VIEWER: [Permission.READ_SESSIONS, Permission.READ_REPORTS],
}

class RBACManager:
    def check_permission(self, user_roles: List[Role], required_permission: Permission) -> bool:
        for role in user_roles:
            permissions = ROLE_PERMISSIONS.get(role, [])
            if Permission.ADMIN_ACCESS in permissions or required_permission in permissions:
                return True
        return False
```

**Effort:** 2-3 godziny

---

#### 1.3.3. Integracja z FastAPI
**Plik:** `feniks/apps/api/main.py`

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from feniks.security.auth import AuthManager
from feniks.security.rbac import RBACManager, Permission

security = HTTPBearer()
auth_manager = AuthManager(secret_key=settings.jwt_secret)
rbac_manager = RBACManager()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token_data = auth_manager.verify_token(credentials.credentials)
        return token_data
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def require_permission(permission: Permission):
    def dependency(user = Depends(get_current_user)):
        if not rbac_manager.check_permission(user.scopes, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

# Użycie w endpointach:
@app.post("/sessions/analyze", dependencies=[Depends(require_permission(Permission.WRITE_SESSIONS))])
async def analyze_session(...):
    ...
```

**Effort:** 3-4 godziny

---

**SPRINT 1 Total Effort:** ~25-35 godzin (1-2 tygodnie dla 1 developera)

---

## 🔥 SPRINT 2: Wysokie (2-3 tygodnie)

### 2.1. Integracja OpenTelemetry

**Cel:** Zastąpić własną implementację tracingu standardem OTEL.

#### 2.1.1. Dodać zależności
**Plik:** `pyproject.toml`

```toml
[project.optional-dependencies]
observability = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-jaeger>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
]
```

---

#### 2.1.2. Wrapper nad OTEL
**Plik:** `feniks/infra/tracing.py` (refaktoryzacja)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from contextvars import ContextVar

_project_id_ctx: ContextVar[str] = ContextVar("project_id", default=None)

def init_tracing(service_name: str = "feniks", jaeger_host: str = "localhost", jaeger_port: int = 6831):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)

def get_tracer(name: str = "feniks"):
    return trace.get_tracer(name)

# Backward compatibility
def span(name: str, attributes: dict = None):
    tracer = get_tracer()
    return tracer.start_as_current_span(name, attributes=attributes)
```

**Effort:** 4-5 godzin

---

### 2.2. Eksport metryk do Prometheus

#### 2.2.1. Dodać prometheus-client
**Plik:** `pyproject.toml`

```toml
dependencies = [
    ...
    "prometheus-client>=0.18.0",
]
```

---

#### 2.2.2. Refaktoryzacja MetricsCollector
**Plik:** `feniks/infra/metrics.py`

```python
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

class PrometheusMetricsCollector:
    def __init__(self):
        self.cost_total = Counter("feniks_cost_total", "Total cost in USD")
        self.quality_score = Gauge("feniks_quality_score", "Current quality score")
        self.recommendations_count = Counter("feniks_recommendations_count", "Total recommendations")
        self.operations_total = Counter("feniks_operations_total", "Total operations")
        self.errors_total = Counter("feniks_errors_total", "Total errors")

    def export_prometheus(self):
        return generate_latest(REGISTRY)
```

---

#### 2.2.3. Dodać endpoint /metrics w API
**Plik:** `feniks/apps/api/main.py`

```python
from fastapi.responses import PlainTextResponse

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    return metrics.export_prometheus()
```

**Effort:** 3-4 godziny

---

### 2.3. Dodanie Golden Fixtures (2-3 nowe)

**Cel:** Zwiększyć liczbę golden scenarios z 3 do 5+.

#### 2.3.1. Golden Fixture: High Cost Session
**Plik:** `tests/fixtures/golden/sessions/high_cost.json`

```json
{
  "session_id": "golden-high-cost",
  "duration": 600,
  "success": true,
  "reasoning_traces": [...],
  "cost_profile": {
    "total_tokens": 150000,
    "cost_usd": 2.5,
    "breakdown": {"input": 1.0, "output": 1.5}
  }
}
```

**Test:**
```python
def test_golden_high_cost_alert(engine):
    session = load_golden_session("high_cost")
    reflections = engine.run_post_mortem(session, project_id="golden-test")
    assert any("High Session Cost" in r.title for r in reflections)
```

---

#### 2.3.2. Golden Fixture: Warning Level Issues
**Plik:** `tests/fixtures/golden/sessions/warning_quality.json`

```json
{
  "session_id": "golden-warning",
  "duration": 120,
  "success": true,
  "reasoning_traces": [
    {"step_id": "1", "thought": "short", "action": "read", "result": "ok", "timestamp": "ts1"}
  ],
  "cost_profile": {"total_tokens": 5000, "cost_usd": 0.15, "breakdown": {}}
}
```

**Test:**
```python
def test_golden_warning_quality(engine):
    session = load_golden_session("warning_quality")
    reflections = engine.run_post_mortem(session, project_id="golden-test")
    assert any("Too Short" in r.title for r in reflections)
    assert all(r.impact.value != "critical" for r in reflections)
```

---

#### 2.3.3. Golden Fixture: Perfect Session
**Plik:** `tests/fixtures/golden/sessions/perfect.json`

```json
{
  "session_id": "golden-perfect",
  "duration": 45,
  "success": true,
  "reasoning_traces": [
    {"step_id": "1", "thought": "This is a well-formed reasoning step with sufficient detail.", "action": "read_file", "result": "ok", "timestamp": "ts1"},
    {"step_id": "2", "thought": "Based on the file content, I will now write the changes.", "action": "write_file", "result": "ok", "timestamp": "ts2"}
  ],
  "cost_profile": {"total_tokens": 2000, "cost_usd": 0.05, "breakdown": {}}
}
```

**Test:**
```python
def test_golden_perfect_no_alerts(engine):
    session = load_golden_session("perfect")
    reflections = engine.run_post_mortem(session, project_id="golden-test")
    assert len(reflections) == 0, f"Expected 0 reflections, got {len(reflections)}"
```

**Effort:** 4-5 godzin

---

**SPRINT 2 Total Effort:** ~35-45 godzin (2-3 tygodnie dla 1 developera)

---

## 🔥 SPRINT 3: Średnie (1-2 tygodnie)

### 3.1. Pełna dokumentacja API (OpenAPI)

**Cel:** Uzupełnić OpenAPI descriptions i examples.

**Plik:** `feniks/apps/api/main.py`

```python
app = FastAPI(
    title="Feniks API",
    description="""
    # Feniks: Meta-Reflective Code Analysis Engine

    ## Features
    - Post-Mortem Analysis
    - Longitudinal Trend Detection
    - Cost & Quality Policies

    ## Authentication
    Use Bearer token in Authorization header.
    """,
    version="0.1.0",
    openapi_tags=[
        {"name": "sessions", "description": "Session analysis operations"},
        {"name": "reports", "description": "Report retrieval"},
        {"name": "patterns", "description": "Error pattern analysis"},
        {"name": "metrics", "description": "System metrics"},
    ]
)

@app.post(
    "/sessions/analyze",
    tags=["sessions"],
    summary="Analyze a session",
    description="Submit a session summary for Post-Mortem analysis.",
    response_model=AnalyzeSessionResponse,
    responses={
        200: {"description": "Analysis complete"},
        500: {"description": "Analysis failed"},
    }
)
async def analyze_session(request: AnalyzeSessionRequest):
    ...
```

**Effort:** 3-4 godziny

---

### 3.2. Rate Limiting w API

**Plik:** `feniks/apps/api/main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/sessions/analyze")
@limiter.limit("10/minute")
async def analyze_session(request: Request, ...):
    ...
```

**Effort:** 2-3 godziny

---

### 3.3. Health Checks dla zależności

**Plik:** `feniks/apps/api/main.py`

```python
@app.get("/health")
async def health_check():
    health_status = {
        "status": "ok",
        "version": "0.1.0",
        "dependencies": {}
    }

    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        collections = client.get_collections()
        health_status["dependencies"]["qdrant"] = {"status": "healthy", "collections": len(collections.collections)}
    except Exception as e:
        health_status["dependencies"]["qdrant"] = {"status": "unhealthy", "error": str(e)}

    # Check RAE
    if settings.rae_enabled:
        try:
            from feniks.adapters.rae_client import create_rae_client
            rae = create_rae_client()
            if rae:
                rae.health_check()
                health_status["dependencies"]["rae"] = {"status": "healthy"}
        except Exception as e:
            health_status["dependencies"]["rae"] = {"status": "unhealthy", "error": str(e)}

    # Determine overall status
    if any(d["status"] == "unhealthy" for d in health_status["dependencies"].values()):
        health_status["status"] = "degraded"

    return health_status
```

**Effort:** 2-3 godziny

---

**SPRINT 3 Total Effort:** ~15-20 godzin (1-2 tygodnie dla 1 developera)

---

## 📊 Harmonogram Implementacji

| Sprint | Effort | Czas kalendarzowy | Priorytet |
|--------|--------|-------------------|-----------|
| Sprint 1 | 25-35h | 1-2 tygodnie | ⚠️ Krytyczne |
| Sprint 2 | 35-45h | 2-3 tygodnie | 🔶 Wysokie |
| Sprint 3 | 15-20h | 1-2 tygodnie | 🟡 Średnie |
| **Total** | **75-100h** | **4-7 tygodni** | - |

Dla zespołu 2-3 developerów: **2-4 tygodnie** (z równoległą pracą).

---

## ✅ Kryteria Akceptacji (Definition of Done)

### Po Sprint 1:
- ✅ Coverage testów ≥ 80%
- ✅ CI/CD pipeline działa (GitHub Actions)
- ✅ Auth JWT i RBAC działają w API
- ✅ Wszystkie testy przechodzą w CI

### Po Sprint 2:
- ✅ OpenTelemetry integracja działa
- ✅ Metryki eksportowane do Prometheus
- ✅ 5+ Golden Fixtures
- ✅ Jaeger pokazuje traces

### Po Sprint 3:
- ✅ OpenAPI documentation kompletna
- ✅ Rate limiting działa
- ✅ Health checks dla zależności działają
- ✅ README zaktualizowane z nową funkcjonalnością

---

## 🎯 Metryki Sukcesu

Po zakończeniu wszystkich 3 Sprintów, projekt Feniks osiągnie:

| Metryka | Przed | Po | Target |
|---------|-------|-----|--------|
| Test Coverage | ~50% | 80%+ | ✅ |
| CI/CD | ❌ | ✅ GitHub Actions | ✅ |
| Auth/RBAC | Stub | JWT + RBAC | ✅ |
| Observability | Własne | OTEL + Prometheus | ✅ |
| Golden Fixtures | 3 | 5+ | ✅ |
| API Documentation | Częściowa | Pełna OpenAPI | ✅ |
| Production Readiness | ⚠️ Pre-prod | ✅ Production | ✅ |
| **Ocena Enterprise** | ⭐⭐⭐⭐ (4.25/5) | ⭐⭐⭐⭐⭐ (5/5) | ✅ |

---

## 🚀 Next Steps (Post-Enterprise)

Po osiągnięciu 5/5 ⭐, rozważyć:

1. **Multi-tenancy** - dla SaaS deployment
2. **Grafana Dashboards** - dla visualizacji metryk
3. **PagerDuty/Opsgenie** - dla alerting
4. **Kubernetes Helm Charts** - dla deployment
5. **Performance Testing** - Locust/K6 dla load testing
6. **Security Audit** - zewnętrzny pentesting

---

**Koniec planu naprawy**

*Dokument przygotowany przez Claude Code*
*Data: 26 Listopada 2025*
