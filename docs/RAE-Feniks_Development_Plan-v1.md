# RAE-Feniks – Development Plan (v1.0)

## Cel dokumentu

Celem tego planu jest przekształcenie obecnego projektu **Feniks** w:

> **RAE-Feniks** – silnik analizy kodu, meta-refleksji i refaktoryzacji klasy enterprise,  
> ściśle zintegrowany z **RAE (Reflective Agentic-memory Engine)**.

Docelowo RAE-Feniks ma:

- wykorzystywać istniejące funkcje Feniksa:
  - analizę kodu (AST / indexery),
  - wyciąganie chunków kodu z metadanymi,
  - embeddingi + TF-IDF,
  - Qdrant jako wektorowy magazyn wiedzy o kodzie,
  - pluginy językowe (np. JavaScript / AngularJS),
- dodać **warstwę metarefleksji**:
  - refleksje o stanie kodu, architektury, długu technicznego,
  - meta-refleksje o jakości samych refleksji i procesów refaktoryzacji,
  - self-model systemu (wiedza o własnych zdolnościach i ograniczeniach),
- zaoferować **workflows klasy enterprise do refaktoryzacji**:
  - bezpieczna refaktoryzacja kodu (LLM + AST),
  - kontrola zmian (dry-run, diff, PR),
  - audytowalność i integracja z CI/CD,
  - współpraca z RAE jako centralną warstwą pamięci.

---

## Architektura docelowa – RAE + RAE-Feniks

### RAE (już istniejący komponent)
- Pamięć epizodyczna, semantyczna, refleksyjna.
- GraphRAG + Hybrid Search.
- Multi-tenant, PII scrubber, Cost Controller.
- API + SDK Python.
- Integracje (MCP, langchain, itp.).

### RAE-Feniks (docelowo)
- **Warstwa analizy kodu**:
  - indexery (Node/Babel, AST, JSONL),
  - model `Chunk` + metadane (złożoność, moduł, API, zależności).
- **Warstwa wiedzy o systemie**:
  - graf zdolności (capability graph),
  - mapa modułów, endpointów, zależności.
- **Warstwa metarefleksji**:
  - meta-refleksje o kodzie, architekturze i samym RAE-Feniksie,
  - self-model systemu (co potrafi, czego nie potrafi).
- **Warstwa refaktoryzacji enterprise**:
  - przepisy refaktoryzacyjne (recipes),
  - integracja z LLM (RAE jako pamięć + LLM jako „mózg”),
  - kontrola zmian, audyt, integracja z git/CI.

---

# Iteracja 1 – Stabilizacja i uporządkowanie Feniksa

### Cel
Przekształcić Feniksa z prototypu w stabilny, spójny pakiet Python, gotowy do dalszego rozwoju i integracji z RAE.

### Zakres

1. **Struktura pakietu**
   - Uporządkowanie katalogu `feniks/`:
     - `feniks/core/` – orkiestracja pipeline’ów (ingest, analiza, refaktoryzacja).
     - `feniks/ingest/` – logika importu danych z indexerów (Node, inne).
     - `feniks/plugins/` – pluginy językowe (na start `JavaScriptPlugin`).
     - `feniks/embedding/` – obsługa SentenceTransformers + TF-IDF.
     - `feniks/store/` – Qdrant, ewentualnie inne backendy.
     - `feniks/types.py` – definicje typów domenowych (Chunk, Dependency, ApiEndpoint, GitInfo, itp.).
     - `feniks/config.py` – Settings, ścieżki, konfiguracja modeli i Qdranta.
     - `feniks/logger.py` – centralny logger.
     - `feniks/utils.py` – drobne helpery (np. extract_module_from_path).

2. **Pakietowanie**
   - Dostosować `pyproject.toml` / `setup.cfg` (w zależności od obecnej konfiguracji) tak, by:
     - `pip install -e .` instalował `feniks` jako moduł.
     - entrypoint CLI był jasno zdefiniowany (np. `feniks = feniks.core.cli:main`).

3. **Konfiguracja**
   - Ustandaryzować źródło konfiguracji:
     - `.env` + `pydantic` Settings,
     - environment variables,
     - profil `dev` / `prod`.
   - Konfiguracja Qdranta, ścieżek do Node indexera, modelu embeddingów.

