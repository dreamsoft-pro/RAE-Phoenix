# File: docs/02-01-BEHAVIOR_CONTRACT_MODELS.md

# MODELE DANYCH: BehaviorScenario & BehaviorContract  
**Status:** Draft → do wdrożenia w `feniks/core/models`  
**Powiązanie:** Feniks + RAE (Meta-Refleksja nad systemami legacy bez testów)

---

## 1. Cel modeli

Modele `BehaviorScenario` i `BehaviorContract` służą do formalnego opisania **zachowania istniejącego systemu legacy**, tak by mogło ono pełnić rolę:

- **zastępczych testów regresyjnych** (kiedy nie ma unit/integration testów),
- **kontraktów zachowania** między starą a nową wersją systemu (np. AngularJS → Next.js, Python → Python),
- **źródła prawdy** dla Feniksa przy ocenie ryzyka refaktoryzacji.

Feniks nie tylko analizuje kod, ale również porównuje **behavior przed i po zmianach**, zapisując wynik w `FeniksReport` i pętlach refleksji.  

---

## 2. Główne pojęcia

- **BehaviorScenario** – opis *scenariusza użytkownika* lub *przebiegu technicznego* (np. wywołanie API, pipeline CLI) wraz z wejściami i oczekiwanymi efektami.
- **BehaviorSnapshot** – konkretna, zmierzona instancja wykonania scenariusza (logi, odpowiedzi, DOM, statusy).
- **BehaviorContract** – uogólniony kontrakt zachowania wynikający z wielu snapshotów (co *musi* pozostać zgodne po refaktorze).
- **BehaviorCheckResult** – wynik porównania nowego snapshotu ze znanym kontraktem (pass/fail, poziom ryzyka, lista naruszeń).

---

## 3. Model: `BehaviorScenario`

### 3.1. Opis

`BehaviorScenario` opisuje **co** użytkownik/klient robi w systemie legacy oraz **jakiego rodzaju wynik** jest ważny z punktu widzenia zachowania. To najmniejsza jednostka, na której można budować kontrakty.

### 3.2. Pola (Pydantic / core/models)

Propozycja definicji (w warstwie `feniks/core/models/behavior.py`):

