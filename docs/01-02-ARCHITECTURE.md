ARCHITECTURE.md
# Feniks — Architektura Systemu  
**Stan: RAE-FENIKS-STATE-26-11-2025**

Feniks jest warstwą meta-refleksyjnej analityki nad silnikiem RAE.  
Jego architektura została zaprojektowana według zasady:

🎯 **Core → Adapters → Apps → Interfaces**

---

# 📂 Struktura katalogów



feniks/
apps/
api/
cli/
workers/
core/
reflection/
evaluation/
policies/
models/
adapters/
rae_client/
storage/
llm/
config/
settings.py
infra/
logging.py
metrics.py
tracing.py
tests/
unit/
integration/
e2e/
docs/


---

# 🔧 Moduły

## `core/reflection/`
- Pętle meta-reasoning  
- Główna pętla Feniksa  
- Analiza historyczna  
- Modele meta-decyzyjne  

## `core/evaluation/`
- Ocena jakości reasoning  
- Porównywanie sesji  
- Wykrywanie patternów błędów  
- Generowanie scoringów i ocen  

## `core/policies/`
- Polityki jakości  
- Progi kosztów  
- Guardrails  
- Zasady meta-bezpieczeństwa  

## `core/models/`
- Kontrakty danych Feniksa:
  - `FeniksReport`
  - `SessionSummary`
  - `ReasoningTrace`
  - `CostProfile`
  - `PatternMatch`
  - `PolicyViolation`

---

## `adapters/rae_client/`
Abstrakcja komunikacji z RAE:
- pobieranie sesji,
- pobieranie historii,
- zapytania wektorowe,
- dane z metryk.

## `adapters/llm/`
- jednolity interfejs LLMClient
- implementacje:
  - OpenAI
  - Gemini
  - Claude
  - Lokalny model

---

## `adapters/storage/`
- Postgres (sesje Feniksa, raporty)
- Qdrant lub Elastic (patterny reasoning)

---

## `apps/api/`
Minimalne API (stabilne kontrakty):
- `POST /sessions/analyze`
- `GET /sessions/{id}/report`
- `GET /patterns/errors`
- `GET /metrics/overview`

---

## `apps/cli/`
- `feniks analyze-session`
- `feniks compare-sessions`
- `feniks export-report`

---

## `apps/workers/`
- batch analysis  
- async scoring  
- przypominanie o przekroczeniach polityk  

---

# 🔍 Przepływ danych — diagram wysokiego poziomu


    ┌──────────┐
    │   RAE    │
    └────┬─────┘
         │ (sesje, logi, koszty)
         ▼
  ┌──────────────┐
  │   Feniks     │
  │  Reflection  │
  └────┬────┬────┘
       │    │


┌───────┘ └────────────────────┐
▼                              ▼
Evaluation Policies/Guardrails
│                              │
└──────────┬───────────────────┘
           ▼
           Feniks Report
           │
           ▼
           Storage
           │
           ▼
           API / CLI Output


---

# 🧩 Zasady architektoniczne

1. **Core nigdy nie importuje adapterów**
2. **Apps to tylko cienkie warstwy**
3. **Kontrakty danych są niezmienne i w `core/models`**
4. **Pętle refleksji są czyste, deterministyczne i testowalne**
5. **Każda funkcja musi mieć test (unit lub integration)**
6. **Każda zmiana ma przejść przez pre-commit + CI**

---