4. **Logowanie i obsługa błędów**
   - Spójny logger (`feniks.logger.get_logger`).
   - Zdefiniowanie własnych wyjątków domenowych:
     - `FeniksConfigError`,
     - `FeniksIngestError`,
     - `FeniksStoreError`,
     - `FeniksPluginError`.

### Kryteria akceptacji

- `pip install -e .` działa lokalnie.
- Komenda `feniks --help` wyświetla pomoc.
- Struktura katalogów jest zgodna z powyższym.
- Logowanie jest spójne i czytelne (poziomy: INFO, WARNING, ERROR, DEBUG).
- Kod przechodzi `ruff` / `flake8` + podstawowe testy.

---

# Iteracja 2 – Unifikacja pipeline’u ingestu kodu

### Cel
Zastąpić eksperymentalne / regexowe ścieżki ingestu jednolitym, stabilnym pipeline’em opartym na Node/Babel indexerze i Qdrant.

### Zakres

1. **Node/Babel indexer jako źródło prawdy**
   - Ustalić, że:
     - indexer JS/HTML (`js_html_indexer.mjs`) generuje **JSONL z `Chunk` + metadane**,
     - Feniks **nie próbuje już od nowa parsować JS** – używa JSONL jako wejścia.
   - Doprecyzować format JSONL (zgodny z `feniks.types.Chunk`):
     - `id`, `file_path`, `start_line`, `end_line`,
     - `module`, `kind` (controller/service/directive/...),
     - `complexity`,
     - `api_calls`, `dependencies`,
     - `git_info` (autor, data, commit),
     - `business_tags`.

2. **Warstwa ingestu po stronie Feniksa**
   - Moduł `feniks.ingest.jsonl_loader`:
     - wczytuje JSONL,
     - waliduje dane (pydantic),
     - normalizuje ścieżki, moduły, metadane.
   - Opcjonalne filtrowanie:
     - ignorowanie plików/vendor/legacy,
     - proste reguły `include/exclude`.

3. **Integracja z Qdrant**
   - Standaryzacja kolekcji:
     - `collections: code_chunks` (domyślna nazwa),
     - wektor gęsty: `dense_code` (SentenceTransformers),
     - wektor rzadki: `sparse_keywords` (TF-IDF),
     - payload: pełne metadane chunków (bez nadmiernego duplikowania tekstu).
   - Upsert punktów z:
     - `id` = stabilny hash (np. sha1(file_path + start_line + end_line + commit_id)),
     - wektory,
     - payload.

4. **CLI**
   - Komenda:
     ```bash
     feniks ingest \
       --project-root /path/to/project \
       --jsonl-path /path/to/indexer_output.jsonl \
       --collection code_chunks
     ```
   - Obsługa błędów (brak JSONL, błędny format, brak Qdranta).

### Kryteria akceptacji

- Można uruchomić:
  1. Node indexer → JSONL,
  2. `feniks ingest` → Qdrant.
- W Qdrant widoczne są:
  - poprawne payloady,
  - poprawne wektory,
  - stałe, powtarzalne ID.
- Przynajmniej 1 test E2E:
  - mały projekt → JSONL → Qdrant → prosty search (`qdrant.search`).

---

# Iteracja 3 – Warstwa wiedzy o systemie (System Model Layer)

### Cel
Na podstawie danych z ingestu zbudować **model wiedzy o systemie**, tj.:

- mapa modułów,
- graf zależności,
- opis endpointów i API,
- wstępny graf zdolności (capability graph).

### Zakres

1. **Model domenowy**
   - Rozszerzenie `feniks.types` o:
     - `Module` (nazwa, ścieżka, typ: frontend/backend/core),
     - `Dependency` (source → target, rodzaj zależności),
     - `ApiEndpoint` (metoda, URL, typy parametrów, powiązane moduły),
     - `Capability` (np. `hybrid_search`, `pii_scrub`, `cost_control`, `labels_imposition` – w kontekście konkretnych projektów).

2. **Budowa grafu systemu**
   - Moduł `feniks.core.system_model_builder`:
     - iteruje po chunkach i zależnościach,
     - tworzy graf:
       - węzły = moduły / serwisy / kontrolery / API,
       - krawędzie = zależności, wywołania, importy.
   - Wyliczanie podstawowych metryk:
     - stopień węzła (in/out),
     - moduły centralne (wysoki degree),
     - potencjalne „god objects”.

