Feniks · Knowledge Base Builder (AngularJS 1.x Frontend)

Feniks buduje bazę wiedzy z kodu frontend (AngularJS 1.x) i szablonów HTML:

chunkuje pliki .js i .html na małe fragmenty z metadanymi (DI, typ AST, zakres linii),

tworzy embeddingi (dense) oraz sparse (TF-IDF),

ładuje wszystko do Qdrant (hybryda dense+sparse; automatyczny fallback do dense-only),

udostępnia CLI do wyszukiwania (PL→EN normalizacja, filtry: --mode, --modules, DI/AST).

Idealne jako kontekst dla agentów AI do refaktoryzacji frontendu.

⚡ TL;DR
# 0) (opcjonalnie) Python venv
python3 -m venv .venv && source .venv/bin/activate

# 1) Zależności
pip install -r requirements.txt

# 2) Qdrant (lokalnie w Dockerze)
docker compose -f docker-compose.qdrant.yml up -d

# 3) Zbuduj bazę wiedzy (przykład ze ścieżką do frontu)
python scripts/build_kb.py index \
  --root /home/grzegorz/cloud/Dockerized/frontend \
  --out  ./ \
  --collection frontend_feniks \
  --host 127.0.0.1 --port 6333 \
  --model intfloat/multilingual-e5-base \
  --reset --write-ignores

# 4) Wyszukaj (PL -> EN, tryb JS)
python scripts/build_kb.py search "refaktoryzuj serwis autentykacji użytkownika" \
  --mode js --alpha 0.8 --topk 12 --modules all


Jeśli Twoja wersja qdrant-client nie obsługuje sparse, Feniks automatycznie przechodzi w dense-only i kończy indeks poprawnie.

Co jest indeksowane

app/src/**/*.js oraz app/src/**/*.html wewnątrz --root.

Pomijane domyślnie (.feniksignore/wbudowane):
node_modules/, bower_components/, dist/, build/, vendor/, .cache/, .git/,
*.min.js, *.map, *.spec.js, *.test.js, *.d.ts.

Jeśli Twój frontend ma inną strukturę niż app/src/..., zmień globy w scripts/build_kb.py (JS_GLOB, HTML_GLOB) lub wskaż inny --root.

Dane wyjściowe

data/chunks.jsonl – każdy wiersz to chunk, np.:

{
  "id": "...sha1",
  "file_path": "app/src/index/services/auth.service.js",
  "module": "index",
  "chunk_name": "fn_3",
  "kind": "js_function | html_section",
  "ast_node_type": "Service | Factory | Controller | Directive | Function | Template",
  "dependencies_di": ["$http", "$q", "SessionService"],
  "anti_patterns": ["direct_dom", "scope_watch"],
  "text": "fragment kodu…",
  "start_line": 120,
  "end_line": 168
}


