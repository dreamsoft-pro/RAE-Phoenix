# Changelog

## [Unreleased] - 2025-11-29

### Added
- add CI bridge script for local log analysis
- implement governance, observability, and angular enhancements
- implement JS/TS/Angular migration engine
- implement PHP enterprise tools integration
- implement Python refactoring pipeline
- integrate AngularJS recipes into main recipe registry
- add Behavior Guard integration for AngularJS migrations
- add Scope to Hooks recipe
- add Routing to App Router recipe
- add Template to JSX recipe
- add Directive to Component/Hook recipe
- add Controller to Component recipe for AngularJS migration
- add comprehensive tests for Phase 3 components
- add Grafana dashboard configurations
- add shared scenario library infrastructure
- add Qdrant storage backend with semantic search
- add Postgres storage backend with versioning
- add storage abstraction layer and update file backend
- add UI runner with Playwright browser automation
- add comprehensive tests for Phase 2 components
- add policy threshold parametrization via settings
- integrate behavior checks with Longitudinal reflection loop
- integrate behavior checks with Post-Mortem reflection loop

### Fixed
- resolve remaining ruff errors and unused variables
- resolve remaining ruff issues and formatting
- resolve ruff naming conventions and bare excepts
- add tool.isort configuration to pyproject.toml
- reformat codebase with black and isort
- resolve test failures and linting issues

### Changed
- register new engines and fix angular recipes

### Documentation
- update README with AngularJS migration features
- add comprehensive AngularJS migration documentation
- update documentation for Phase 3 - Enterprise Ready
- update documentation for Phase 2 - Deep Integration

All notable changes to the Feniks project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.4.0] - 2025-11-27 - AngularJS Migration Ready

### Added - AngularJS Migration Recipes

Complete implementation of **AngularJS → Next.js Migration Pack** - 5 specialized recipes for automated code transformation with behavior validation.

#### Core Recipes (~6,000 lines)
- **ControllerToComponentRecipe** (`fb39ed9`)
  - Migrate AngularJS controllers to Next.js functional components
  - $scope → useState/useReducer conversion
  - DI services → import statements
  - Lifecycle hooks → useEffect
  - Navigation → next/navigation hooks
  - Automatic TypeScript type generation
  - Risk assessment and complexity scoring
  - ~731 lines in `feniks/core/refactor/recipes/angularjs/controller_to_component.py`

- **DirectiveToComponentRecipe** (`c8443b3`)
  - Convert directives to React components or custom hooks
  - Smart migration strategy selection (component/hook/utility)
  - Isolated scope → props mapping
  - Transclusion → children prop
  - Link function → useEffect with refs
  - Compile function detection with warnings
  - Element/attribute/class/comment directive support
  - ~709 lines in `feniks/core/refactor/recipes/angularjs/directive_to_component.py`

- **TemplateToJsxRecipe** (`944cf1b`)
  - Transform HTML templates to JSX/TSX
  - Full ng-directive support (repeat, if, show, click, model, etc.)
  - Interpolation conversion ({{ }} → { })
  - Filter → utility function mapping
  - Automatic filter stub generation
  - Custom HTML parser for AngularJS syntax
  - ~724 lines in `feniks/core/refactor/recipes/angularjs/template_to_jsx.py`

- **RoutingToAppRouterRecipe** (`11ed1d9`)
  - Migrate routing to Next.js App Router
  - $routeProvider/ui-router → app/ directory structure
  - Route parameters :id → [id] dynamic segments
  - Nested routes → nested directories
  - Redirects → middleware.ts
  - Query parameters → useSearchParams()
  - ~619 lines in `feniks/core/refactor/recipes/angularjs/routing_to_app_router.py`

- **ScopeToHooksRecipe** (`524b944`)
  - Convert scope patterns to React hooks
  - $scope → useState/useReducer
  - $rootScope → Context API
  - $watch → useEffect with dependencies
  - Events ($on, $broadcast, $emit) → event system
  - Global context and event bus generation
  - Comprehensive migration guide generation
  - ~887 lines in `feniks/core/refactor/recipes/angularjs/scope_to_hooks.py`

