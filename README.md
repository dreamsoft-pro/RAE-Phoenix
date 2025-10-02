# Feniks: Baza Wiedzy i Silnik Refaktoryzacji dla Projektów AngularJS

**WAŻNE: Uruchomienie środowiska jest wymagane**

Przed użyciem `feniks`, **zawsze należy najpierw uruchomić lokalne środowisko deweloperskie** zgodnie z instrukcjami w repozytorium [dreamsoft-pro/Dockerized](https://github.com/dreamsoft-pro/Dockerized).

Jest to warunek konieczny do poprawnego działania kluczowych funkcji, w tym testów E2E (Oracle Tests) oraz agentów wchodzących w interakcję z aplikacją.

---

Feniks to zaawansowany system do budowy bazy wiedzy z kodu źródłowego AngularJS (1.x) oraz do przeprowadzania automatycznych refaktoryzacji. Jego celem jest przygotowanie precyzyjnych danych i narzędzi dla agentów AI, aby zautomatyzować i wspomóc proces migracji starych aplikacji do nowoczesnych technologii.

**Kluczowe Cechy:**

*   **Parsowanie oparte na AST:** Wykorzystuje parser Babel do precyzyjnego rozumienia struktury kodu JavaScript, identyfikując kontrolery, serwisy, dyrektywy i ich zależności.
*   **Wzbogacone Metadane:** Każdy fragment kodu jest wzbogacony o cenne metadane, takie jak zależności (DI), częstotliwość zmian (churn), złożoność cyklomatyczna i użycie wzorców `$watch` czy `$emit`.
*   **Zaawansowana Ocena Trudności Migracji:** Automatycznie oblicza `criticality_score` dla każdego fragmentu kodu, umożliwiając inteligentne priorytetyzowanie zadań refaktoryzacyjnych.
*   **Wyszukiwanie Hybrydowe:** Zapisuje wektory w bazie Qdrant, umożliwiając zaawansowane wyszukiwanie semantyczne i filtrowanie.
*   **Deklaratywny Silnik Refaktoryzacji:** Umożliwia definiowanie złożonych transformacji kodu (np. migracja serwisu AngularJS do zbioru funkcji TS) za pomocą prostych "receptur" w formacie YAML.
*   **Agent Automatyzujący Refaktoryzację:** Posiada agenta, który wykorzystuje bazę wiedzy do inteligentnego wyszukiwania celów i automatycznego stosowania na nich receptur.

---

## Szybki Start

### 1. Wymagania

*   Python 3.10+
*   Node.js 18+
*   Docker

### 2. Instalacja

Zalecane jest uruchomienie projektu w izolowanym środowisku wirtualnym Pythona.

```bash
# Sklonuj repozytorium
git clone https://github.com/dreamsoft-pro/feniks.git
cd feniks

# Stwórz i aktywuj środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate

# Zainstaluj zależności Python i Node.js
pip install -r requirements.txt
npm install
```

### 3. Uruchomienie Bazy Danych

Feniks używa Qdrant jako wektorowej bazy danych.

```bash
# Uruchom kontener Qdrant w tle
sudo docker compose -f docker-compose.qdrant.yml up -d
```
*Uwaga: `sudo` może być wymagane w zależności od konfiguracji Dockera.*

### 4. Budowanie Bazy Wiedzy

Głównym poleceniem jest `feniks_cli.py build`. Wskazuje ono na katalog z kodem AngularJS i buduje całą bazę wiedzy.

```bash
# Uruchom pełen proces budowania bazy wiedzy
python3 scripts/feniks_cli.py build --reset
```

### 5. Automatyczna Refaktoryzacja (Nowość!)

Feniks zawiera agenta do automatycznej refaktoryzacji kodu na podstawie zdefiniowanych reguł (receptur).

```bash
# Przykład: Uruchom agenta, aby znalazł do 5 serwisów ('kind:service')
# i zastosował na nich recepturę migracji w trybie symulacji (--dry-run).

python3 scripts/refactor_agent.py \
  --recipe recipes/angularjs-service-to-ts-function.yml \
  --query "kind:service" \
  --limit 5 \
  --dry-run
```

---

## Testowanie

Projekt zawiera zestaw testów jednostkowych i integracyjnych. Aby je uruchomić, użyj `pytest`.

```bash
# Uruchom wszystkie testy
pytest
```

### Dane Logowania do Testów

Do testowania funkcjonalności wymagających zalogowania, można użyć następujących danych:

*   **Login:** `office@diditalprint.pro`
*   **Hasło:** `1234`

---
## Struktura Projektu

*   `scripts/feniks_cli.py`: Główny punkt wejścia CLI do budowania bazy wiedzy.
*   `scripts/refactor_agent.py`: Agent automatyzujący, który wyszukuje cele w bazie wiedzy i uruchamia na nich refaktoryzację.
*   `scripts/apply_recipe.py`: Silnik wykonujący pojedynczą recepturę refaktoryzacyjną na pliku.
*   `scripts/js_html_indexer.mjs`: Silnik parsowania AST dla kodu JS i HTML.
*   `recipes/`: Katalog z recepturami refaktoryzacyjnymi w formacie YAML.
*   `scripts/feniks/`: Pakiet Pythona zawierający główną logikę aplikacji (konfiguracja, typy, logger).
*   `tests/`: Testy jednostkowe i integracyjne.
*   `requirements.txt`: Zależności Pythona.
*   `package.json`: Zależności Node.js.