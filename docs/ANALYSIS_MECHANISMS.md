# Mechanizmy Analizy Feniksa

**Pytanie:** Czy Feniks patrzy tylko na vectory z bazy Qdrant czy ma też inne mądrzejsze mechanizmy analizy?

**Odpowiedź:** Feniks ma o wiele bardziej zaawansowane mechanizmy analizy niż tylko patrzenie na wektory! **Qdrant to tylko STORAGE** - prawdziwa inteligencja jest w warstwie Core.

---

## 🎯 Przegląd: Qdrant vs. Inteligencja Feniksa

| Komponent | Rola | Mechanizm |
|-----------|------|-----------|
| **Qdrant** | 📦 Storage | Przechowuje chunki kodu jako wektory (dense + sparse) |
| **Reflection Engine** | 🧠 Analiza | Post-mortem, Longitudinal, Self-model loops |
| **Rules Engine** | 🔍 Wykrywanie | 8+ reguł architektonicznych (god modules, hotspots) |
| **Policy Manager** | 🛡️ Guardrails | Real-time enforcement (cost, quality, behavior risk) |
| **System Model** | 🕸️ Graf | Dependency graph, centrality metrics, hotspots |
| **Capability Detector** | 🎨 Semantyka | Wykrywa API, UI, batch, database operations |
| **Behavior Guard** | 📸 Regression | Snapshot comparison, contract verification |

---

## 1. Reflection Engine - Trzy Pętle Refleksji 🧠

### 1.1. Post-Mortem Analysis

**Plik:** `feniks/core/reflection/post_mortem.py`

**Analizuje pojedynczą sesję** i wykrywa problemy:

#### Co wykrywa:
- ❌ **Failure Detection** - czy sesja się powiodła
- 💰 **Cost Analysis** - czy koszt przekroczył próg ($0.50 default)
- 🔄 **Loop Detection** - wykrywa powtarzające się akcje (reasoning loops)
- 🤔 **Empty Reasoning** - wykrywa puste myśli w traces
- 📊 **Pattern Recognition** - identyfikuje problematyczne wzorce

#### Przykład kodu:
```python
class PostMortemAnalyzer:
    def analyze_session(self, session_summary: SessionSummary) -> List[MetaReflection]:
        reflections = []

        # 1. Check if session failed
        if not session_summary.success:
            reflections.append(self._create_failure_reflection(session_summary))

        # 2. Check if cost exceeded threshold
        if session_summary.cost_profile:
            COST_THRESHOLD = 0.50
            if session.cost_profile.cost_usd > COST_THRESHOLD:
                reflections.append(MetaReflection(
                    title="High Session Cost",
                    content=f"Cost ${cost:.2f} exceeded ${COST_THRESHOLD:.2f}",
                    impact=ReflectionImpact.MONITOR
                ))

        # 3. Detect reasoning loops (consecutive identical actions)
        traces = session_summary.reasoning_traces
        for i in range(1, len(traces)):
            if traces[i].action == traces[i-1].action:
                reflections.append(MetaReflection(
                    title="Reasoning Loop Detected",
                    content=f"Identical action repeated: {traces[i].action}",
                    impact=ReflectionImpact.CRITICAL
                ))
                break

        # 4. Detect empty thoughts
        empty_thoughts = [t for t in traces if not t.thought.strip()]
        if empty_thoughts:
            reflections.append(MetaReflection(
                title="Empty Reasoning Steps",
                content=f"Found {len(empty_thoughts)} steps with empty thoughts",
                impact=ReflectionImpact.REFACTOR_RECOMMENDED
            ))

        return reflections
```

#### Wyjście:
```python
MetaReflection(
    id="pm-loop-abc123",
    level=ReflectionLevel.META_REFLECTION,
    scope=ReflectionScope.PATTERN,
    impact=ReflectionImpact.CRITICAL,
    title="Reasoning Loop Detected",
    content="Identical action repeated at step 5: read_file",
    recommendations=[
        "Implement loop detection mechanism in agent core",
        "Increase penalties for repeated actions"
    ]
)
```

---

### 1.2. Longitudinal Analysis

**Plik:** `feniks/core/reflection/longitudinal.py`