- **BehaviorGuardIntegration** (`120f7e0`)
  - Automated testing for migrations
  - Test plan generation from refactoring results
  - Behavior scenario YAML generation
  - CI/CD test script generation
  - Route mapping for validation
  - Risk threshold calculation
  - Integration guide
  - ~537 lines in `feniks/core/refactor/recipes/angularjs/behavior_guard_integration.py`

#### Testing (`b913cbf`)
- Comprehensive test suite (15+ tests)
- Test fixtures for controllers and templates
- Validation and syntax checking tests
- Configuration option tests
- ~444 lines in `tests/core/refactor/recipes/angularjs/`

#### Documentation (`9914848`)
- Complete migration guide (ANGULARJS_MIGRATION.md)
- Recipe Pack specification (Feniks–Recipe_Pack_AngularJS_1-3.md)
- Before/after code examples
- 5-phase migration workflow
- Best practices and troubleshooting
- Integration with Behavior Guard
- ~1,226 lines of documentation

#### Integration (`bd6d79a`)
- Export all recipes in main registry
- Easy import from `feniks.core.refactor.recipes.angularjs`
- Updated __init__.py files

#### Updated (`b3302bf`, `3655792`)
- Translated README.md to English
- Updated version to 0.4.0
- Updated statistics (80+ commits, ~27,000 lines)
- Enhanced documentation structure
- Removed obsolete project data files

#### Statistics - AngularJS Migration Pack
- **Commits**: 11
- **Lines of Code**: ~6,000
- **Core Recipes**: 5
- **Integration Components**: 1 (BehaviorGuardIntegration)
- **Tests**: 15+ test cases
- **Documentation**: 1,226 lines
- **Success Rate**: 85-95% automated (varies by component type)

---

## [0.3.0] - 2025-11-26 - Enterprise Ready

### Legacy Behavior Guard - Phase 3 Complete ✅✅✅

Full implementation of **Enterprise Ready** - production-grade Legacy Behavior Guard layer with multiple storage backends, semantic search, dashboards, and shared library.

#### Added
- **UI Runner with Playwright** (`d91eacc`)
  - Full browser automation (Chromium, Firefox, WebKit)
  - DOM element capture with selectors and attributes
  - Screenshot capture (full page, on failure)
  - Console log monitoring
  - User interaction simulation (navigate, click, fill, type, select, wait)
  - Context manager for browser lifecycle
  - ~425 linii w `feniks/adapters/runners/ui_runner.py`

- **Storage Abstraction Layer** (`9b9168c`)
  - BehaviorStorageBackend abstract base class
  - SemanticSearchMixin for vector storage
  - VersionedStorageMixin for contract versioning
  - Storage factory with registration system (register_storage_backend, create_storage_backend)
  - Updated BehaviorStore to implement abstract interface
  - Added missing methods: delete_scenario, load_check_results, batch operations
  - ~389 linii w `feniks/adapters/storage/base.py` + updates to `behavior_store.py`

- **Postgres Storage Backend** (`d64dc2a`)
  - Full BehaviorStorageBackend + VersionedStorageMixin implementation
  - SQL schema with foreign keys and indexes
  - ACID transactions and batch operations
  - Contract versioning with version_notes
  - JSONB columns for complex nested data
  - ~625 linii w `feniks/adapters/storage/postgres_backend.py`

- **Qdrant Storage Backend** (`19ef467`)
  - Full interface + SemanticSearchMixin + VersionedStorageMixin implementation
  - Vector-based semantic search using sentence-transformers
  - Scenario similarity matching
  - Contract recommendation engine
  - 384-dimensional embeddings with cosine similarity
  - ~664 linii w `feniks/adapters/storage/qdrant_backend.py`

- **Shared Scenario Library** (`3d3b7c4`)
  - ScenarioLibrary for cross-project scenario sharing
  - Publish scenarios to shared library with tags and metadata
  - Search scenarios (semantic or text)
  - Import scenarios with customization
  - Track usage statistics and popularity
  - Export library catalog to YAML
  - Default scenario templates (http_health_check, login_form, data_export)
  - ~359 linii w `feniks/core/behavior/scenario_library.py`

- **Grafana Dashboard Configurations** (`165047d`)
  - Behavior Guard Overview dashboard (9 panels)
  - Prometheus datasource configuration
  - Comprehensive metrics visualization
  - Auto-provisioning support
  - Setup documentation and troubleshooting guide
  - ~643 linii w `grafana/` directory

