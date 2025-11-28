# Architektura Systemu Feniks

**Wersja:** 2.1 (Code Aligned)  
**Data:** 28 Listopada 2025

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
|  | MetaReflection |    |    Analysis     |    |  Refactor  |  |
|  |    Engine      |    |    Pipeline     |    |   Engine   |  |
|  +-------+--------+    +--------+--------+    +-----+------+  |
|          |                      |                   |         |
|          +-----------+----------+-------------------+         |
|                      |                                        |
|              +-------v-------+                                |
|              | Domain Models |                                |
|              +---------------+                                |
|                      ^                                        |
|              +-------+-------+                                |
|              |   Policies    |                                |
|              |    Manager    |                                |
|              +---------------+                                |
+---------------------------------------------------------------+
          ^                  ^                     ^
          |                  |                     |
+---------|------------------|---------------------|------------+
|         |                  |                     |            |
|  +------+------+    +------+------+    +---------+---------+  |
|  |   Storage   |    |  RAE Client |    |     Ingest        |  |
|  |   (Qdrant)  |    |   Adapter   |    |    (Loaders)      |  |
|  +-------------+    +-------------+    +-------------------+  |
|                                                               |
|                   ADAPTERS (Infrastruktura)                   |
+---------------------------------------------------------------+
```

---

## 2. Opis Modułów

### 2.1. Core (`feniks/core`)
Serce systemu.

*   **Models (`core/models`)**: Definicje obiektów domeny (Pydantic).
*   **Reflection (`core/reflection`)**: 
    *   `MetaReflectionEngine`: Silnik meta-refleksji generujący insights.
    *   `SystemModel`: Reprezentacja grafowa systemu.
*   **Evaluation (`core/evaluation`)**: 
    *   `AnalysisPipeline`: Koordynuje proces ładowania chunków, budowy modelu i generowania raportów.
    *   `ReportGenerator`: Tworzy raporty końcowe.
*   **Refactor (`core/refactor`)**: 
    *   Silnik refaktoryzacji oparty na "przepisach" (`recipes`).
    *   Obsługuje migrację AngularJS (`ScopeToHooks`, `ControllerToComponent` itp.).
*   **Policies (`core/policies`)**: `PolicyManager` zarządzający regułami kosztowymi i jakościowymi.
*   **Behavior (`core/behavior`)**: (Legacy Behavior Guard)
    *   `BehaviorScenario`: Definicje scenariuszy.
    *   `ComparisonEngine`: Silnik porównujący snapshoty zachowań.

### 2.2. Adapters (`feniks/adapters`)
Warstwa odpowiedzialna za komunikację ze światem zewnętrznym.

*   **Storage (`adapters/storage`)**: Obsługa Qdrant.
*   **Ingest (`adapters/ingest`)**: 
    *   `JSONLLoader`: Ładowanie danych z plików JSONL.
    *   `Filters`: Filtrowanie chunków.
*   **RAE Client (`adapters/rae_client`)**: Klient integracji z agentami RAE.
*   **LLM (`adapters/llm`)**: Obsługa embeddingów i generowania tekstu.

### 2.3. Apps (`feniks/apps`)
Punkty wejścia.

*   **CLI (`apps/cli`)**: Główne narzędzie operacyjne.
*   **API (`apps/api`)**: Serwer REST (FastAPI).
*   **Workers (`apps/workers`)**: Tło przetwarzania asynchronicznego.

### 2.4. Cross-Cutting Concerns
*   **Infra (`feniks/infra`)**: Logging, Tracing (OpenTelemetry), Metrics (Prometheus).
*   **Security (`feniks/security`)**: Uwierzytelnianie (Auth) i autoryzacja (RBAC).
*   **Plugins (`feniks/plugins`)**: Rozszerzenia językowe (np. JavaScript).

---

## 3. Przepływ Danych: Analiza i Refaktoryzacja

1.  **Ingest**: Adaptery ładują kod do bazy wektorowej (Qdrant).
2.  **Analysis**: `AnalysisPipeline` buduje `SystemModel` i uruchamia `MetaReflectionEngine`.
3.  **Refactor Plan**: Na podstawie modelu, `RefactorRecipe` (np. `ControllerToComponent`) generuje plan zmian.
4.  **Execution**: Silnik refaktoryzacji aplikuje zmiany (generuje nowe pliki React).
5.  **Verification**: Testy Behavior Guard weryfikują zgodność zachowań przed i po zmianie.

---

## 4. Stos Technologiczny

*   **Język**: Python 3.10+
*   **Web Framework**: FastAPI
*   **Vector DB**: Qdrant
*   **Frontend Generowany**: React, Next.js (via recipes)
*   **Testy**: Pytest, Playwright