```python
class BehaviorScenario(BaseModel):
    """
    Opis scenariusza zachowania systemu legacy (flow użytkownika lub ścieżka API/CLI).
    """
    id: str
    project_id: str

    # Kategoria i typ scenariusza
    category: Literal["ui", "api", "cli", "batch", "mixed"]
    name: str
    description: str

    # Kontekst środowiska
    environment: Literal["legacy", "candidate", "production", "staging", "test"]
    tags: list[str] = []

    # Wejście do scenariusza
    # Dla UI: ścieżka URL, sekwencja akcji użytkownika
    # Dla API: request (method, path, body, headers)
    # Dla CLI: komenda, argumenty, env
    input: "BehaviorInput"

    # Oczekiwane kryteria sukcesu
    # Np. brak wyjątków, HTTP 200, obecność tekstu w DOM, brak error logów
    success_criteria: "BehaviorSuccessCriteria"

    # Metadane audytowe
    created_at: datetime
    created_by: str | None = None  # user/agent id
3.3. Powiązane modele wejścia i kryteriów
3.3.1. BehaviorInput
python
Skopiuj kod
class UIAction(BaseModel):
    """
    Pojedyncza akcja użytkownika w scenariuszu UI.
    """
    action_type: Literal["click", "type", "navigate", "select", "wait"]
    selector: str | None = None      # CSS/XPath
    text: str | None = None          # np. wpisywany tekst
    url: str | None = None           # dla navigate
    extra: dict[str, Any] = {}       # elastyczne pole na rozszerzenia


class APIRequest(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    url: str
    headers: dict[str, str] = {}
    body: dict[str, Any] | str | None = None


class CLICommand(BaseModel):
    command: str          # np. "python"
    args: list[str] = []  # np. ["main.py", "--config", "config.yml"]
    env: dict[str, str] = {}


class BehaviorInput(BaseModel):
    """
    Wejście scenariusza – w zależności od kategorii używane są odpowiednie pola.
    """
    ui_actions: list[UIAction] | None = None
    api_request: APIRequest | None = None
    cli_command: CLICommand | None = None

    # Dodatkowy kontekst – np. user role, feature flags
    context: dict[str, Any] = {}
3.3.2. BehaviorSuccessCriteria
python
Skopiuj kod
class HTTPCriteria(BaseModel):
    expected_status_codes: list[int] = [200]
    allowed_status_codes: list[int] = [200, 201, 204]
    forbidden_status_codes: list[int] = [500, 502, 503]

    # Opcjonalnie: oczekiwane fragmenty JSON/body
    must_contain_json_paths: list[str] = []     # np. "$.data.id"
    must_not_contain_json_paths: list[str] = []


class DOMCriteria(BaseModel):
    required_selectors: list[str] = []          # muszą istnieć w DOM
    forbidden_selectors: list[str] = []         # nie mogą istnieć (np. ".error-banner")
    required_text_snippets: list[str] = []      # np. "Zamówienie zostało zapisane"
    forbidden_text_snippets: list[str] = []


class LogCriteria(BaseModel):
    # np. "ERROR", "Exception", "Traceback" – które nie mogą się pojawić
    forbidden_patterns: list[str] = []
    required_patterns: list[str] = []


class BehaviorSuccessCriteria(BaseModel):
    """
    Kryteria sukcesu scenariusza – wielowarstwowe:
    HTTP, DOM, logi, inne.
    """
    http: HTTPCriteria | None = None
    dom: DOMCriteria | None = None
    logs: LogCriteria | None = None

    # Dodatkowe arbitralne reguły, które mogą być evalowane przez Feniksa/RAE
    custom_rules: list[str] = []
4. Model: BehaviorSnapshot
4.1. Opis
BehaviorSnapshot reprezentuje konkretny przebieg scenariusza (np. kliknięcie przez Playwrighta, wywołanie API, odpalenie CLI), wraz z zarejestrowanym stanem:

request/response,

DOM (UI),

logi,

metryki czasu, błędy itp.

Ze zbioru snapshotów Feniks potrafi wyprowadzić kontrakt (BehaviorContract) oraz wykrywać regresje.

4.2. Pola
python
Skopiuj kod
class BehaviorSnapshot(BaseModel):
    """
    Konkretny przebieg scenariusza BehaviorScenario (jedno wykonanie).
    """
    id: str
    scenario_id: str
    project_id: str

    environment: Literal["legacy", "candidate", "production", "staging", "test"]

    # Surowe dane obserwacyjne
    observed_http: "ObservedHTTP" | None = None
    observed_dom: "ObservedDOM" | None = None
    observed_logs: "ObservedLogs" | None = None

    # Metryki techniczne
    duration_ms: int | None = None
    error_count: int = 0
    warning_count: int = 0

    # Ocena "na gorąco" – czy scenariusz przeszedł wg kryteriów sukcesu
    success: bool
    violations: list["BehaviorViolation"] = []

    created_at: datetime
    recorded_by: str | None = None  # agent/user
4.3. Modele obserwacji
python
Skopiuj kod
class ObservedHTTP(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: str | dict[str, Any] | None = None


class ObservedDOM(BaseModel):
    # Minimalny snapshot – bez konieczności przechowywania całego HTML
    present_selectors: list[str] = []
    missing_selectors: list[str] = []
    present_text_snippets: list[str] = []
    missing_text_snippets: list[str] = []


class ObservedLogs(BaseModel):
    lines: list[str] = []
    matched_forbidden_patterns: list[str] = []
    matched_required_patterns: list[str] = []
5. Model: BehaviorContract
5.1. Opis
BehaviorContract jest uogólnioną, stabilną regułą zachowania, wyprowadzoną z wielu snapshotów scenariusza.
Kontrakt mówi: “Jeżeli wykonamy scenariusz X, system powinien zachować się w granicach Y”.

Kontrakt:

powstaje przez analizę wielu snapshotów,

może zawierać progi tolerancji (np. dopuszczalne statusy, zakresy czasów),

jest używany przez Legacy Behavior Guard do oceny regresji.

5.2. Pola
python
Skopiuj kod
class BehaviorContract(BaseModel):
    """
    Kontrakt zachowania dla scenariusza – wypadkowa obserwacji wielu snapshotów.
    """
    id: str
    scenario_id: str
    project_id: str

    # Zakres obowiązywania kontraktu
    version: str | None = None               # np. "1.0.0"
    environment_scope: list[
        Literal["legacy", "candidate", "production", "staging", "test"]
    ] = ["legacy", "candidate"]

    # Uogólnione reguły zachowania
    http_contract: "HTTPContract" | None = None
    dom_contract: "DOMContract" | None = None
    log_contract: "LogContract" | None = None

    # Progi tolerancji i ryzyka
    max_error_rate: float | None = 0.0       # dopuszczalny odsetek błędnych snapshotów
    max_duration_ms_p95: int | None = None   # oczekiwany czas dla 95 percentyla

    # Metadane
    derived_from_snapshot_ids: list[str] = []
    created_at: datetime
    created_by: str | None = None
5.3. Kontrakty HTTP/DOM/LOG
python
Skopiuj kod
class HTTPContract(BaseModel):
    """
    Uogólniony kontrakt HTTP (statusy, struktura odpowiedzi).
    """
    required_status_codes: list[int] = [200]
    allowed_status_codes: list[int] = [200, 201, 204]
    forbidden_status_codes: list[int] = [500, 502, 503]

    # Wzorce JSON (np. JSONPath, prosty subset)
    required_json_paths: list[str] = []
    forbidden_json_paths: list[str] = []


class DOMContract(BaseModel):
    """
    Uogólniony kontrakt DOM – minimalny zestaw elementów widoczny dla użytkownika.
    """
    must_have_selectors: list[str] = []
    must_not_have_selectors: list[str] = []
    must_have_text_snippets: list[str] = []
    must_not_have_text_snippets: list[str] = []


class LogContract(BaseModel):
    """
    Kontrakt logowy – czego absolutnie nie chcemy widzieć po refaktorze.
    """
    forbidden_patterns: list[str] = ["Exception", "Traceback", "ERROR"]
    required_patterns: list[str] = []  # np. "Request handled successfully"
6. Model: BehaviorCheckResult i BehaviorViolation
6.1. Opis
BehaviorCheckResult jest wynikiem porównania:

nowego BehaviorSnapshot

z istniejącym BehaviorContract.

Wynik trafia do FeniksReport / pętli refleksji jako element oceny ryzyka refaktoryzacji.

6.2. Pola
python
Skopiuj kod
class BehaviorViolation(BaseModel):
    """
    Konkretny punkt, w którym zachowanie odstaje od kontraktu.
    """
    code: str                      # np. "HTTP_STATUS_MISMATCH", "DOM_ELEMENT_MISSING"
    message: str                   # opis naruszenia
    severity: Literal["low", "medium", "high", "critical"]
    details: dict[str, Any] = {}


class BehaviorCheckResult(BaseModel):
    """
    Wynik porównania snapshotu z kontraktem.
    """
    snapshot_id: str
    contract_id: str
    project_id: str

    passed: bool
    violations: list[BehaviorViolation] = []

    # Zsyntetyzowany poziom ryzyka:
    # - 0.0–0.3: low, 0.3–0.7: medium, 0.7–1.0: high/critical
    risk_score: float

    checked_at: datetime
    checked_by: str | None = None  # agent/user id
7. Integracja z istniejącymi modelami Feniksa
7.1. Powiązanie z FeniksReport
Do FeniksReport (już istniejącego modelu) dodajemy pola:

behavior_checks_summary: BehaviorChecksSummary | None

behavior_violations: list[BehaviorViolation]

Propozycja pomocniczego modelu:

python
Skopiuj kod
class BehaviorChecksSummary(BaseModel):
    total_scenarios_checked: int
    total_snapshots_checked: int
    total_passed: int
    total_failed: int
    max_risk_score: float
Te pola będą używane w:

pętli post-mortem (ocena pojedynczego refaktoru),

pętli longitudinal (trend jakości zachowania systemu w czasie),

politykach (np. “nie akceptuj merge’a, jeśli max_risk_score > 0.5”).

8. Przechowywanie i indeksowanie
8.1. Postgres
Tabele:

behavior_scenarios

behavior_snapshots

behavior_contracts

behavior_check_results

Każda tabela odwzorowuje odpowiedni model Pydantic → ORM.

8.2. Qdrant (opcjonalnie)
Wybrane elementy kontraktów i scenariuszy mogą być przechowywane jako wektory, np.:

embedding nazwy/opisu scenariusza,

embedding logów/DOM do wyszukiwania podobnych scenariuszy.

Umożliwia to:

znajdowanie podobnych scenariuszy legacy,

przenoszenie kontraktów między projektami.

9. Podsumowanie
Modele:

BehaviorScenario

BehaviorSnapshot

BehaviorContract

BehaviorCheckResult

BehaviorViolation

tworzą wspólnie język opisu zachowania systemów legacy, który Feniks może:

analizować,

porównywać,

wykorzystać jako “parasol bezpieczeństwa” nad refaktoryzacją bez klasycznych testów.

Ten plik powinien zostać zaimplementowany w feniks/core/models/behavior.py i uwzględniony w dokumentacji:

ARCHITECTURE.md

LEGACY_BEHAVIOR_GUARD.md (osobny plik, opisujący warstwę ochronną).

yaml
Skopiuj kod

---

```markdown
# File: docs/LEGACY_BEHAVIOR_GUARD.md

