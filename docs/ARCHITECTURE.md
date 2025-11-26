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

*   **Models (`core/models`)**: Definicje obiektów domeny (`SessionSummary`, `FeniksReport`, `ReasoningTrace`). Są to czyste klasy danych (Pydantic), używane do komunikacji między warstwami.
*   **Reflection (`core/reflection`)**: Silnik meta-refleksji. Zawiera logikę analizy post-mortem, longitudinal i self-model. To tutaj zapadają decyzje o jakości kodu.
*   **Evaluation (`core/evaluation`)**: Pipeline przetwarzania danych. Koordynuje pobieranie danych, analizę i generowanie raportów.
*   **Policies (`core/policies`)**: Strażnicy systemu (Guardrails). Moduł ten zawiera reguły kosztowe i jakościowe, które są egzekwowane na każdym etapie analizy.

### 2.2. Adapters (`feniks/adapters`)
Warstwa odpowiedzialna za komunikację ze światem zewnętrznym. Implementuje interfejsy wymagane przez Core.

*   **Storage (`adapters/storage`)**: Obsługa Qdrant (baza wektorowa). Tłumaczy obiekty domenowe na punkty wektorowe i odwrotnie.
*   **RAE Client (`adapters/rae_client`)**: Klient integrujący się z silnikiem RAE. Wysyła i pobiera pamięć agentów.
*   **LLM (`adapters/llm`)**: Abstrakcja nad modelami językowymi (OpenAI, Gemini, Claude). Obecnie obsługuje głównie generowanie embeddingów.

### 2.3. Apps (`feniks/apps`)
Punkty wejścia do aplikacji. Te moduły "sklejają" system w całość, inicjalizując odpowiednie adaptery i przekazując je do Core.

*   **CLI (`apps/cli`)**: Interfejs wiersza poleceń.
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

---

## 4. Stos Technologiczny

*   **Język**: Python 3.10+
*   **Web Framework**: FastAPI, Uvicorn
*   **Validation**: Pydantic V2
*   **Vector DB**: Qdrant
*   **HTTP Client**: Requests / Httpx
*   **Testy**: Pytest, Playwright (E2E)