3. **Modele zdolności (capabilities)**
   - Na podstawie:
     - patternów w kodzie (np. obecność `$http`, routerów, serwisów),
     - nazw modułów,
     - konfiguracji,
   - generowanie listy pozornych „zdolności” systemu:
     - np. „obsługuje dashboard produkcyjny”, „obsługuje kalkulacje cen”, „obsługuje workflow RAE”.

4. **Output / API wewnętrzne**
   - Funkcje:
     - `build_system_model(project_id) -> SystemModel`
     - `get_capability_graph(project_id) -> CapabilityGraph`
   - Zapis system modelu do:
     - Qdrant (jako osobna kolekcja, np. `system_nodes`),
     - lub do RAE (w kolejnych iteracjach).

### Kryteria akceptacji

- Można:
  - zbudować System Model dla przykładowego projektu,
  - wylistować moduły i ich zależności,
  - wygenerować prosty raport tekstowy:
    - „moduły centralne”,
    - „moduły graniczne”,
    - „potencjalne hotspots do refaktoryzacji”.

---

# Iteracja 4 – Warstwa metarefleksji 1.0 (local-only)

### Cel
Dodać do Feniksa warstwę **metarefleksji** nad kodem (bez integracji z RAE, jeszcze lokalnie):

- refleksje o stanie kodu,
- meta-refleksje o jakości architektury,
- rekomendacje refaktoryzacyjne na poziomie ogólnym.

### Zakres

1. **Model meta-refleksji**
   - Struktura:
     ```json
     {
       "timestamp": "...",
       "project_id": "...",
       "level": 1,
       "origin": "feniks",
       "scope": "codebase" | "module" | "system",
       "content": "System wykazuje wysoki poziom zależności cyklicznych...",
       "evidence": [...],
       "impact": "refactor-recommended" | "monitor" | "informational"
     }
     ```
   - Poziomy:
     - level 0 – czyste obserwacje,
     - level 1 – refleksje (wnioski),
     - level 2 – meta-refleksje (ocena refleksji / procesów).

2. **Silnik metarefleksji**
   - Moduł `feniks.core.meta_reflection_engine`:
     - przyjmuje `SystemModel`, metryki z grafu i Qdranta,
     - generuje metarefleksje wg zestawu reguł + LLM (opcjonalnie):
       - zbyt wysoka złożoność w kluczowych modułach,
       - zbyt duża liczba zależności w jednym kierunku,
       - brak testów w hotspotach,
       - powtarzalne patterns długu technicznego.

3. **Lokalny storage metarefleksji**
   - Na początek: lokalny plik JSONL / SQLite / prosty store.
   - Później: delegacja do RAE (Iteracja 5).

4. **CLI**
   - Komenda:
     ```bash
     feniks analyze \
       --project-id my_project \
       --output meta_reflections.jsonl
     ```
   - Wynik: raport z metarefleksji (np. w formie Markdown + JSONL).

### Kryteria akceptacji

- Można uruchomić:
  - `feniks ingest` (Iteracja 2),
  - `feniks analyze` → otrzymać listę metarefleksji.
- Metarefleksje są:
  - spójne,
  - odwołują się do realnych modułów / problemów,
  - zawierają rekomendacje (ale nie krzyczą „magiczne AI”, tylko rzeczowe wnioski).

---

# Iteracja 5 – Integracja z RAE (Self-Model + Pamięć)

### Cel
Podłączyć Feniksa do RAE jako:

- **konsumenta pamięci (czytanie z RAE)** – w przyszłości,
- **producenta metarefleksji + self-modelu (pisanie do RAE)** – teraz.

### Zakres

1. **Klient RAE**
   - Moduł `feniks.integrations.rae_client`:
     - konfiguracja: `RAE_BASE_URL`, `RAE_API_KEY` / JWT,
     - funkcje:
       - `store_meta_reflection(reflection_payload)`,
       - `store_system_capabilities(system_model)`,
       - `get_memory_for_project(project_id, filters)` (później).