# LEGACY_BEHAVIOR_GUARD  
**Jak z Feniksa zrobić parasol bezpieczeństwa nad refaktoryzacją bez testów**

**Status:** Design → do implementacji  
**Powiązanie:** Feniks + RAE, systemy legacy (AngularJS, Python, inne)

---

## 1. Problem, który rozwiązujemy

W praktyce:

- Istnieje duży system legacy (AngularJS, stary backend w Pythonie, itp.).
- System **działa od lat**, ale:
  - nie ma testów (lub są szczątkowe),
  - kod jest złożony i pełen długu technicznego,
  - każda większa zmiana grozi regresją w miejscach, o których wszyscy zapomnieli.

Refaktoryzacja/migracja (np. AngularJS → Next.js, Python → Python 3.x + typy) jest:

- **konieczna** (utrzymanie, wydajność, bezpieczeństwo),
- ale **ryzykowna**, bo brakuje klasycznych testów regresyjnych.

**Legacy Behavior Guard** to warstwa Feniksa, której celem jest:

> *Zbudować „parasolkę bezpieczeństwa” nad refaktoryzacją systemów legacy bez testów, wykorzystując rzeczywiste zachowanie systemu (logi, ścieżki użytkowników, snapshoty odpowiedzi) jako substytut testów.*

