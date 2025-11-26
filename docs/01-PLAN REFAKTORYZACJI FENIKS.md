# PLAN REFAKTORYZACJI FENIKS  
**Cel: Feniks jako projekt Hi-Quality / World Class**

Plan jest podzielony na 20 precyzyjnych zadań, z kryteriami sukcesu.

---

## 🔥 Faza 1 — Porządkowanie architektury

### **Zadanie 1: Uporządkowanie katalogów**
- Przenieść moduły do `core/`, `adapters/`, `apps/`, `infra/`.
- Poprawić importy.
- Dodać `__init__.py`.

**Kryterium sukcesu:**  
Repo przechodzi `pytest`, a importy są spójne.

---

### **Zadanie 2: Dodanie Pydantic models**
Stworzyć:
- `SessionSummary`
- `ReasoningTrace`
- `CostProfile`
- `FeniksReport`

**Kryterium:**  
Każdy raport używa nowych modeli.

---

### **Zadanie 3: Dodanie adaptera `rae_client`**
- Wrapper na RAE API.

**Kryterium:**  
Jedno źródło prawdy, zero powtórzeń.

---

## 🔥 Faza 2 — Testowalność

### **Zadanie 4: Testy dla transformacji SessionSummary**
Pokryć przypadki:
- duże sesje,
- sesje bez reasoning,
- sesje z pętlami.

### **Zadanie 5: Testy dla evaluation**
- scoring quality
- scoring efficiency
- wykrywanie pętli reasoning

---

## 🔥 Faza 3 — Pętle refleksji

### **Zadanie 6: Implementacja post-mortem loop**
- analiza jednej sesji,
- scoring,
- rekomendacje.

### **Zadanie 7: Implementacja longitudinal loop**
- analiza wielu sesji,
- wykrywanie trendów.

### **Zadanie 8: Implementacja self-model loop**
- mierzenie jakości Feniksa.

---

## 🔥 Faza 4 — Polityki i guardrails

### **Zadanie 9: Polityki kosztowe**
- limity tokenów,
- alerty.

### **Zadanie 10: Polityki jakości reasoning**
- progi minimalne,
- klasyfikacja problemów.

---

## 🔥 Faza 5 — Infrastrukturę

### **Zadanie 11: Logging**
- strukturalny JSON,
- trace ID.

### **Zadanie 12: Metrics**
- Prometheus style:
  - feniks_cost_total
  - feniks_quality_score
  - feniks_recommendations_count

### **Zadanie 13: Tracing**
- OpenTelemetry,
- span per step reasoning.

---

## 🔥 Faza 6 — API i CLI

### **Zadanie 14: Minimalne API**
- `POST /sessions/analyze`
- `GET /report/{id}`
- `GET /patterns/errors`

### **Zadanie 15: CLI**
- `feniks analyze-session`
- `feniks compare-sessions`

---

## 🔥 Faza 7 — Dokumentacja

### **Zadanie 16: README**
- jasny opis,
- szybki start.

### **Zadanie 17: ARCHITECTURE.md**
- diagram
- opis modułów

### **Zadanie 18: REFLECTION_LOOPS.md**

---

## 🔥 Faza 8 — Przygotowanie pod AI Refactor

### **Zadanie 19: AGENT_PLAYBOOK.md**
- instrukcje dla AI agentów

### **Zadanie 20: Golden Test Fixtures**
- 5 przykładowych sesji RAE
- testy porównawcze

**Kryterium:**  
Agent może bezpiecznie wykonać PR.

---

# 🏁 Koniec planu
Ten plan prowadzi Feniksa do stanu **High Quality / World Class**,  
gotowego do refaktoryzacji zarówno przez ludzi, jak i autonomiczne agentowe pipeline’y.
