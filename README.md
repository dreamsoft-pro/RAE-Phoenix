# 🦅 Feniks: Meta-Reflective Code Analysis Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![Architecture](https://img.shields.io/badge/architecture-hexagonal-orange)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-green)]()

**Feniks** to system klasy Enterprise do statycznej analizy kodu, wzbogacony o unikalną warstwę **Meta-Refleksji**. W przeciwieństwie do tradycyjnych linterów, Feniks nie tylko znajduje błędy składniowe, ale analizuje *sens* i *jakość* procesu deweloperskiego (reasoning), wykrywa długoterminowe trendy w kodzie i pilnuje budżetów operacyjnych AI.

Został zaprojektowany jako warstwa analityczna nad silnikiem **RAE (Reflective Agent Engine)**.

---

## 🚀 Kluczowe Funkcjonalności

### 1. Architektura Wiedzy (Knowledge Base)
*   **Ingest Pipeline**: Inteligentne parsowanie kodu (JS/TS, Python, HTML) do postaci wektorowej (Qdrant).
*   **Semantic Understanding**: Wykorzystuje modele embeddingów do zrozumienia intencji kodu, a nie tylko jego struktury.

### 2. Silnik Meta-Refleksji (The Brain)
*   **Post-Mortem Loop**: Analiza pojedynczych sesji agentów pod kątem błędów w rozumowaniu, pętli decyzyjnych i kosztów.
*   **Longitudinal Loop**: Wykrywanie trendów w czasie (np. "Jakość kodu w module Auth spada od 3 tygodni").
*   **Self-Model Loop**: System monitoruje własną wydajność i ryzyko "zmęczenia alertami" (Alert Fatigue).

### 3. Governance & Guardrails
*   **Cost Controller**: Ścisła kontrola budżetów tokenów na poziomie projektu i sesji.
*   **Quality Policies**: Egzekwowanie standardów rozumowania (np. "Zakaz pustych myśli przed podjęciem akcji").
*   **Behavior Risk Policies**: MaxBehaviorRiskPolicy, ZeroRegressionPolicy dla legacy systems.

### 4. Legacy Behavior Guard 🆕
*   **Behavior Contracts**: Zastępuje testy regresyjne dla systemów bez testów.
*   **Snapshot Comparison**: Porównuje zachowanie before/after refactoringu.
*   **Risk Scoring**: Automatyczna ocena ryzyka regresji (0.0-1.0).
*   **Multi-layer Validation**: HTTP status, DOM elements, log patterns.
*   **CI/CD Integration**: Blokuj merge przy wysokim ryzyku.
*   Szczegóły w [docs/LEGACY_BEHAVIOR_GUARD.md](docs/LEGACY_BEHAVIOR_GUARD.md)

### 5. Dostępność
*   **CLI**: Potężne narzędzie wiersza poleceń do integracji z CI/CD.
*   **REST API**: Nowoczesne API (FastAPI) do integracji z dashboardami i zewnętrznymi narzędziami.
*   **Behavior CLI**: Dedykowane komendy dla Legacy Behavior Guard (`feniks behavior`).

---

## ⚡ Quick Start

### Wymagania
*   Python 3.10+
*   Qdrant (uruchomiony lokalnie lub w chmurze)
*   Zmienne środowiskowe (skopiuj `.env.example` do `.env`)

### Instalacja

```bash
# 1. Klonowanie repozytorium
git clone https://github.com/your-org/feniks.git
cd feniks

# 2. Utworzenie wirtualnego środowiska
python3 -m venv venv
source venv/bin/activate

# 3. Instalacja w trybie developerskim
pip install -e .
```

### Użycie CLI

**1. Ingest (Zasilenie bazy wiedzy):**
```bash
feniks ingest --jsonl-path ./data/source_code.jsonl --collection my_project_v1 --reset
```