---

## 2. Idea wysokopoziomowa

### 2.1. Zasada działania

1. **Obserwujemy istniejący system legacy**, podczas typowych scenariuszy użytkownika / API / CLI.
2. Z obserwacji budujemy:
   - `BehaviorScenario` – opis scenariusza,
   - `BehaviorSnapshot` – konkretne przebiegi,
   - `BehaviorContract` – uogólniony kontrakt zachowania.
3. Po refaktoryzacji (nowa wersja systemu) uruchamiamy te same scenariusze:
   - zbieramy nowe snapshoty,
   - porównujemy je z kontraktami.
4. Feniks generuje:
   - `BehaviorCheckResult`,
   - raport z naruszeniami,
   - syntetyczny `risk_score` refaktoru,
   - rekomendacje (merge / popraw / rollback).

**Kluczowa myśl:**  
> Nie potrzebujemy pełnego pokrycia testami, żeby inteligentnie wychwycić najgroźniejsze regresje.

---

## 3. Rola Feniksa w architekturze

Legacy Behavior Guard wpasowuje się w istniejącą architekturę Feniksa:

- **Core / Models** – implementacja modeli:
  - `BehaviorScenario`, `BehaviorSnapshot`, `BehaviorContract`, `BehaviorCheckResult`, `BehaviorViolation`.  
- **Core / Reflection** – analiza behavior:
  - nowe moduły: `behavior_post_mortem.py`, `behavior_longitudinal.py`.
- **Core / Policies** – polityki dopuszczalnego ryzyka:
  - np. `MaxBehaviorRiskPolicy`.
- **Adapters / Workers** – wykonanie scenariuszy i zbieranie snapshotów:
  - integracje z Playwright/Puppeteer (UI),
  - prosty runner HTTP/CLI (API, batch).
- **Apps / CLI & API** – komendy:
  - `feniks behavior record`,
  - `feniks behavior build-contracts`,
  - `feniks behavior check`.

Feniks pozostaje “mózgiem meta-refleksji” – Behavior Guard jest dodatkową pętlą nastawioną na *zachowanie całego systemu*, a nie tylko kod.

---

## 4. Modele danych (skrót)

Szczegółowa specyfikacja modeli jest w `02-01-BEHAVIOR_CONTRACT_MODELS.md`.  
Poniżej skrót używany w tym dokumencie:

- **BehaviorScenario** – opis scenariusza (UI/API/CLI).
- **BehaviorSnapshot** – pojedynczy przebieg scenariusza (zebrane logi, HTTP, DOM).
- **BehaviorContract** – uogólniony kontrakt z wielu snapshotów.
- **BehaviorCheckResult** – wynik porównania nowego snapshotu z kontraktem.
- **BehaviorViolation** – pojedyncze naruszenie kontraktu.