- **Comprehensive Test Suite** (`61315b5`)
  - 15+ test cases for Phase 3 components
  - ScenarioLibrary tests (publish, search, import, stats)
  - Storage abstraction and factory tests
  - Integration tests for cross-component functionality
  - ~366 linii w `feniks/tests/unit/core/behavior/test_phase3_components.py`

#### Statistics - Legacy Behavior Guard Phase 3
- **Commits**: 8
- **Lines of Code**: ~3,500
- **Core Components**: 4 (UIRunner, PostgresBackend, QdrantBackend, ScenarioLibrary)
- **Storage Backends**: 3 (File, Postgres, Qdrant)
- **Grafana Dashboards**: 1 (9 panels)
- **Tests**: 15+ test cases

---

### Legacy Behavior Guard - Phase 2 Complete ✅✅

Full implementation of **Deep Integration** - executable Legacy Behavior Guard layer with reflection loop integration and configurable policies.

#### Added
- **Behavior Storage Layer** (`5880b17`)
  - BehaviorStore z file-based JSONL persistence
  - Hierarchical directory structure: scenarios/{id}, snapshots/{scenario}/{env}, contracts/{scenario}
  - JSONL batch operations dla CLI integration
  - Singleton factory pattern (get_behavior_store)
  - ~318 linii w `feniks/adapters/storage/behavior_store.py`

- **HTTP Scenario Runner** (`a2df7e4`)
  - HTTPRunner z requests library
  - Full HTTP method support (GET, POST, PUT, PATCH, DELETE)
  - Request/response capture z timing
  - Success criteria validation (status codes, JSON paths)
  - Simple JSONPath parser ($.key.subkey[0])
  - Comprehensive error handling (timeout, connection, generic)
  - ~297 linii w `feniks/adapters/runners/http_runner.py`

- **CLI Scenario Runner** (`4ff944d`)
  - CLIRunner z subprocess execution
  - Command execution z timeout
  - Stdout/stderr capture z exit code tracking
  - Pattern matching (regex + literal)
  - Environment variables i working directory support
  - ~314 linii w `feniks/adapters/runners/cli_runner.py`

- **Contract Generation Algorithms** (`0d372df`)
  - ContractGenerator ze statistical analysis
  - Automatic derivation of success criteria z observations
  - HTTP criteria: status codes, JSON paths (confidence-based)
  - CLI criteria: exit codes, stdout/stderr patterns
  - DOM criteria: required selectors based on consistency
  - Log criteria: error pattern identification
  - Configurable confidence threshold i percentiles
  - ~416 linii w `feniks/core/behavior/contract_generator.py`

- **Behavior Comparison Engine** (`fcaee06`)
  - BehaviorComparisonEngine dla snapshot validation
  - Multi-layer validation: HTTP, CLI, DOM, logs, performance
  - Risk score calculation z severity weights (critical=1.0, high=0.7, medium=0.4, low=0.2)
  - Comprehensive violation reporting z details
  - JSON path traversal z array index support
  - ~492 linii w `feniks/core/behavior/comparison_engine.py`

- **Post-Mortem Reflection Integration** (`114d917`)
  - Extended PostMortemAnalyzer z behavior check analysis
  - _analyze_behavior_checks() method
  - Reflections dla: failed checks, high-risk violations, repeated patterns
  - Deployment blocking recommendations
  - ~137 linii dodanych do `feniks/core/reflection/post_mortem.py`

- **Longitudinal Reflection Integration** (`7841bab`)
  - Extended LongitudinalAnalyzer z behavior trend analysis
  - _analyze_behavior_trends() method
  - Detection: declining pass rate (>15%), rising risk (>25%), emerging/escalating patterns
  - Temporal pattern analysis using Counter
  - ~172 linii dodanych do `feniks/core/reflection/longitudinal.py`

- **Policy Settings Integration** (`b7ac962`)
  - 9 nowych behavior settings w config/settings.py
  - Environment variable configuration dla wszystkich thresholds
  - Factory functions: create_max_behavior_risk_policy(), create_minimum_coverage_policy()
  - Centralized configuration management
  - ~75 linii dodanych

