FENIKS_VISION.md
# Feniks — Warstwa Meta-Refleksji nad RAE  
**Stan: RAE-FENIKS-STATE-26-11-2025**

Feniks jest warstwą *meta-myślenia* nad silnikiem RAE.  
Nie jest kolejnym RAG-iem, nie jest bazą wiedzy, nie jest warstwą API.

Feniks jest systemem, który **analizuje, obserwuje i ocenia RAE**, a następnie:
- wykrywa błędy,
- śledzi wzorce działania,
- przewiduje koszty,
- optymalizuje pętle reasoning,
- monitoruje jakość,
- rekomenduje zmiany.

Feniks ma umożliwiać:
- *autonomiczny nadzór* nad agentami,
- *meta-refleksję* nad procesami,
- *kontrolę jakości* reasoning,
- *kontrolę kosztów*.

---

## 🎯 Cele Feniksa
### 1. **Meta-refleksja nad RAE**
Feniks rozumie *jak RAE pracuje*, a nie tylko „co” zwrócił API.  
Przechowuje i analizuje:
- ścieżki reasoning,
- koszty tokenowe,
- przebieg sesji,
- decyzje w czasie.

### 2. **Model samo-analizy systemu**
Feniks generuje „self-model” systemu RAE+agents:
- w czym są mocni,
- gdzie popełniają błędy,
- jak skrócić reasoning,
- jakie strategie działają lepiej.

### 3. **Warstwa jakości i audytu**
Feniks tworzy raporty:
- poprawności reasoning,
- jakości outputów,
- powtarzalnych problemów,
- nieefektywności kosztów.

### 4. **Warstwa governance + guardrails**
Feniks ocenia zgodność z politykami:
- limity kosztów,
- limity głębokości reasoning,
- zachowanie zgodne z regułami/meta-policy.

---

## 🚫 Co Feniks NIE robi
- nie obsługuje klientów końcowych,
- nie jest RAG-iem,
- nie przechowuje długoterminowych danych użytkowników,
- nie generuje embeddingów,
- nie jest agentem wykonawczym.

Feniks to *meta-warstwa* — nie *warstwa operacyjna*.

---

## 🧠 Model działania Feniksa
### Feniks analizuje dane z:
- RAE (pamięci)
- agenta LLM
- logów reasoning
- pomiarów kosztów
- przebiegu sesji API

A następnie przetwarza je w:
- raport meta-reasoning  
- rekomendacje  
- scoring jakości  
- wykryte wzorce błędów  
- modele optymalizacji  

---

## 🔮 Kierunek rozwoju
- Rozszerzenie feniksowych pętli refleksji.
- Wprowadzenie modelu scoringu reasoning.
- Rejestracja meta-metryk.
- Integracja z politykami (policy packs).
- Zautomatyzowane meta-rekomendacje.
- API na GitHub (Feniks Cloud).
- Ułatwienie refaktoryzacji przez AI (agent-friendly design).

---