**Analizuje trendy w czasie** na podstawie wielu sesji:

#### Co wykrywa:
- 📉 **Success Rate Trend** - czy % sukcesu spada (alarm <70%)
- 📈 **Cost Escalation** - czy koszty rosną (alarm jeśli +20%)
- 🔍 **Pattern Frequency** - jak często pojawiają się błędy
- ⚠️ **Quality Degradation** - czy jakość się pogarsza

#### Przykład kodu:
```python
class LongitudinalAnalyzer:
    def _analyze_success_rate(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        success_count = sum(1 for s in sessions if s.success)
        rate = success_count / len(sessions)

        if rate < 0.7:  # Below 70% success rate
            return MetaReflection(
                title="Low Global Success Rate",
                content=f"Success rate is {rate:.1%} across {len(sessions)} sessions",
                impact=ReflectionImpact.CRITICAL,
                recommendations=[
                    "Conduct deep dive into failed sessions",
                    "Review recent changes to agent logic"
                ]
            )
        return None

    def _analyze_cost_trend(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        costs = [s.cost_profile.cost_usd for s in sessions if s.cost_profile]

        # Compare first half vs last half
        mid = len(costs) // 2
        first_half_avg = statistics.mean(costs[:mid])
        last_half_avg = statistics.mean(costs[mid:])

        if last_half_avg > first_half_avg * 1.2:  # 20% increase
            return MetaReflection(
                title="Cost Trend Increasing",
                content=f"Average cost increased from ${first_half_avg:.2f} to ${last_half_avg:.2f}",
                impact=ReflectionImpact.MONITOR
            )
        return None
```

#### Przykład wykrycia trendu:
```
Input: 50 sesji, sukces spada z 90% (pierwsze 25) do 65% (ostatnie 25)

Output:
MetaReflection(
    title="Success Rate Degradation",
    content="Success rate dropped from 90% to 65% over last 25 sessions",
    impact=CRITICAL,
    evidence=[
        ReflectionEvidence(type="trend", source="session_history", value=0.65)
    ]
)
```

---

### 1.3. Self-Model Analysis

**Plik:** `feniks/core/reflection/self_model.py`

**Meta-learning** - Feniks uczy się o sobie:

#### Co robi:
- 🧬 **Self-awareness** - rozumie własne mocne/słabe strony
- 📚 **Learning from reflections** - integruje wnioski z przeszłości
- 🎯 **Strategy adaptation** - dostosowuje strategie na podstawie doświadczeń
- 🔄 **Feedback loops** - zamyka pętlę uczenia się

#### Koncepcja:
```python
class SelfModelAnalyzer:
    def update_self_model(self, recent_reflections: List[MetaReflection]) -> List[MetaReflection]:
        """
        Analyzes recent reflections to update Feniks' self-understanding.

        Example:
        - If many "Loop Detected" reflections → strengthen loop detection
        - If many "High Cost" alerts → recommend more aggressive caching
        - If quality improving → reinforce current strategies
        """
        self_reflections = []

        # Analyze reflection patterns
        by_type = self._group_reflections_by_type(recent_reflections)

        # Identify recurring issues
        for reflection_type, count in by_type.items():
            if count > threshold:
                self_reflections.append(MetaReflection(
                    title=f"Recurring Issue: {reflection_type}",
                    content=f"Detected {count} instances of {reflection_type}",
                    level=ReflectionLevel.META_REFLECTION,
                    recommendations=self._suggest_adaptations(reflection_type)
                ))

        return self_reflections
```

---

## 2. Rules Engine - Inteligentne Reguły Architektoniczne 🔍

**Plik:** `feniks/core/reflection/rules.py`

**Analizuje architekturę kodu** niezależnie od Qdrant:

### 2.1. Dostępne Reguły

#### Reguła 1: God Modules Detection
```python
ReflectionRule(
    id="god_modules",
    name="God Modules Detected",
    condition=lambda sm: len(sm.god_modules) > 0,
    impact=ReflectionImpact.REFACTOR_RECOMMENDED,
    generate=self._generate_god_modules_reflection
)
```
**Co wykrywa:** Moduły z nadmiernymi zależnościami (>20 dependencies)

