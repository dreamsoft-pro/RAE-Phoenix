# Architektura Systemu Feniks

**Wersja:** 2.0 (Enterprise Ready)  
**Data:** 26 Listopada 2025

## 1. Koncepcja Wysokopoziomowa

Feniks to system zaprojektowany w oparciu o zasady **Clean Architecture** (Architektura Cebulowa/Heksagonalna). Głównym celem tej architektury jest uniezależnienie logiki biznesowej (Core) od zewnętrznych frameworków, baz danych i interfejsów użytkownika.

### Diagram Warstw

```
+---------------------------------------------------------------+
|                      APPS (Warstwa Wejścia)                   |
|  +-------------+    +-------------+    +-------------------+  |
|  |     CLI     |    |   REST API  |    |  Async Workers    |  |
|  +------+------+    +------+------+    +---------+---------+  |
|         |                  |                     |            |
+---------|------------------|---------------------|------------+
          |                  |                     |
          v                  v                     v
+---------------------------------------------------------------+
|                      CORE (Logika Biznesowa)                  |
|                                                               |
|  +----------------+    +-----------------+    +------------+  |
|  |   Reflection   |    |   Evaluation    |    |  Policies  |  |
|  |    Engine      |    |    Pipeline     |    |  Manager   |  |
|  +-------+--------+    +--------+--------+    +-----+------+  |
|          |                      |                   |         |
|          +-----------+----------+-------------------+         |
|                      |                                        |
|              +-------v-------+                                |
|              | Domain Models |                                |
|              +---------------+                                |
+---------------------------------------------------------------+
          ^                  ^                     ^
          |                  |                     |
+---------|------------------|---------------------|------------+
|         |                  |                     |            |
|  +------+------+    +------+------+    +---------+---------+  |
|  |  Qdrant     |    |  RAE Client |    |   LLM Adapter     |  |
|  |  Adapter    |    |  Adapter    |    |   Adapter         |  |
|  +-------------+    +-------------+    +-------------------+  |
|                                                               |
|                   ADAPTERS (Infrastruktura)                   |
+---------------------------------------------------------------+
```

---

## 2. Opis Modułów

### 2.1. Core (`feniks/core`)
Serce systemu. Tutaj znajdują się reguły biznesowe, które nie zależą od żadnych zewnętrznych bibliotek (poza standardowymi).

*   **Models (`core/models`)**: Definicje obiektów domeny:
    *   `SessionSummary`, `FeniksReport`, `ReasoningTrace` - modele analizy kodu
    *   `BehaviorScenario`, `BehaviorSnapshot`, `BehaviorContract`, `BehaviorCheckResult` - modele Legacy Behavior Guard
    *   Są to czyste klasy danych (Pydantic), używane do komunikacji między warstwami.
*   **Reflection (`core/reflection`)**: Silnik meta-refleksji. Zawiera logikę analizy post-mortem, longitudinal i self-model. To tutaj zapadają decyzje o jakości kodu.
*   **Evaluation (`core/evaluation`)**: Pipeline przetwarzania danych. Koordynuje pobieranie danych, analizę i generowanie raportów.
*   **Policies (`core/policies`)**: Strażnicy systemu (Guardrails). Moduł ten zawiera reguły kosztowe i jakościowe, które są egzekwowane na każdym etapie analizy. Zawiera także polityki behavior risk (MaxBehaviorRiskPolicy, ZeroRegressionPolicy).

### 2.2. Adapters (`feniks/adapters`)
Warstwa odpowiedzialna za komunikację ze światem zewnętrznym. Implementuje interfejsy wymagane przez Core.

*   **Storage (`adapters/storage`)**: Obsługa Qdrant (baza wektorowa). Tłumaczy obiekty domenowe na punkty wektorowe i odwrotnie.
*   **RAE Client (`adapters/rae_client`)**: Klient integrujący się z silnikiem RAE. Wysyła i pobiera pamięć agentów.
*   **LLM (`adapters/llm`)**: Abstrakcja nad modelami językowymi (OpenAI, Gemini, Claude). Obecnie obsługuje głównie generowanie embeddingów.