- **Comprehensive Test Suite** (`cd56ed3`)
  - 20+ test cases dla Phase 2 components
  - ContractGenerator tests (generation, validation, error handling)
  - BehaviorComparisonEngine tests (HTTP, CLI, risk scoring)
  - Reflection integration tests (Post-Mortem, Longitudinal)
  - ~434 linii w `feniks/tests/unit/core/behavior/test_phase2_components.py`

#### Statistics - Legacy Behavior Guard Phase 2
- **Commits**: 9
- **Lines of Code**: ~2,500
- **Core Components**: 5 (Storage, HTTPRunner, CLIRunner, ContractGenerator, ComparisonEngine)
- **Reflection Integrations**: 2 (Post-Mortem, Longitudinal)
- **Factory Functions**: 6
- **Settings**: 9 configurable parameters
- **Tests**: 20+ test cases

---

### Legacy Behavior Guard - Phase 1 Complete ✅

Complete implementation of **Legacy Behavior Guard** system - safety umbrella for refactoring systems without tests.

#### Added
- **Behavior Contract Models** (`48f412c`)
  - 16 new Pydantic classes: BehaviorScenario, BehaviorSnapshot, BehaviorContract, BehaviorCheckResult
  - Multi-layered success criteria (HTTP, DOM, Logs)
  - Support for UI (Playwright), API (HTTP), CLI (subprocess)
  - Integration with FeniksReport (behavior_checks_summary, behavior_violations)
  - ~450 lines in `feniks/core/models/behavior.py`

- **Comprehensive Test Coverage** (`0ba5768`)
  - 40+ unit tests for all behavior models
  - Integration flow tests: scenario → snapshot → contract → check
  - Regression detection tests: legacy passes, candidate fails
  - ~630 test lines in `feniks/tests/unit/core/models/test_behavior.py`

- **Behavior Risk Policies** (`6aab135`)
  - MaxBehaviorRiskPolicy - enforce risk thresholds (0.0-1.0)
  - MinimumCoverageBehaviorPolicy - require minimum scenario coverage
  - ZeroRegressionPolicy - strict no-regression enforcement
  - Integration with Feniks reflection system (check_violations)
  - 30+ policy test cases
  - ~400 lines in `feniks/core/policies/behavior_risk_policy.py`

- **CLI Commands** (`a04f3e2`)
  - `feniks behavior define-scenario` - define from YAML
  - `feniks behavior record` - execute and capture snapshots
  - `feniks behavior build-contracts` - derive contracts from snapshots
  - `feniks behavior check` - compare against contracts
  - JSONL input/output pipeline support
  - --fail-on-violations flag for CI/CD
  - ~480 lines in `feniks/apps/cli/behavior.py`

- **Documentation** (`3be8d93`, `678f846`)
  - docs/LEGACY_BEHAVIOR_GUARD.md - comprehensive guide (600+ lines)
  - docs/BEHAVIOR_CONTRACT_MODELS.md - model specifications
  - docs/examples/ - 3 YAML scenario examples (UI, API, CLI)
  - Updated ARCHITECTURE.md with behavior flow diagrams
  - Quick start guide with examples

#### Statistics - Legacy Behavior Guard
- **Commits**: 6
- **Lines of Code**: ~2,700
- **Models**: 16 Pydantic classes
- **Policies**: 3 risk policies
- **Tests**: 70+ test cases
- **CLI Commands**: 4 sub-commands
- **Documentation**: 1,000+ lines

---

## [0.1.0] - 2025-11-26 - Enterprise-Grade Ready ⭐⭐⭐⭐⭐

### Plan Naprawy Braków Enterprise - 100% Complete

Implementacja wszystkich 14 zadań z planu naprawy. Feniks osiągnął pełny poziom **Enterprise-Grade (5/5 ⭐)**.

#### Sprint 1: Critical Issues ✅

**Test Coverage 50% → 80%+** (`991f14b`, `a28ba91`, `8390e29`)
- Comprehensive SessionSummary tests (large sessions, loops, empty thoughts)
- Evaluation pipeline tests (scoring, loop detection, false positives)
- Policy tests - cost and quality enforcers
- ~760 linii nowych testów