#### Reguła 2: Hotspot Detection
```python
ReflectionRule(
    id="hotspot_modules",
    name="Hotspot Modules Identified",
    condition=lambda sm: len(sm.hotspot_modules) > 0,
    impact=ReflectionImpact.REFACTOR_RECOMMENDED
)
```
**Co wykrywa:** Moduły wysokiego ryzyka (high complexity + high connectivity)

#### Reguła 3: High System Complexity
```python
ReflectionRule(
    id="high_complexity",
    condition=lambda sm: sm.avg_module_complexity > 50,
    impact=ReflectionImpact.MONITOR
)
```
**Co wykrywa:** System z wysoką złożonością cyklomatyczną

#### Reguła 4: Centralization Risk
```python
ReflectionRule(
    id="centralization_risk",
    condition=lambda sm: len(sm.central_modules) > len(sm.modules) * 0.3,
    impact=ReflectionImpact.MONITOR
)
```
**Co wykrywa:** Over-centralization (>30% modułów to central nodes)

#### Reguła 5: Poor Module Isolation
```python
ReflectionRule(
    id="poor_isolation",
    condition=lambda sm: self._check_high_coupling(sm),
    impact=ReflectionImpact.REFACTOR_RECOMMENDED
)
```
**Co wykrywa:** Wysokie coupling między modułami

#### Reguła 6: Large Modules
```python
ReflectionRule(
    id="large_modules",
    condition=lambda sm: self._check_large_modules(sm),
    impact=ReflectionImpact.MONITOR
)
```
**Co wykrywa:** Zbyt duże moduły (>1000 linii)

#### Reguła 7: Capability Diversity
```python
ReflectionRule(
    id="capability_diversity",
    condition=lambda sm: len(sm.capabilities) >= 5,
    impact=ReflectionImpact.INFORMATIONAL
)
```
**Co wykrywa:** System z bogатым zestawem capabilities

#### Reguła 8: Architecture Quality
```python
ReflectionRule(
    id="architecture_quality",
    condition=lambda sm: True,  # Always runs
    impact=ReflectionImpact.INFORMATIONAL
)
```
**Co robi:** Ogólna ocena jakości architektury

### 2.2. Przykład działania Rules Engine

```python
class ReflectionRuleSet:
    def evaluate(self, system_model: SystemModel) -> List[MetaReflection]:
        reflections = []

        for rule in self.rules:
            if rule.condition(system_model):
                reflection = rule.generate(system_model)
                reflections.append(reflection)

        return reflections

# Przykład użycia
system_model = build_system_model(chunks)
rules = ReflectionRuleSet()
reflections = rules.evaluate(system_model)

# Output:
# [
#   MetaReflection(title="God Modules Detected", modules=["UserService", "DataManager"]),
#   MetaReflection(title="High System Complexity", avg_complexity=67.5),
#   MetaReflection(title="Over-Centralized Architecture", central_ratio=0.35)
# ]
```

---

## 3. Policy Manager - Real-time Guardrails 🛡️

**Plik:** `feniks/core/policies/manager.py`

**Real-time enforcement** niezależnie od vectorów:

### 3.1. Cost Policies

**Plik:** `feniks/core/policies/cost_policy.py`

```python
class CostPolicyEnforcer:
    MAX_SESSION_COST = 1.0  # $1.00
    BUDGET_WARNING_THRESHOLD = 0.8  # 80% of budget

    def check_session_cost(self, session: SessionSummary) -> List[MetaReflection]:
        violations = []

        if session.cost_profile.cost_usd > self.MAX_SESSION_COST:
            violations.append(MetaReflection(
                title="Max Session Cost Exceeded",
                content=f"Session cost ${session.cost_profile.cost_usd:.2f} > ${self.MAX_SESSION_COST:.2f}",
                impact=ReflectionImpact.CRITICAL
            ))

        return violations

    def check_budget_health(self, project: str) -> List[MetaReflection]:
        budget = get_project_budget(project)
        spent = get_project_spent(project)

        if spent / budget > self.BUDGET_WARNING_THRESHOLD:
            return [MetaReflection(
                title="Budget Threshold Exceeded",
                content=f"Project spent {spent/budget:.1%} of budget",
                impact=ReflectionImpact.MONITOR
            )]

        return []
```