---

## 5. Data Flow – krok po kroku

### 5.1. Faza 1 – Rejestracja scenariuszy legacy

**Cel:** Złapać reprezentatywne zachowania działającego systemu legacy.

1. Właściciel systemu (lub agent AI) wybiera:
   - najważniejsze flow biznesowe (np. “złóż zamówienie”, “wystaw fakturę”),
   - krytyczne endpointy API (np. `/api/orders`, `/api/invoices`),
   - typowe zadania batch/CLI (np. `python recalc_stats.py`).

2. Dla każdego flow tworzymy `BehaviorScenario`:
   - `category`: `"ui"`, `"api"`, `"cli"`, `"batch"` lub `"mixed"`,
   - `input`: sekwencja akcji użytkownika / request API / komenda CLI,
   - `success_criteria`: minimalny zestaw warunków “musi działać” (statusy, elementy DOM, brak błędów w logach).

3. Scenariusze zapisujemy w Postgres (i opcjonalnie indeksujemy wektorowo).

CLI (propozycja):

```bash
feniks behavior define-scenario \
  --project-id my_legacy_app \
  --from-file docs/scenarios/order_create.yaml
5.2. Faza 2 – Zbieranie snapshotów legacy
Cel: Zebrać realne wykonania scenariuszy w środowisku legacy.

Runner (np. Playwright, HTTP client, wrapper na CLI) uruchamia scenariusze na starej wersji systemu (AngularJS, stary backend itp.).

Zbiera:

odpowiedzi HTTP,

fragmenty DOM (np. obecność kluczowych selektorów/tekstów),

logi aplikacji/serwera.

Tworzy BehaviorSnapshot, oznaczając:

environment = "legacy",

success = True/False (wg BehaviorSuccessCriteria),

ewentualne BehaviorViolation (legacy też może mieć błędy).

CLI:

bash
Skopiuj kod
feniks behavior record \
  --project-id my_legacy_app \
  --scenario-id order_create \
  --environment legacy \
  --output data/behavior_legacy.jsonl
5.3. Faza 3 – Budowa kontraktów
Cel: Wyprowadzić stabilne kontrakty zachowania z wielu snapshotów.

Feniks analizuje zebrane snapshoty:

usuwa outliery (np. jednorazowe błędy sieci),

szuka wspólnych cech:

zakres dopuszczalnych statusów HTTP,

minimalny zestaw elementów DOM,

wzorce logów.

Tworzy BehaviorContract dla każdego scenariusza:

required_status_codes, must_have_selectors, forbidden_patterns itd.,

progi tolerancji (max_error_rate, max_duration_ms_p95).

Zapisuje kontrakty w Postgres, z referencją do snapshotów, z których powstały.

CLI:

bash
Skopiuj kod
feniks behavior build-contracts \
  --project-id my_legacy_app \
  --input data/behavior_legacy.jsonl \
  --output data/behavior_contracts.jsonl
5.4. Faza 4 – Sprawdzanie nowej wersji (candidate)
Cel: Odpalić te same scenariusze na nowej wersji systemu (candidate) i ocenić ryzyko.

Runner odpala scenariusze na nowej wersji:

environment = "candidate" (Next.js, nowy backend, zrefaktoryzowany Python).

Generuje nowe BehaviorSnapshot (candidate).

Feniks dla każdego snapshotu:

wyszukuje właściwy BehaviorContract,

porównuje snapshot z kontraktem,

tworzy BehaviorCheckResult.

CLI:

bash
Skopiuj kod
feniks behavior check \
  --project-id my_legacy_app \
  --environment candidate \
  --contracts data/behavior_contracts.jsonl \
  --snapshots data/behavior_candidate.jsonl \
  --output data/behavior_check_results.jsonl
5.5. Faza 5 – Raport i decyzje
Cel: Na bazie wyników behavior checks podjąć decyzję o merge/rollback/poprawkach.

Feniks agreguje BehaviorCheckResult:

liczy ile scenariuszy:

przeszło bez naruszeń,

przeszło z drobnymi naruszeniami,

nie przeszło (poważne regresje).

wylicza risk_score (globalny).

Tworzy rozszerzony FeniksReport, zawierający:

behavior_checks_summary (ile pass/fail, max risk),

listę behavior_violations,

rekomendację:

✅ “ryzyko niskie – można merge’ować”

⚠️ “ryzyko średnie – zalecane ręczne testy modułów X”

❌ “ryzyko wysokie – nie merge’uj, popraw scenariusze Y, Z”

Raport może być:

wyświetlony w CLI,

zwrócony przez API,

zapisany jako artefakt CI (GitHub Actions / GitLab CI).

6. Polityki i guardrails
6.1. Przykładowa polityka: MaxBehaviorRiskPolicy
Polityka, która nie pozwala na uznanie refaktoru za “bezpieczny”, jeśli:

max_risk_score > 0.5 lub

ilość failed scenarios > N.

Pseudokod (Core / Policies):

python
Skopiuj kod
class MaxBehaviorRiskPolicy(Policy):
    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        summary = report.behavior_checks_summary
        if not summary:
            return PolicyEvaluationResult(
                passed=False,
                reason="No behavior checks were executed."
            )

        if summary.max_risk_score > 0.5:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"Max behavior risk score {summary.max_risk_score} exceeds 0.5"
            )

        if summary.total_failed > 0:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"{summary.total_failed} scenarios failed behavior checks."
            )

        return PolicyEvaluationResult(passed=True, reason="Behavior risk within limits.")
7. Scenariusze użycia (use cases)
7.1. AngularJS → Next.js (UI-heavy)
Legacy: stara aplikacja AngularJS, bez testów, złożony DOM, dużo routingów.

Cel: przepisać interfejs do Next.js, zachowując:

kluczowe ścieżki,

zachowanie formularzy,

komunikację z backendem.

Z Legacy Behavior Guard:

Nagrywasz scenariusze UI (Playwright).

Generujesz snapshoty i kontrakty.

Po przeniesieniu fragmentu do Next.js:

odpalasz te same scenariusze na nowym froncie,

patrzysz na raport Feniksa:

czy brakuje kluczowych elementów,

czy API odpowiada tak samo,

czy nie pojawiły się nowe błędy w logach.

7.2. Python → Python (refaktor backendu)
Legacy: monolit w Pythonie, brak testów, rozbudowany kod biznesowy.

Cel: refaktor (np. dodanie typów, wydzielenie modułów, poprawa architektury).

Z Legacy Behavior Guard:

Definiujesz scenariusze CLI/API:

typowe wywołania (np. “przelicz statystyki”, “wygeneruj raport”).

Zbierasz snapshoty legacy (wejście → wyjście + logi).

Refaktorujesz kod (ręcznie lub częściowo automatycznie).

Odpalasz te same scenariusze na nowym kodzie:

porównujesz strukturę odpowiedzi,

porównujesz logi,

Feniks raportuje behavior risk.

8. Integracja z CI/CD
8.1. Pipeline (GitHub Actions – przykład)
Krok: build & test (to co już masz).

Krok: behavior-check (przy refaktorach legacy):

Odpalenie scenariuszy na environment candidate.

Zebranie nowych BehaviorSnapshot.

Uruchomienie feniks behavior check.

Fail joba, jeśli polityki bezpieczeństwa nie przejdą.

Artefakty:

behavior_candidate.jsonl

behavior_check_results.jsonl

feniks_behavior_report.md

9. Fazy wdrożenia Legacy Behavior Guard
Faza 1 – Minimal Viable Guard
Implementacja modeli (BehaviorScenario, Snapshot, Contract, CheckResult).

Proste CLI:

behavior record,

behavior build-contracts,

behavior check.

Integracja z FeniksReport (bez zaawansowanych polityk).

Faza 2 – Deep Integration
Pełne wpięcie w pętle refleksji:

post-mortem (jednorazowy refaktor),

longitudinal (trend jakości behavior w czasie).

Polityki MaxBehaviorRiskPolicy + parametryzacja progów.

Wsparcie dla AngularJS / Next.js (UI runner) i prostego HTTP runnera.

Faza 3 – Enterprise Ready
Integracja z:

Playwright / Puppeteer (UI),

systemami logowania (ELK, Loki, Datadog),

dashboardami (Grafana).

Możliwość wersjonowania BehaviorContract (v1, v2…).

Biblioteka scenariuszy współdzielonych (np. dla typowych wzorców systemów).

10. Podsumowanie
Legacy Behavior Guard:

nie zastępuje testów,

ale daje realny, operacyjny parasol bezpieczeństwa nad refaktoryzacją systemów legacy,

integruje:

realne zachowanie systemu (snapshoty),

kontrakty zachowania (BehaviorContract),

polityki ryzyka (MaxBehaviorRiskPolicy),

raporty Feniksa.