2. **Format danych pod RAE**
   - Metarefleksje Feniksa zapisujemy jako:
     - pamięć **refleksyjna** i/lub **meta-refleksyjna** w RAE,
     - typy:
       - `memory_type = "meta_reflection"`,
       - `domain = "codebase" | "architecture" | "system_model"`.
   - System Model / Capability Graph zapisujemy jako:
     - pamięć semantyczną:
       - „System posiada moduł X…”
       - „System implementuje capability Y…”.

3. **Endpoint Self-Model – `/system/describe_self`**
   - Po stronie RAE:
     - endpoint zbierający informacje z pamięci semantycznej + meta-refleksyjnej,
     - generujący aktualny self-model.
   - RAE-Feniks:
     - jest jednym z głównych dostawców tych danych (kompetencje, granice systemu).

4. **Triggerowanie update’ów**
   - Po skończonej analizie:
     - Feniks:
       - wysyła metarefleksje do RAE,
       - wysyła zaktualizowany system model.
     - RAE:
       - może opublikować event (np. `system_model.updated`).

### Kryteria akceptacji

- Można:
  - uruchomić Feniksa z RAE skonfigurowanym w `.env`,
  - po analizie kodu:
    - sprawdzić w RAE, że pojawiły się nowe wpisy pamięci (meta_reflection + system_model),
  - wywołać `/system/describe_self` i zobaczyć, że:
    - opisuje m.in. zdolności systemu wynikające z Feniksa.

---

# Iteracja 6 – Workflows refaktoryzacji klasy enterprise

### Cel
Dodać do RAE-Feniks **robocze, ale sensowne** narzędzia do refaktoryzacji kodu we współpracy z LLM i RAE, z myślą o bezpieczeństwie, audycie i praktycznym użyciu.

### Zakres

1. **Receptury refaktoryzacyjne (recipes)**
   - Zdefiniować zestaw podstawowych „recept”:
     - `rename_controller`,
     - `split_large_module`,
     - `extract_service_from_controller`,
     - `reduce_cyclomatic_complexity`,
     - `migrate_$http_to_service`,
     - itp.
   - Każda recepta:
     - ma wejście: wskazane moduły / pliki / warunki,
     - ma plan: co zmienić,
     - ma walidację: jak sprawdzić poprawność.

2. **Integracja LLM + AST (bezpieczne modyfikacje)**
   - Współpraca:
     - Feniks pobiera chunk + kontekst z Qdranta,
     - RAE dostarcza pamięć szerszego kontekstu (np. wcześniejsze decyzje refaktoryzacyjne, style, zasady),
     - LLM generuje propozycję zmian,
     - `JavaScriptPlugin` (lub inne pluginy) waliduje / wstrzykuje zmiany na poziomie AST (zamiast „plain string replace”).

3. **Dry-run + diff**
   - Każdy workflow refaktoryzacyjny:
     - generuje patch (diff),
     - zapisuje go jako artefakt (np. w katalogu `output/patches/`),
     - pozwala na:
       - `apply` – zastosowanie,
       - `discard` – odrzucenie.
   - Integracja z git:
     - opcja: `feniks refactor --apply` → tworzy brancha + commit.

4. **Audyt i bezpieczeństwo**
   - Każda operacja:
     - loguje metarefleksję:
       - „Dlaczego ta refaktoryzacja?”,
       - „Jakie ryzyka?”,
       - „Jakie moduły zostały zmienione?”.
   - Możliwość integracji z RAE:
     - przechowywanie historii refaktoryzacji jako pamięci epizodycznej.

### Kryteria akceptacji

- Co najmniej jeden „end-to-end workflow”:
  - projekt AngularJS,
  - Feniks ingest + analyse + zaproponowana refaktoryzacja,
  - wygenerowany patch,
  - możliwość ręcznego review i zastosowania zmian.
- Raport z refaktoryzacji zawiera:
  - metarefleksje,
  - zmienione pliki,
  - potencjalne ryzyka.

---

# Iteracja 7 – Hardening, observability, governance

### Cel
Podnieść RAE-Feniks do poziomu **enterprise** pod względem:

- stabilności,
- obserwowalności,
- bezpieczeństwa,
- przewidywalności kosztów.

### Zakres

