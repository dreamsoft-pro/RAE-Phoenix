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

### 4. Dostępność
*   **CLI**: Potężne narzędzie wiersza poleceń do integracji z CI/CD.
*   **REST API**: Nowoczesne API (FastAPI) do integracji z dashboardami i zewnętrznymi narzędziami.

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

## 🤝 Contributing

Jesteśmy otwarci na kontrybucje! Zapoznaj się z [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) przed zgłoszeniem PR.

---

**Feniks Team**  
*Bringing consciousness to code analysis.*