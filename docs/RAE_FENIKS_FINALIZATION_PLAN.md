#docs/RAE_FENIKS_FINALIZATION_PLAN.md
Zawiera:

pełny plan domknięcia projektu,

checklistę CI/CD,

testy,

release,

cleanup nieużywanych katalogów,

audyt folderów i „śmieci”,

etapy finalnej stabilizacji.

RAE-Feniks: Plan Finalizacji Projektu (v1.0 Release Readiness)
Cel dokumentu
Celem jest domknięcie wszystkich technicznych, organizacyjnych i jakościowych aspektów projektu RAE-Feniks, aby przygotować pierwsze publiczne wydanie:

RAE-Feniks v1.0 – Production-Ready Release

Dokument opisuje:

Audyt struktury repozytorium

Usunięcie nieużywanych katalogów i plików

Wprowadzenie pełnego GitHub Actions CI

Konwencję wersjonowania i pierwszy release

Wzmocnienie DX (Developer Experience)

Testy e2e, integracyjne i smoke

Checklistę „OSS-readiness”

Finalny proces publikacji i weryfikacji

1. Audyt repozytorium i czyszczenie folderów
1.1 Foldery wymagające potwierdzenia lub usunięcia
Przeprowadzić przegląd następujących elementów repozytorium (z automatu lub ręcznie):

Katalogi podejrzane / potencjalnie nieużywane
old/, legacy/, backup/, tmp/, temp/, drafts/, notes/

generowane automatycznie pliki .pyc, .pytest_cache/, .coverage, dist/, build/

katalogi eksperymentalne:

scripts/experimental/

scratch/

draft_recipes/

katalogi z duplikatami starych przepływów (np. old_ingest/, old_indexer/)

Katalogi do potwierdzenia celu
examples/ — czy wszystkie przykłady są potrzebne?
zachować tylko te, które służą dokumentacji

docs/ — upewnić się, że nie zawiera starych wersji planów (plan_v2_old.md, iteration_4_old.md)

refactor/recipes/ — sprawdzić, czy wszystkie przepisy są kompletne

Pliki potencjalnie zbędne
TODO.txt, notes.md, ideas.md

wyeksportowane logi LLM (claude_output.txt, gemini_notes.md)

tymczasowe pliki JSON wygenerowane przez narzędzia (np. *.jsonl w root repo)

1.2 Proces czyszczenia
A. Automatyczna detekcja nieużywanych plików
Użyć skryptu:

lua
Skopiuj kod
find . -type f -name "*.py" -print0 | xargs -0 grep -L "import feniks"
Do wykrycia:

plików .py nieimportowanych nigdzie w projekcie

przestarzałych modułów po refaktoryzacji

B. Detekcja nieużywanych katalogów
Skrypt Python:

python
Skopiuj kod
from pathlib import Path

root = Path(".")
for p in root.iterdir():
    if p.is_dir():
        has_py = any(p.glob("*.py"))
        has_md = any(p.glob("*.md"))
        if not has_py and not has_md:
            print("[EMPTY DIR?]", p)
C. Ostateczna kontrola
Usunąć katalogi:

puste

nieużywane

pozostawione po refaktoryzacjach

generowane, ale niewymagane (np. /output/ → dodać do .gitignore)

2. Wprowadzenie GitHub Actions (CI/CD)
2.1 Minimalne workflow ci.yml
Umieścić w:

bash
Skopiuj kod
.github/workflows/ci.yml
Zawiera:

✔ Matrix Python 3.10–3.12
✔ Instalacja pakietu z [dev]
✔ ruff (lint)
✔ mypy (typing)
✔ pytest --cov
✔ Artefakt raportu coverage
✔ Badge w README „Build: passing"
Pełny workflow (przykład):
yaml
Skopiuj kod
name: RAE-Feniks CI

on:
  push:
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.10", "3.11", "3.12" ]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install .[dev]

      - name: Lint (ruff)
        run: ruff check feniks

      - name: Type check (mypy)
        run: mypy feniks

      - name: Test (pytest)
        run: pytest --cov=feniks --cov-report=xml

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
3. Testy wymagane przed wydaniem v1.0
3.1 Testy jednostkowe
wszystkie moduły z core/

ingest/

embedding/

store/qdrant.py

pluginy językowe

3.2 Testy E2E
W katalogu:

bash
Skopiuj kod
tests/e2e/
Scenariusz:

javascript
Skopiuj kod
node_indexer → JSONL → feniks ingest → feniks analyze
3.3 Test integracji z RAE
mock RAE lub docker-compose (opcjonalnie)

test:

feniks generuje meta-refleksję

wysyła ją do RAE

RAE udostępnia ją w /system/describe_self

4. Release Process (v1.0)
4.1 SemVer
Ustawić wersję w:

pyproject.toml

feniks/__init__.py

dokumentacji

Format:

Skopiuj kod
v1.0.0
4.2 CHANGELOG.md
Stworzyć:

markdown
Skopiuj kod
## 1.0.0 – Initial Production Release

### Added
- Ingest pipeline
- System Model Builder
- Capability Detector
- Meta-Reflection Engine
- Refactoring Workflows
- RAE integration
- Security & Governance modules
- Documentation + examples
4.3 Release na GitHub
Utworzyć Release z:

tagiem: v1.0.0

paczką .whl

paczką .tar.gz

krótkim filmikiem / gifem pokazującym feniks analyze

informacją o kompatybilności:

Python 3.10+

Node 18+

Qdrant > 1.7

RAE >= 2.0.0

5. Developer Experience (DX)
5.1 README.md
Powinien zawierać:

diagram architektury

5-minutowy Quickstart:

bash
Skopiuj kod
pip install feniks
docker compose -f docker-compose.qdrant.yml up -d
feniks ingest --project-id demo --source ./examples/angular
feniks analyze --project-id demo
linki do docs

badge:

Build: passing

License: Apache 2.0

Python: 3.10–3.12

6. Checklist „OSS-Readiness”
Dokumentacja
 README.md kompletne

 GETTING_STARTED.md

 ARCHITECTURE.md

 RAE_INTEGRATION.md

 REFLECTIVE_WORKFLOWS.md

Jakość kodu
 ruff → 0 błędów

 mypy → 0 błędów krytycznych

 90%+ pokrycia testami (cel)

 brak dead code

Repo
 brak nieużywanych folderów

 brak szkiców i backupów

 .gitignore kompletny

 workflow ci.yml działa

Release
 wersjonowanie SemVer

 CHANGELOG.md

 v1.0.0 jako pierwszy stabilny release

7. Proces finalnej weryfikacji
7.1 Przed wypchnięciem
pełny pytest lokalnie

ruff check

mypy

feniks ingest na dwóch różnych projektach

feniks analyze

generacja meta-refleksji

wysłanie ich do RAE

7.2 Po wypchnięciu
wszystkie GH Actions muszą przejść na zielono

sprawdzić README pod kątem poprawności linków

sprawdzić stronę Releases na GitHub

8. Finalizacja projektu
Przy spełnieniu wszystkich powyższych punktów:

RAE-Feniks staje się w pełni dojrzałym projektem klasy enterprise, gotowym do użycia w firmach, w pracy agentów AI i w środowiskach produkcyjnych.

Koniec dokumentu.
Gotowe do umieszczenia w repozytorium w docs/RAE_FENIKS_FINALIZATION_PLAN.md.