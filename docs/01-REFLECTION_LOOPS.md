REFLECTION_LOOPS.md
# Feniks — Pętle Refleksji
**Stan: RAE-FENIKS-STATE-26-11-2025**

Feniks stosuje trzy główne pętle meta-refleksji.

---

# 🔄 1. Pętla „Post-mortem”
Analiza zakończonej sesji RAE.

### Wejście:
- Reasoning trace
- Logi kroków
- Koszty tokenowe
- Wyniki zapytań do pamięci
- Output agenta

### Wyjścia:
- Raport jakości reasoning (Quality Score)
- Wykryte problemy
- Wzorce błędów
- Zalecenia dla RAE

---

# 🔄 2. Pętla „Longitudinal”
Analiza *historii wielu sesji*.

### Wykrywa:
- powtarzalne błędy,
- rosnące koszty,
- złe strategie reasoning,
- nieefektywne pętle,
- regresem jakości.

### Wynik:
- PatternMap (mapa wzorców)
- TrendMetrics (metryki trendów)
- MetaRecommendations (zalecenia)

---

# 🔄 3. Pętla „Self-Model”
Feniks buduje *model samego siebie* i RAE.

### Dla RAE:
- jak często używa niepotrzebnie BFS?
- kiedy generuje za długie odpowiedzi?
- ile kosztuje retrieval?
- kiedy agent się zapętla?
- ile spraw załatwia bez pamięci?

### Dla Feniksa:
- czas przetwarzania,
- jakość raportów,
- precyzja wykrywania problemów.

---

# 🔧 Mechanika pętli refleksji

### 1. Zbieranie
Dane pobierane są z RAE przez `rae_client`.

### 2. Transformacja
Tworzony jest ujednolicony `SessionSummary`.

### 3. Ocena
Moduły:
- `evaluation/reasoning_scoring.py`
- `evaluation/error_patterns.py`
- `evaluation/cost_analysis.py`

### 4. Polityki
Sprawdzane są polityki:
- kosztowe,
- jakościowe,
- strukturalne.

### 5. Raport
Tworzy się obiekt:
`FeniksReport`

---

# 📊 Struktura FeniksReport

```json
{
  "session_id": "abc123",
  "scores": {
    "quality": 0.92,
    "efficiency": 0.81,
    "cost": 0.55
  },
  "cost_profile": {...},
  "detected_patterns": [...],
  "policy_violations": [...],
  "recommendations": [...]
}

🧪 Testowalność

Każda pętla refleksji musi być:

deterministyczna,

testowalna,

niezależna od LLM,

oparta na SessionSummary.