**2. Analiza (Uruchomienie pipeline'u):**
```bash
feniks analyze --project-id my_project --collection my_project_v1 --output report.md
```

**3. Uruchomienie API:**
```bash
feniks serve-api --port 8000
```

**4. Legacy Behavior Guard (testowanie bez testów):**
```bash
# Nagranie zachowania legacy system
feniks behavior record --project-id my_app --scenario-id login --environment legacy --output legacy_snapshots.jsonl

# Budowa kontraktów
feniks behavior build-contracts --project-id my_app --input legacy_snapshots.jsonl --output contracts.jsonl

# Sprawdzenie refactored system
feniks behavior check --project-id my_app --contracts contracts.jsonl --snapshots candidate_snapshots.jsonl --output results.jsonl --fail-on-violations
```

---

## 🏛️ Przegląd Architektury

Feniks stosuje czystą architekturę (Clean Architecture / Hexagonal), separując logikę biznesową od infrastruktury.

```
feniks/
├── apps/           # Punkty wejścia (CLI, API, Workers)
├── core/           # Logika biznesowa (Reflection, Evaluation, Policies)
├── adapters/       # Integracje (Qdrant, RAE, LLM)
├── infra/          # Infrastruktura techniczna (Logging, Tracing, Metrics)
└── config/         # Konfiguracja (Pydantic Settings)
```

Szczegóły w [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📊 Metryki i Obserwowalność

Feniks natywnie wspiera ustrukturyzowane logowanie (JSON) i metryki biznesowe.

*   **Trace ID**: Każda operacja posiada unikalny identyfikator śledzenia.
*   **Metryki**:
    *   `feniks_quality_score`: Bieżąca ocena jakości projektu.
    *   `feniks_cost_total`: Łączny koszt operacyjny.
    *   `feniks_recommendations_count`: Liczba wygenerowanych sugestii naprawczych.

---

## 📚 Dokumentacja

### Architektura i Mechanizmy
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architektura systemu, data flow, komponenty
- **[ANALYSIS_MECHANISMS.md](docs/ANALYSIS_MECHANISMS.md)** - 🆕 Szczegółowy opis mechanizmów analizy (Post-Mortem, Rules Engine, Policies)
- **[REFLECTION_LOOPS.md](docs/REFLECTION_LOOPS.md)** - Pętle refleksji: Post-Mortem, Longitudinal, Self-Model

### Legacy Behavior Guard
- **[LEGACY_BEHAVIOR_GUARD.md](docs/LEGACY_BEHAVIOR_GUARD.md)** - 🆕 Kompletny przewodnik po Legacy Behavior Guard
- **[BEHAVIOR_CONTRACT_MODELS.md](docs/BEHAVIOR_CONTRACT_MODELS.md)** - 🆕 Specyfikacja modeli Behavior
- **[examples/](docs/examples/)** - 🆕 Przykładowe scenariusze YAML (UI, API, CLI)

### Historia i Postęp
- **[CHANGELOG.md](CHANGELOG.md)** - 🆕 Historia zmian i postęp prac w czasie
- **[IMPLEMENTACJA_PLANU_NAPRAWY_PODSUMOWANIE.md](docs/IMPLEMENTACJA_PLANU_NAPRAWY_PODSUMOWANIE.md)** - Podsumowanie upgrade do Enterprise-Grade

### Dla Deweloperów
- **[AGENT_PLAYBOOK.md](docs/AGENT_PLAYBOOK.md)** - Playbook dla AI agentów
- **[RAE_INTEGRATION.md](docs/RAE_INTEGRATION.md)** - Integracja z RAE
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Guidelines dla kontrybutorów

---

## 🎯 Status Projektu

- **Wersja:** 0.2.0 (Deep Integration Complete)
- **Status:** ⭐⭐⭐⭐⭐ Production Ready
- **Test Coverage:** 80%+
- **Commity:** 60+
- **Linie kodu:** ~17,500+
- **Ostatnia aktualizacja:** 2025-11-26

### Najnowsze Dodatki (2025-11-26)
- ✅ **Legacy Behavior Guard - Phase 2** - Deep Integration Complete (9 commitów, 2,500 linii)
  - Storage layer (BehaviorStore)
  - Scenario runners (HTTP, CLI)
  - Contract generation algorithms
  - Behavior comparison engine
  - Reflection loop integrations (Post-Mortem, Longitudinal)
  - Policy settings integration
  - Comprehensive test suite (20+ tests)
- ✅ **Legacy Behavior Guard - Phase 1** - Complete (6 commitów, 2,700 linii)
- ✅ **Enterprise Upgrade** - 14 zadań, 80%+ coverage (14 commitów, 1,868 linii)
- ✅ **CI/CD Pipeline** - GitHub Actions multi-version testing
- ✅ **OpenTelemetry + Prometheus** - Full observability
- ✅ **Auth + RBAC** - JWT authentication, role-based access

---

## 🤝 Contributing

Jesteśmy otwarci na kontrybucje! Zapoznaj się z [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) przed zgłoszeniem PR.

---

## 📄 Licencja

Apache License 2.0 - Zobacz [LICENSE](LICENSE) dla szczegółów.

---

**Feniks Team** - Grzegorz Leśniowski
*Bringing consciousness to code analysis.*

🦅 **Feniks nie tylko analizuje kod - rozumie jego sens i ewolucję.**