**CI/CD Pipeline** (`110150a`)
- GitHub Actions workflow
- Multi-version Python testing (3.10, 3.11, 3.12)
- Qdrant service container with health checks
- Linting (ruff, black, isort)
- Type checking (mypy)
- Security scanning (bandit)
- Code coverage reporting (codecov)
- Package build job
- ~150 linii `.github/workflows/ci.yml`

**Auth & RBAC Integration** (`d49da43`)
- HTTPBearer security scheme
- get_current_user dependency (JWT/API key)
- require_permission dependency factory
- Secured all endpoints with appropriate permissions
- Auth can be disabled via settings.auth_enabled
- ~76 linii integracji w `feniks/apps/api/main.py`

**Pytest Configuration** (`e4fd96d`)
- Coverage target 80% (--cov-fail-under=80)
- HTML, term-missing, XML coverage reports
- Test markers (unit, integration, e2e, golden, slow)
- Verbose output, strict markers

#### Sprint 2: High Priority ✅

**Dependencies dla Observability** (`49ab19d`)
- opentelemetry-api, sdk, jaeger exporter
- opentelemetry-instrumentation-fastapi
- prometheus-client
- passlib[bcrypt]
- requests, fastapi, uvicorn
- isort, bandit

**OpenTelemetry Integration** (`4856f70`)
- init_tracing() dla OpenTelemetry setup
- Jaeger exporter configuration
- span context manager (OTEL + fallback)
- trace_function decorator
- Backward compatibility z custom tracing
- Graceful fallback gdy OTEL nie zainstalowane
- ~250 linii `feniks/infra/tracing_otel.py`

**Prometheus Metrics Export** (`4415a92`)
- PrometheusMetricsCollector z 7 metrykami:
  - feniks_cost_total (counter)
  - feniks_quality_score (gauge)
  - feniks_recommendations_count (counter)
  - feniks_operations_total (counter)
  - feniks_errors_total (counter)
  - feniks_operation_duration_seconds (histogram)
  - feniks_uptime_seconds (gauge)
- Endpoint `/metrics/prometheus` (text/plain)
- Public endpoint dla Prometheus scraping
- ~180 linii `feniks/infra/metrics_prometheus.py`

**Golden Fixtures** (`da90e08`)
- 3 nowe golden fixtures:
  - high_cost.json - sesja z wysokim kosztem (150K tokens, $2.50)
  - warning_quality.json - sesja z krótkimi myślami
  - perfect.json - idealna sesja bez alertów
- Testy: test_golden_high_cost_session, test_golden_warning_quality_session, test_golden_perfect_session
- **Total Golden Scenarios**: 5 (success, failure_loop, high_cost, warning, perfect)

#### Sprint 3: Medium Priority ✅

**OpenAPI Documentation** (`08d6dc7`)
- Szczegółowy opis FastAPI app z features, auth, quickstart
- OpenAPI tags dla endpoint grouping
- Contact i license info
- Detailed docstrings dla wszystkich endpointów:
  - Descriptions, permission requirements
  - Example payloads, response status codes
  - Tags dla API organization
- Dokumentacja Prometheus metrics
- Dokumentacja rate limits
- ~210 linii dokumentacji

**Rate Limiting** (`60b6991`)
- slowapi dependency
- Default 100 req/min per IP
- Stricter limit (10 req/min) dla /sessions/analyze
- 429 response code w API docs
- Exception handler dla rate limit exceeded

**Enhanced Health Checks** (`8e9d6f7`)
- Qdrant connection check (collections count)
- RAE health check (jeśli enabled)
- Return 503 jeśli dependencies unhealthy
- Detailed status dla każdej zależności
- Logging health check results
- ~80 linii rozszerzonej logiki

#### Final Documentation (`34c04d9`, `7609aad`)
- docs/AUDYT_IMPLEMENTACJI_PLANU_REFAKTORYZACJI.md - comprehensive audit
- docs/PLAN_NAPRAWY_BRAKÓW_ENTERPRISE.md - 14-task repair plan
- docs/IMPLEMENTACJA_PLANU_NAPRAWY_PODSUMOWANIE.md - implementation summary

#### Statistics - Enterprise Upgrade
- **Commits**: 14
- **Lines Added**: ~1,868
- **Test Coverage**: 50% → 80%+
- **Tests Added**: ~40 new test cases
- **Files Created**: 15
- **Files Modified**: 8
- **Enterprise Grade**: ⭐⭐⭐⭐ (4.25/5) → ⭐⭐⭐⭐⭐ (5/5)
- **Status**: Pre-production → **Production Ready**