kb/modules/*.json – karty modułów:

listy services, controllers, factories, directives,

routes (ui-router/ngRoute), templates, files.

Kolekcja Qdrant: frontend_feniks

wektor dense dense_code (COSINE, 768D),

wektor sparse sparse_keywords (jeśli wspierane przez klienta/serwer).

Wyszukiwanie (CLI)
python scripts/build_kb.py search "twoje zapytanie po PL" \
  --mode js|html|any \
  --alpha 0.7..0.9 \
  --topk 10..30 \
  --modules all|mod1,mod2 \
  [--deps $http $q AuthService] \
  [--ast-types Service Controller ...] \
  [--paths-include app/src/] \
  [--no-translate]


PL→EN: domyślnie zapytanie jest tłumaczone na angielski (wyłącz --no-translate).

--mode:

js – boost dla serwisów/kontrolerów (filtry DI/AST, preferuje .js),

html – boost dla szablonów (preferuje .html, ścieżki templates|views|partials),

any – neutralny.

--alpha – miks: alpha*dense + (1-alpha)*keywords + bonusy.
Rekomendacje: 0.8 (JS), 0.7 (HTML).

--modules – filtr po app/src/<module>/... (np. cart,client-zone lub all).

Przykłady:

# JS: refaktoryzacja autentykacji
python scripts/build_kb.py search "refaktoryzuj serwis autentykacji użytkownika" \
  --mode js --alpha 0.8 --topk 12 --modules all

# HTML: walidacja formularza rejestracji w konkretnych modułach
python scripts/build_kb.py search "popraw walidację formularza rejestracji" \
  --mode html --alpha 0.7 --topk 12 --modules cart,client-zone

Backups (snapshots) + jak przywrócić

Qdrant ma wbudowane snapshoty kolekcji – można je tworzyć, listować, pobierać i przywracać przez REST API i przez Web UI (http://localhost:6333/dashboard). 
qdrant.tech
+1

Gdzie Qdrant trzyma dane

W kontenerze: /qdrant/storage

Na hoście (przykład): jeśli używasz wolumenu -v qdrant_storage:/qdrant/storage, to mountpoint zwykle jest w /var/lib/docker/volumes/qdrant_storage/_data.
Alternatywnie możesz montować własną ścieżkę: -v $(pwd)/path/to/data:/qdrant/storage. 
qdrant.tech
GitHub

1) Utwórz snapshot kolekcji
# utworzenie snapshotu dla kolekcji 'frontend_feniks'
curl -X POST "http://127.0.0.1:6333/collections/frontend_feniks/snapshots"
# jeśli masz API key:
# curl -X POST "http://127.0.0.1:6333/collections/frontend_feniks/snapshots" -H "api-key: <KEY>"


Endpoint: POST /collections/{collection_name}/snapshots (zwraca nazwę pliku snapshotu). 
api.qdrant.tech

2) Lista i pobieranie snapshotów
# lista snapshotów
curl "http://127.0.0.1:6333/collections/frontend_feniks/snapshots" | jq

# pobranie wskazanego snapshotu (podmień {SNAPSHOT})
curl -L "http://127.0.0.1:6333/collections/frontend_feniks/snapshots/{SNAPSHOT}" \
  -o backups/frontend_feniks-{SNAPSHOT}


Endpoints:
GET /collections/{collection_name}/snapshots (lista),
GET /collections/{collection_name}/snapshots/{snapshot_name} (pobranie). 
api.qdrant.tech
+1

3) Przywracanie snapshotu (restore)

Masz dwie proste opcje:

(A) Restore z lokalnego pliku (wewnątrz kontenera)

Skopiuj snapshot do kontenera (folder snapshotów Qdrant):

docker cp backups/frontend_feniks-{SNAPSHOT} qdrant:/qdrant/snapshots/


Zgłoś recover z lokalnej ścieżki (koniecznie priority: "snapshot"):

curl -X PUT "http://127.0.0.1:6333/collections/frontend_feniks/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d '{
        "location": "file:///qdrant/snapshots/{SNAPSHOT}",
        "priority": "snapshot"
      }'


Endpoint: PUT /collections/{collection_name}/snapshots/recover
location może być URL albo file:// wewnątrz noda; priority: "snapshot" wymusza odtworzenie danych ze snapshotu. 
api.qdrant.tech
qdrant.tech

(B) Restore z URL (bez kopiowania do kontenera)

Użyj bezpośredniego URL do snapshotu (np. do węzła, z którego go pobrałeś):

curl -X PUT "http://127.0.0.1:6333/collections/frontend_feniks/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d '{
        "location": "http://127.0.0.1:6333/collections/frontend_feniks/snapshots/{SNAPSHOT}",
        "priority": "snapshot"
      }'


Wersja z URL działa, jeśli Qdrant ma dostęp do tego URL (ta sama maszyna/port). 
api.qdrant.tech

Uwaga: jeśli masz włączone API-Key w Qdrant, dodaj nagłówek -H "api-key: <KEY>" również do PUT .../recover. 
api.qdrant.tech

4) Snapshot całego węzła (opcjonalnie)

Poza snapshotami kolekcji istnieją też snapshoty storage całego noda: GET /snapshots, POST /snapshots. W pojedynczym węźle zwykle wystarczą snapshoty kolekcji; w klastrze snapshoty trzeba tworzyć/przywracać na każdym node. 
api.qdrant.tech
docs.e2enetworks.com

5) Web UI

Lokalnie: http://localhost:6333/dashboard – podejrzyj kolekcje, punkty, payload, uruchamiaj REST z konsoli UI, wgrywaj snapshoty. 
qdrant.tech
+1

FAQ / problemy

„pack exceeds maximum allowed size (2.00 GiB)” przy push do GitHuba
Nie wrzucaj ciężarów: node_modules/, .venv/, data/ (o ile nie chcesz), kb/ itp.
Jeśli jednak chcesz snapshoty w repo – użyj Git LFS:

git lfs install
git lfs track "*.snapshot"
git add .gitattributes && git commit -m "Enable LFS" && git push


Gdzie trzymane są dane Qdrant?
W kontenerze: /qdrant/storage. Zamontuj wolumen/ścieżkę hosta, żeby dane były trwałe. 
qdrant.tech

Nie działa restore z URL
Upewnij się, że URL jest osiągalny z perspektywy Qdrant (tej samej maszyny / sieci). W przeciwnym razie użyj wariantu file:// i skopiuj plik do /qdrant/snapshots.


Wklej ten blok do feniks/Makefile (albo dopisz do istniejącego). Zawiera: install, qdrant-up, kb-index, kb-search-js, kb-search-html, oraz snapshoty: snapshot-create, snapshot-list, snapshot-download, snapshot-restore-file, snapshot-restore-url.

SHELL := /bin/bash

# --- Konfiguracja domyślna (możesz nadpisać w linii poleceń) ---
HOST ?= 127.0.0.1
PORT ?= 6333
COLLECTION ?= frontend_feniks
ROOT ?= /home/grzegorz/cloud/Dockerized/frontend
OUT ?= .
MODEL ?= intfloat/multilingual-e5-base
ALPHA ?= 0.8
TOPK ?= 12
MODULES ?= all
CONTAINER ?= qdrant       # nazwa kontenera Qdrant (zmień jeśli inna, np. feniks-qdrant-1)

VENV := .venv
CURL := curl -sS

.PHONY: install qdrant-up kb-index kb-search-js kb-search-html snapshot-create snapshot-list snapshot-download snapshot-restore-file snapshot-restore-url

# 1) Python venv + zależności
install:
	python3 -m venv $(VENV)
	$(SHELL) -lc 'source $(VENV)/bin/activate && pip install -U pip && pip install -r requirements.txt'

# 2) Qdrant (Docker Compose)
qdrant-up:
	docker compose -f docker-compose.qdrant.yml up -d

# 3) Zbuduj bazę wiedzy (index)
kb-index:
	$(SHELL) -lc 'source $(VENV)/bin/activate && \
	  python scripts/build_kb.py index \
	    --root "$(ROOT)" \
	    --out  "$(OUT)" \
	    --collection "$(COLLECTION)" \
	    --host $(HOST) --port $(PORT) \
	    --model "$(MODEL)" \
	    --reset --write-ignores'

# 4) Wyszukiwanie – JS (podaj zapytanie: Q="...")
kb-search-js:
	@test -n "$(Q)" || (echo 'Usage: make kb-search-js Q="zapytanie" [ALPHA=0.8] [TOPK=12] [MODULES=all]'; exit 1)
	$(SHELL) -lc 'source $(VENV)/bin/activate && \
	  python scripts/build_kb.py search "$(Q)" \
	    --mode js --alpha $(ALPHA) --topk $(TOPK) --modules $(MODULES)'

# 5) Wyszukiwanie – HTML (podaj zapytanie: Q="...")
kb-search-html:
	@test -n "$(Q)" || (echo 'Usage: make kb-search-html Q="zapytanie" [ALPHA=0.7] [TOPK=12] [MODULES=all]'; exit 1)
	$(SHELL) -lc 'source $(VENV)/bin/activate && \
	  python scripts/build_kb.py search "$(Q)" \
	    --mode html --alpha $(ALPHA) --topk $(TOPK) --modules $(MODULES)'

# --- Snapshoty Qdrant ---

# Utwórz snapshot kolekcji
snapshot-create:
	$(CURL) -X POST "http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots" | jq .

# Lista snapshotów
snapshot-list:
	$(CURL) "http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots" | jq .

# Pobierz snapshot (SNAPSHOT=<nazwa z listy>) -> backups/<plik>
snapshot-download:
	@test -n "$(SNAPSHOT)" || (echo 'Usage: make snapshot-download SNAPSHOT=<name>'; exit 1)
	mkdir -p backups
	$(CURL) -L "http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots/$(SNAPSHOT)" -o backups/$(COLLECTION)-$(SNAPSHOT)

# Przywróć z pliku (backups/<plik>) – kopiuje do kontenera i recover
snapshot-restore-file:
	@test -n "$(SNAPSHOT)" || (echo 'Usage: make snapshot-restore-file SNAPSHOT=<file-in-backups>'; exit 1)
	docker cp backups/$(SNAPSHOT) $(CONTAINER):/qdrant/snapshots/
	$(CURL) -X PUT "http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots/recover" \
	  -H "Content-Type: application/json" \
	  -d "{\"location\":\"file:///qdrant/snapshots/$(SNAPSHOT)\",\"priority\":\"snapshot\"}" | jq .

# Przywróć bezpośrednio z URL Qdrant
snapshot-restore-url:
	@test -n "$(SNAPSHOT)" || (echo 'Usage: make snapshot-restore-url SNAPSHOT=<name-on-server>'; exit 1)
	$(CURL) -X PUT "http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots/recover" \
	  -H "Content-Type: application/json" \
	  -d "{\"location\":\"http://$(HOST):$(PORT)/collections/$(COLLECTION)/snapshots/$(SNAPSHOT)\",\"priority\":\"snapshot\"}" | jq .

Szybkie użycie

Setup: make install → make qdrant-up

Index: make kb-index ROOT=/ścieżka/do/frontu OUT=./

Search (JS): make kb-search-js Q="refaktoryzuj serwis autentykacji"

Search (HTML): make kb-search-html Q="popraw walidację formularza rejestracji" ALPHA=0.7

Snapshot:

make snapshot-create

make snapshot-list

make snapshot-download SNAPSHOT=<nazwa>

make snapshot-restore-file SNAPSHOT=<plik-z-backups>

make snapshot-restore-url SNAPSHOT=<nazwa>

Jeśli Twój kontener Qdrant nazywa się inaczej niż qdrant, podaj CONTAINER=feniks-qdrant-1 przy restore z pliku.