### 3.2. Quality Policies

**Plik:** `feniks/core/policies/quality_policy.py`

```python
class QualityPolicyEnforcer:
    MIN_THOUGHT_LENGTH = 10  # characters
    FORBIDDEN_PATTERNS = [
        r"not sure",
        r"I don't know",
        r"unclear",
        r"maybe",
        r"perhaps"
    ]

    def check_trace_quality(self, session: SessionSummary) -> List[MetaReflection]:
        violations = []

        # Check for short thoughts
        short_thoughts = [
            t for t in session.reasoning_traces
            if len(t.thought.strip()) < self.MIN_THOUGHT_LENGTH
        ]

        if short_thoughts:
            violations.append(MetaReflection(
                title="Reasoning Steps Too Short",
                content=f"Found {len(short_thoughts)} steps with thoughts <{self.MIN_THOUGHT_LENGTH} chars",
                impact=ReflectionImpact.REFACTOR_RECOMMENDED
            ))

        # Check for forbidden patterns
        for trace in session.reasoning_traces:
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, trace.thought, re.IGNORECASE):
                    violations.append(MetaReflection(
                        title="Uncertain Reasoning Detected",
                        content=f"Step {trace.step_id} contains '{pattern}'",
                        impact=ReflectionImpact.MONITOR
                    ))

        return violations
```

### 3.3. Behavior Risk Policies

**Plik:** `feniks/core/policies/behavior_risk_policy.py`

```python
class MaxBehaviorRiskPolicy:
    def __init__(self, max_risk_score: float = 0.5, max_failed_scenarios: int = 0):
        self.max_risk_score = max_risk_score
        self.max_failed_scenarios = max_failed_scenarios

    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        summary = report.behavior_checks_summary

        if not summary:
            return PolicyEvaluationResult(
                passed=False,
                reason="No behavior checks executed"
            )

        if summary.max_risk_score > self.max_risk_score:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"Risk score {summary.max_risk_score:.2f} > {self.max_risk_score:.2f}"
            )

        if summary.total_failed > self.max_failed_scenarios:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"{summary.total_failed} scenarios failed"
            )

        return PolicyEvaluationResult(passed=True)
```

---

## 4. System Model Builder - Dependency Graph Analysis 🕸️

**Plik:** `feniks/core/reflection/system_model.py`

**Buduje graf zależności** i oblicza metryki:

### 4.1. Co buduje:

```python
def build_system_model(chunks: List[Chunk]) -> SystemModel:
    # 1. Build dependency graph
    graph = nx.DiGraph()
    for chunk in chunks:
        graph.add_node(chunk.module)
        for dep in chunk.dependencies:
            graph.add_edge(chunk.module, dep.value)

    # 2. Calculate centrality metrics
    betweenness = nx.betweenness_centrality(graph)
    eigenvector = nx.eigenvector_centrality(graph)

    # 3. Identify central modules (high centrality)
    central_modules = [
        node for node, score in betweenness.items()
        if score > 0.1
    ]

    # 4. Identify god modules (too many dependencies)
    god_modules = [
        module for module, degree in graph.out_degree()
        if degree > 20
    ]

    # 5. Identify hotspots (high complexity + high connectivity)
    hotspot_modules = []
    for module in modules:
        complexity = get_module_complexity(module)
        connectivity = graph.degree(module)
        if complexity > 30 and connectivity > 10:
            hotspot_modules.append(module)

    return SystemModel(
        modules=modules,
        dependencies=dependencies,
        central_modules=central_modules,
        god_modules=god_modules,
        hotspot_modules=hotspot_modules,
        avg_module_complexity=avg_complexity
    )
```

### 4.2. Metryki obliczane:

- **Betweenness Centrality** - jak ważny jest moduł dla przepływu w grafie
- **Eigenvector Centrality** - jak ważni są sąsiedzi modułu
- **Degree Centrality** - ile zależności ma moduł
- **Cyclomatic Complexity** - złożoność cyklomatyczna
- **Module Size** - ilość linii kodu

---

## 5. Capability Detector - Semantyczna Analiza 🎨

**Plik:** `feniks/core/reflection/capabilities.py`