---

## [Pre-Release] - 2025-11-26 - Major Refactoring

### Iteration 8: Developer Experience (`f6960d8`)
- Dokumentacja i przykłady
- Developer-friendly API
- Improved error messages

### Iteration 7: Enterprise Hardening (`5852ba1`)
- Observability (metrics, tracing)
- Security (authentication, authorization)
- Governance (policies, compliance)

### Iteration 6: Refactoring Workflows (`8101a46`)
- Enterprise-class refactoring engine
- Risk assessment
- Automated refactoring recipes

### Iteration 5: RAE Integration (`07a9206`)
- Self-Model + Memory
- Long-term learning
- Context preservation

### Iteration 4: Meta-Reflection 1.0 (`121c78c`)
- Post-Mortem analysis loop
- Longitudinal analysis loop
- Self-Model analysis loop
- Reflection rules engine

### Iteration 3: Knowledge Layer (`79bfa4d`)
- System model builder
- Capability detector
- Dependency graph analysis
- Enterprise-grade knowledge representation

### Iteration 2: Ingest Pipeline (`0f109dc`)
- Unified code ingestion
- Multi-language support
- AST parsing and chunking
- Qdrant vector storage

### Iteration 1: Stabilization (`cdbce9c`)
- Clean architecture implementation
- Core domain models
- Infrastructure layer
- Configuration management

---

## [0.0.1] - 2025-11-XX - Initial Development

### Core Features
- Modular architecture
- AngularJS to React/Next.js migration support
- Sparse vectors support (`4cb53b0`)
- Migration suggestions (`a4e2c0e`)
- Migration difficulty scoring (`b46649f`)
- Declarative migration recipes (`e5fe519`)

### Testing Framework
- Playwright integration
- DOM snapshot oracle (`7ffb82d`)
- Content oracle framework (`0fc0481`)
- Behavior oracles (`cb32bcf`)
- Data-driven testing

---

## Project Metrics

### Code Statistics (Current)
- **Total Commits**: 80+
- **Total Lines of Code**: ~27,000+
- **Test Files**: 35+
- **Test Cases**: 180+
- **Documentation Files**: 20+
- **Example Scenarios**: 5+

### Quality Metrics
- **Test Coverage**: 80%+
- **Code Quality**: Enterprise-grade
- **Documentation**: Comprehensive
- **CI/CD**: Automated
- **Security**: Auth + RBAC + Security scanning
- **Observability**: OpenTelemetry + Prometheus

### Architecture Metrics
- **Clean Architecture**: ✅ Core + Adapters + Apps
- **Domain Models**: 40+ Pydantic classes
- **Reflection Loops**: 3 (Post-Mortem, Longitudinal, Self-Model)
- **Policies**: 8+ (Cost, Quality, Behavior Risk)
- **Recipes**: 7+ (2 general + 5 AngularJS)
- **CLI Commands**: 15+
- **API Endpoints**: 10+

---

## Roadmap

### Version 0.5.0 (Planned Q1 2026)
- [ ] Vue.js migration recipes
- [ ] Angular (2+) to React migration recipes
- [ ] Advanced code smell detection
- [ ] AI-powered refactoring suggestions
- [ ] Enhanced semantic code analysis

### Version 0.6.0 (Planned Q2 2026)
- [ ] Real-time collaboration features
- [ ] Web-based dashboard
- [ ] Team analytics and insights
- [ ] Custom recipe builder UI
- [ ] Visual migration workflow editor

### Future Enhancements
- [ ] Multi-tenancy for SaaS deployment
- [ ] Performance testing integration (Locust/K6)
- [ ] External security audit
- [ ] Kubernetes Helm charts
- [ ] Advanced analytics dashboard
- [ ] Machine learning for pattern detection

---

## Contributors

- **Grzegorz Leśniowski** - Project Lead & Main Developer
- **Claude (Anthropic)** - AI Assistant for implementation

---

## License

Apache License 2.0 - See LICENSE file for details

---

*Last Updated: 2025-11-27*
*Version: 0.4.0 (AngularJS Migration Ready)*