1. **Monitoring i metryki**
   - Metryki:
     - liczba analizowanych projektów,
     - czas ingestu,
     - czas analizy,
     - liczba wygenerowanych metarefleksji,
     - liczba wykonanych refaktoryzacji,
     - basic performance stats (czas zapytań do Qdrant, LLM latency).
   - Integracja z:
     - Prometheus / OpenTelemetry (opcjonalnie),
     - prosty dashboard (np. w Grafanie albo w RAE dashboard).

2. **Bezpieczeństwo**
   - Autoryzacja:
     - OAuth2 / JWT,
     - integracja z tym samym IdP co RAE.
   - Autentykacja:
     - API-key + JWT dla serwisów,
     - kontrola ról:
       - `viewer` – tylko odczyt metryk / raportów,
       - `refactorer` – może generować refaktoryzacje,
       - `admin` – konfiguracja, integracje, limity.

3. **Multi-project / multi-tenant**
   - Możliwość pracy równolegle na wielu projektach:
     - `project_id`,
     - osobne kolekcje w Qdrant,
     - osobne wpisy w RAE (tenant/project).
   - Spójność z multi-tenancy w RAE.

4. **Kontrola kosztów**
   - Integracja z CostController z RAE:
     - limitowanie zapytań do LLM,
     - budżety na refaktoryzacje,
     - raporty kosztów per projekt.

### Kryteria akceptacji

- Dla przykładowego projektu:
  - widać metryki (czas, koszty, ilość metarefleksji),
  - można ograniczyć dostęp do refaktoryzacji tylko do wybranych ról,
  - budżet LLM na projekt może być limitowany.

---

# Iteracja 8 – Developer Experience, dokumentacja, przykłady

### Cel
Ułatwić życie użytkownikom RAE-Feniks:

- dobra dokumentacja,
- przykładowe scenariusze,
- quickstarty,
- proste integracje.

### Zakres

1. **Dokumentacja**
   - `docs/`:
     - `OVERVIEW.md` – co to jest RAE-Feniks,
     - `GETTING_STARTED.md` – od zera do pierwszego ingestu + analizy,
     - `REFLECTION_AND_META_REFLECTION.md` – jak działa refleksja i metarefleksja,
     - `ENTERPRISE_REFACTORING.md` – opis workflowów refaktoryzacji,
     - `RAE_INTEGRATION.md` – jak to spiąć z RAE.

2. **Przykłady**
   - `examples/`:
     - `angular_project_demo/`,
     - `run_ingest_and_analyze.sh`,
     - `sample_meta_reflections.md`,
     - `sample_refactor_patch.diff`.

3. **CLI UX**
   - Komendy:
     - `feniks ingest ...`,
     - `feniks analyze ...`,
     - `feniks refactor ...`,
     - `feniks report ...`.
   - Czytelne komunikaty błędów, podpowiedzi.

4. **Materiały pomocnicze**
   - Checklista:
     - jak przygotować projekt do analizy,
     - jak interpretować metarefleksje,
     - jak bezpiecznie wdrażać refaktoryzacje.

### Kryteria akceptacji

- Nowa osoba:
  - jest w stanie uruchomić demo w mniej niż godzinę,
  - rozumie, co robi RAE-Feniks,
  - potrafi zobaczyć metarefleksje i przykładową refaktoryzację.

---

## Podsumowanie

Ten plan zakłada **ewolucję, a nie rewolucję**:

- Iteracje 1–2 robią z Feniksa stabilny silnik ingestu i analizy kodu.
- Iteracja 3 dodaje warstwę „wiedzy o systemie”.
- Iteracja 4 dodaje metarefleksje lokalne.
- Iteracja 5 spina to z RAE i Self-Model.
- Iteracja 6 daje realne, praktyczne workflowy refaktoryzacji.
- Iteracja 7–8 podnoszą RAE-Feniks do poziomu narzędzia klasy enterprise:
  - bezpieczeństwo,
  - kontrola kosztów,
  - metryki,
  - dokumentacja i przykłady.

Docelowo RAE-Feniks staje się:
- meta-rozszerzeniem RAE,
- narzędziem do poznawania, oceniania i refaktoryzowania systemów,
- fundamentem do budowy agentów, którzy znają nie tylko użytkownika, ale **również samych siebie i własny kod**.