**Wykrywa co system robi** na podstawie kodu:

### 5.1. Typy Capabilities:

```python
class CapabilityDetector:
    def detect_capabilities(self, chunks: List[Chunk]) -> List[Capability]:
        capabilities = []

        # 1. API Endpoints
        api_chunks = [c for c in chunks if c.api_endpoints]
        if api_chunks:
            capabilities.append(Capability(
                type="api",
                name="REST API",
                evidence=[c.file_path for c in api_chunks],
                confidence=0.95
            ))

        # 2. UI Components
        ui_chunks = [c for c in chunks if c.ui_routes or "component" in c.kind.lower()]
        if ui_chunks:
            capabilities.append(Capability(
                type="ui",
                name="User Interface",
                evidence=[c.chunk_name for c in ui_chunks],
                confidence=0.90
            ))

        # 3. Background Jobs
        batch_keywords = ["cron", "scheduler", "job", "worker", "task"]
        batch_chunks = [
            c for c in chunks
            if any(keyword in c.text.lower() for keyword in batch_keywords)
        ]
        if batch_chunks:
            capabilities.append(Capability(
                type="batch",
                name="Background Processing",
                evidence=batch_keywords_found,
                confidence=0.80
            ))

        # 4. Database Operations
        db_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "query", "transaction"]
        db_chunks = [
            c for c in chunks
            if any(keyword in c.text for keyword in db_keywords)
        ]
        if db_chunks:
            capabilities.append(Capability(
                type="database",
                name="Database Operations",
                evidence=db_keywords_found,
                confidence=0.85
            ))

        # 5. Authentication
        auth_keywords = ["login", "authenticate", "authorize", "token", "jwt", "session"]
        auth_chunks = [
            c for c in chunks
            if any(keyword in c.text.lower() for keyword in auth_keywords)
        ]
        if auth_chunks:
            capabilities.append(Capability(
                type="security",
                name="Authentication",
                evidence=auth_keywords_found,
                confidence=0.75
            ))

        return capabilities
```

---

## 6. Legacy Behavior Guard - Regression Testing 📸

**Pliki:** `feniks/core/models/behavior.py`, `feniks/core/policies/behavior_risk_policy.py`

**Wykrywa regresje** bez tradycyjnych testów:

### 6.1. Jak działa:

```python
# 1. Record legacy behavior
legacy_snapshot = record_scenario(scenario_id="login", environment="legacy")
# ObservedHTTP(status_code=200, body={"success": True})

# 2. Build contract
contract = build_contract([legacy_snapshot1, legacy_snapshot2, ...])
# BehaviorContract(
#     http_contract=HTTPContract(required_status_codes=[200]),
#     dom_contract=DOMContract(must_have_selectors=["#dashboard"])
# )

# 3. Check candidate behavior
candidate_snapshot = record_scenario(scenario_id="login", environment="candidate")
# ObservedHTTP(status_code=500, body={"error": "Internal Server Error"})

# 4. Compare
check_result = compare_snapshot_with_contract(candidate_snapshot, contract)
# BehaviorCheckResult(
#     passed=False,
#     violations=[BehaviorViolation(code="HTTP_STATUS_MISMATCH", severity="critical")],
#     risk_score=0.9  # High risk!
# )

# 5. Policy enforcement
policy = MaxBehaviorRiskPolicy(max_risk_score=0.5)
policy_result = policy.evaluate(feniks_report)
# PolicyEvaluationResult(
#     passed=False,
#     reason="Risk score 0.9 exceeds threshold 0.5"
# )
```

---

## 7. RAE Integration - Długoterminowa Pamięć 📚

**Plik:** `feniks/adapters/rae_client/client.py`

**Synchronizacja z RAE** (Reflective Agent Engine):

```python
def sync_with_rae(system_model: SystemModel, meta_reflections: List[MetaReflection]):
    rae_client = create_rae_client()

    # 1. Store reflections in RAE
    for reflection in meta_reflections:
        rae_client.store_reflection(
            project=system_model.project,
            reflection_data=reflection.to_dict()
        )

    # 2. Retrieve historical context
    historical_reflections = rae_client.get_reflections(
        project=system_model.project,
        limit=100
    )

    # 3. Use context for next analysis
    # Next run will have access to all previous insights
```

