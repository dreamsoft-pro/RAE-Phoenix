# Feniks: Baza Wiedzy dla Projektów AngularJS

Feniks to zaawansowany silnik do budowy bazy wiedzy z kodu źródłowego AngularJS (1.x). Jego celem jest przygotowanie precyzyjnych danych dla agentów AI, aby zautomatyzować i wspomóc proces migracji starych aplikacji do nowoczesnych technologii.

**Kluczowe Cechy:**

*   **Parsowanie oparte na AST:** Wykorzystuje parser Babel do precyzyjnego rozumienia struktury kodu JavaScript, identyfikując kontrolery, serwisy, dyrektywy i ich zależności.
*   **Semantyczne Chunkowanie:** Dzieli kod JS i HTML na logiczne, semantycznie spójne fragmenty (chunki), zachowując ich kontekst.
*   **Wzbogacone Metadane:** Każdy chunk jest wzbogacony o cenne metadane, takie jak zależności (dependency injection), komentarze z kodu i typy węzłów AST.
*   **Wyszukiwanie Hybrydowe:** Tworzy wektory gęste (dense) i rzadkie (sparse, TF-IDF) i zapisuje je w bazie wektorowej Qdrant, umożliwiając zaawansowane wyszukiwanie hybrydowe.
*   **Modułowa Architektura:** Kod jest w pełni zmodularyzowany i przetestowany, co ułatwia jego dalszy rozwój i konserwację.

---

## Szybki Start

### 1. Wymagania

*   Python 3.10+
*   Node.js 18+
*   Docker

### 2. Instalacja

```bash
# Sklonuj repozytorium
git clone https://github.com/dreamsoft-pro/feniks.git
cd feniks

# Zainstaluj zależności Python i Node.js
npm install
pip install -r requirements.txt
```

### 3. Uruchomienie Bazy Danych

Feniks używa Qdrant jako wektorowej bazy danych. Najprostszym sposobem na jej uruchomienie jest użycie dostarczonego pliku Docker Compose.

```bash
# Uruchom kontener Qdrant w tle
sudo docker compose -f docker-compose.qdrant.yml up -d
```
*Uwaga: `sudo` może być wymagane w zależności od konfiguracji Dockera.*

### 4. Budowanie Bazy Wiedzy

Głównym poleceniem jest `build_kb.py index`. Wskazuje ono na katalog z kodem AngularJS i buduje całą bazę wiedzy.

```bash
# Przykład budowania bazy wiedzy
python scripts/build_kb.py index \
  --root /sciezka/do/twojego/frontendu \
  --collection moj-projekt-angular \
  --reset
```

### 5. Wyszukiwanie w Bazie Wiedzy

Po zbudowaniu bazy, możesz w niej wyszukiwać za pomocą polecenia `search`.

```bash
# Przykład: znajdź logikę związaną z autentykacją
python scripts/build_kb.py search "refaktoryzuj serwis logowania" \
  --collection moj-projekt-angular \
  --mode js

# Przykład: znajdź szablony formularzy
python scripts/build_kb.py search "formularz rejestracji użytkownika" \
  --collection moj-projekt-angular \
  --mode html
```

---

## Testowanie

Projekt zawiera zestaw testów jednostkowych i integracyjnych. Aby je uruchomić, użyj `pytest`.

```bash
# Uruchom wszystkie testy
pytest
```

---
## Struktura Projektu

*   `scripts/build_kb.py`: Główny punkt wejścia CLI.
*   `scripts/js_html_indexer.mjs`: Silnik parsowania AST dla kodu JS i HTML (wywoływany automatycznie).
*   `scripts/feniks/`: Pakiet Pythona zawierający główną logikę aplikacji.
    *   `core.py`: Centralne funkcje orkiestrujące.
    *   `embed.py`: Logika tworzenia embeddingów.
    *   `qdrant.py`: Klient i operacje na Qdrant.
    *   `types.py`: Definicje typów danych.
*   `tests/`: Testy jednostkowe i integracyjne.
*   `AUDIT_REPORT.md`: Szczegółowy raport z audytu przeprowadzonego przed refaktoryzacją.
*   `docker-compose.qdrant.yml`: Konfiguracja Docker Compose dla Qdrant.
*   `requirements.txt`: Zależności Pythona.
*   `package.json`: Zależności Node.js.