### 2.3. Apps (`feniks/apps`)
Punkty wejścia do aplikacji. Te moduły "sklejają" system w całość, inicjalizując odpowiednie adaptery i przekazując je do Core.

*   **CLI (`apps/cli`)**: Interfejs wiersza poleceń.
    *   `main.py` - główne komendy (ingest, analyze, refactor, metrics)
    *   `behavior.py` - komendy Legacy Behavior Guard (record, build-contracts, check)
*   **API (`apps/api`)**: Serwer FastAPI udostępniający funkcjonalności przez HTTP.

### 2.4. Infra (`feniks/infra`)
Wspólne narzędzia infrastrukturalne (Cross-cutting concerns).

*   **Logging**: Ustrukturyzowane logowanie JSON.
*   **Tracing**: Śledzenie kontekstu wykonania (Trace ID, Span ID).
*   **Metrics**: Zbieranie metryk biznesowych i technicznych.

---

## 3. Przepływ Danych (Data Flow)

### Scenariusz: Analiza Post-Mortem

1.  **CLI/API** otrzymuje żądanie analizy sesji (`SessionSummary`).
2.  **Policy Manager** sprawdza, czy sesja nie przekroczyła budżetu lub nie zawiera rażących błędów jakościowych.
3.  **Reflection Engine** uruchamia analizę Post-Mortem:
    *   Analizuje ślady rozumowania (`ReasoningTrace`).
    *   Wykrywa pętle i puste akcje.
4.  **Evaluation Pipeline** pobiera dodatkowy kontekst z **Qdrant** (jeśli potrzebny).
5.  Wygenerowane **Meta-Refleksje** są:
    *   Zapisywane w raporcie.
    *   Wysyłane do **RAE** (przez RAE Client) w celu "nauczenia" agenta na przyszłość.
6.  Raport końcowy (`FeniksReport`) jest zwracany do użytkownika.

### Scenariusz: Legacy Behavior Guard

1.  **CLI** otrzymuje żądanie nagrania zachowania scenariusza (`behavior record`).
2.  **Scenario Runner** wykonuje scenariusz:
    *   UI: Playwright/Puppeteer (navigacja, kliknięcia, formularz)
    *   API: HTTP client (request → response)
    *   CLI: subprocess wrapper (komenda → output + logi)
3.  **BehaviorSnapshot** jest tworzony z obserwacji:
    *   ObservedHTTP (status, headers, body)
    *   ObservedDOM (selektory, teksty)
    *   ObservedLogs (linie logów, matched patterns)
4.  Snapshoty są zapisywane do JSONL.
5.  **CLI** otrzymuje żądanie budowy kontraktów (`behavior build-contracts`).
6.  **Contract Builder** analizuje wiele snapshotów:
    *   Wykrywa wspólne cechy (status codes, DOM elements, log patterns)
    *   Usuwa outliery
    *   Tworzy **BehaviorContract** z progami tolerancji
7.  Kontrakty są zapisywane do JSONL.
8.  **CLI** otrzymuje żądanie sprawdzenia zachowania (`behavior check`).
9.  **Behavior Checker** porównuje nowe snapshoty (candidate) z kontraktami:
    *   Tworzy **BehaviorCheckResult** dla każdego scenariusza
    *   Wykrywa **BehaviorViolation** (HTTP status mismatch, DOM element missing, log pattern forbidden)
    *   Oblicza **risk_score** (0.0-1.0)
10. **MaxBehaviorRiskPolicy** ocenia ryzyko:
    *   Pass: risk < 0.5, failed scenarios = 0
    *   Fail: risk ≥ 0.5 lub failed scenarios > 0
11. **BehaviorChecksSummary** jest dodawany do **FeniksReport**.
12. Raport końcowy zawiera:
    *   behavior_checks_summary (pass/fail counts, max risk)
    *   behavior_violations (lista naruszeń kontraktów)
    *   recommendations (merge / fix / rollback)

---

## 4. Stos Technologiczny

*   **Język**: Python 3.10+
*   **Web Framework**: FastAPI, Uvicorn
*   **Validation**: Pydantic V2
*   **Vector DB**: Qdrant
*   **HTTP Client**: Requests / Httpx
*   **Testy**: Pytest, Playwright (E2E)