**Korzyści:**
- 💾 Długoterminowa pamięć (nie tylko Qdrant chunks)
- 📈 Uczenie się w czasie
- 🎯 Context-aware analysis
- 🔄 Continuous improvement

---

## 8. Podsumowanie: Multi-Layered Intelligence

Feniks to **multi-layered analysis system**:

### Warstwa 1: Storage (Qdrant)
- Przechowuje chunki kodu jako wektory
- Fast retrieval dla context

### Warstwa 2: Structural Analysis
- **Rules Engine** - wykrywa anti-patterns
- **System Model** - dependency graph, metrics
- **Capability Detector** - semantic understanding

### Warstwa 3: Behavioral Analysis
- **Post-Mortem** - pojedyncze sesje
- **Longitudinal** - trendy w czasie
- **Behavior Guard** - regression detection

### Warstwa 4: Policy Enforcement
- **Cost Policies** - budget control
- **Quality Policies** - code quality standards
- **Behavior Policies** - regression prevention

### Warstwa 5: Meta-Learning
- **Self-Model** - learns from experience
- **RAE Integration** - long-term memory
- **Adaptive Strategies** - improves over time

---

## 9. Przykład: Kompletny Flow Analizy

```python
# 1. Load chunks from Qdrant (STORAGE)
chunks = qdrant_client.load_chunks(collection="my_project")

# 2. Build system model (STRUCTURAL)
system_model = build_system_model(chunks)
# Output: central_modules, god_modules, hotspots, dependencies graph

# 3. Detect capabilities (SEMANTIC)
capabilities = CapabilityDetector().detect_capabilities(chunks)
# Output: ["REST API", "User Interface", "Background Jobs", "Authentication"]

# 4. Apply reflection rules (BEHAVIORAL)
rules = ReflectionRuleSet()
reflections = rules.evaluate(system_model)
# Output: [
#   "God Modules Detected: UserService (35 dependencies)",
#   "High System Complexity: avg=67.5 (threshold: 50)",
#   "Hotspot: AuthModule (complexity=85, connectivity=23)"
# ]

# 5. Enforce policies (GUARDRAILS)
policy_manager = PolicyManager()
violations = policy_manager.check_session_compliance(session, project)
# Output: [
#   "Max Session Cost Exceeded: $1.25 > $1.00",
#   "Reasoning Steps Too Short: 3 steps <10 chars"
# ]

# 6. Sync with RAE (META-LEARNING)
rae_client.store_reflections(project, reflections)
# Next analysis will have access to these insights

# 7. Generate final report
report = FeniksReport(
    project=project,
    summary=session_summary,
    metrics={"complexity": 67.5, "centrality_max": 0.45},
    recommendations=[
        "Refactor UserService - too many dependencies",
        "Review AuthModule - complexity hotspot",
        "Implement caching - costs increasing"
    ],
    behavior_checks_summary=behavior_summary,  # If behavior checks ran
    behavior_violations=violations
)
```

---

## 10. Kluczowe Różnice vs. Prosta Analiza Vectorów

| Aspekt | Prosta Analiza Vectorów | Feniks Intelligence |
|--------|------------------------|---------------------|
| **Wykrywanie wzorców** | Similarity search | Rules Engine + Graph Analysis |
| **Analiza zachowania** | ❌ Brak | Post-Mortem + Longitudinal + Behavior Guard |
| **Enforc policy** | ❌ Brak | Real-time guardrails (cost, quality, risk) |
| **Uczenie się** | ❌ Brak | Self-Model + RAE integration |
| **Context** | Lokalne chunki | Global system model + historical insights |
| **Depth** | Shallow (text matching) | Deep (semantics, architecture, trends) |

---

**Wnioski:**
1. **Qdrant to tylko 10% Feniksa** - storage layer
2. **Prawdziwa inteligencja to 90%** - Core/Reflection/Policies
3. **Multi-layered approach** - od struktury do meta-uczenia się
4. **Production-ready** - real-time enforcement, long-term memory

---

*Dokument utworzony: 2025-11-26*
*Wersja: 1.0*
