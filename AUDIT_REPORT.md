# Raport z Audytu Silnika "Feniks"

**Data:** 2025-09-27
**Audytor:** Jules

## 1. Wprowadzenie

Niniejszy raport podsumowuje wyniki audytu kodu i architektury silnika "Feniks". Celem audytu było zidentyfikowanie mocnych i słabych stron projektu oraz sformułowanie rekomendacji dotyczących dalszych prac refaktoryzacyjnych, mających na celu podniesienie jakości, wydajności i testowalności rozwiązania.

## 2. Główne Ustalenia

### 2.1. Architektura: Dwa Równoległe Silniki Ingestycji

Najpoważniejszym problemem architektonicznym jest istnienie dwóch oddzielnych, niezintegrowanych ze sobą silników do przetwarzania kodu źródłowego:

1.  **Silnik w Pythonie (`scripts/build_kb.py`):**
    *   Odpowiedzialny za cały pipeline: skanowanie plików, chunkowanie, embedding, obliczenia TF-IDF i zapis do Qdrant.
    *   Używa **wyłącznie wyrażeń regularnych (regex)** do parsowania kodu AngularJS, co jest podejściem bardzo kruchym, podatnym na błędy i niezdolnym do pełnego zrozumienia struktury kodu.

2.  **Silnik w Node.js (`scripts/js_html_indexer.mjs`):**
    *   Używa parsera **Babel (@babel/parser) do budowy Abstrakcyjnego Drzewa Składni (AST)**, co jest podejściem znacznie bardziej solidnym i precyzyjnym.
    *   Potrafi poprawnie identyfikować komponenty AngularJS (kontrolery, serwisy, dyrektywy), ich nazwy oraz zależności (DI).
    *   Jego wynik (plik `chunks.mjs.jsonl`) **jest całkowicie ignorowany** przez główny skrypt w Pythonie.

**Wniosek:** Projekt posiada potężne narzędzie do analizy kodu (parser AST), ale go nie wykorzystuje w głównym procesie. Zamiast tego polega na zawodnej metodzie opartej na regex. Kluczowym celem refaktoryzacji musi być **unifikacja tych dwóch silników** i oparcie całego procesu na danych z parsera AST.

### 2.2. Jakość Kodu: Monolit i Brak Modularyzacji

Skrypt `scripts/build_kb.py` jest przykładem **kodu monolitycznego**. Cała logika, od operacji na plikach, przez heurystyki AngularJS, po embedding i komunikację z Qdrant, znajduje się w jednym, bardzo długim pliku.

*   **Utrudniona konserwacja:** Wprowadzanie zmian w jednej części logiki (np. w komunikacji z Qdrant) grozi niezamierzonymi błędami w innych.
*   **Niska czytelność:** Trudno jest szybko zrozumieć przepływ danych i odpowiedzialność poszczególnych funkcji.
*   **Brak reużywalności:** Funkcje są ściśle powiązane z kontekstem skryptu i nie mogą być łatwo użyte w innych miejscach.

**Rekomendacja:** Należy dokonać refaktoryzacji skryptu `build_kb.py`, wydzielając logiczne części do osobnych modułów w ramach dedykowanego pakietu Pythona (np. w katalogu `feniks/`). Przykładowe moduły: `qdrant_client.py`, `embedding.py`, `chunking.py`, `cli.py`.

### 2.3. Logika Ingestycji: Niewykorzystany Potencjał i Uproszczenia

*   **Chunkowanie:** Obecne strategie chunkowania (zarówno w Pythonie, jak i Node.js) są bardzo proste. Dzielą kod na poziomie funkcji lub sekcji HTML. Brakuje bardziej zaawansowanych technik, które mogłyby zachować szerszy kontekst semantyczny, kluczowy dla jakości systemu RAG.
*   **Metadane:** Parser AST w Node.js wydobywa cenne metadane (nazwy, zależności), ale można by je jeszcze wzbogacić, np. o komentarze JSDoc, powiązania z plikami `templateUrl`, czy bardziej szczegółowe typy węzłów AST.
*   **Obsługa Sparse Vectors:** Skrypt Pythona próbuje używać wektorów rzadkich (sparse vectors), ale ostrzeżenie `qdrant-client nie obsługuje 'sparse_vectors'` wskazuje na problem z kompatybilnością wersji klienta lub jego konfiguracji. Należy to zbadać i naprawić, aby w pełni wykorzystać potencjał wyszukiwania hybrydowego.

### 2.4. Testowalność: Całkowity Brak Testów

W projekcie **nie ma żadnych testów jednostkowych ani integracyjnych**. To krytyczne zaniedbanie, które sprawia, że:
*   Każda zmiana w kodzie jest ryzykowna i może prowadzić do regresji.
*   Nie ma formalnego sposobu na weryfikację poprawności działania kluczowych komponentów (np. czy chunkowanie działa zgodnie z oczekiwaniami, czy dane są poprawnie zapisywane w Qdrant).

**Rekomendacja:** Należy wprowadzić framework do testowania (np. `pytest`) i stworzyć zestaw testów pokrywających kluczowe ścieżki logiki, w tym:
*   **Testy jednostkowe** dla funkcji w nowo wydzielonych modułach.
*   **Testy integracyjne** dla całego pipeline'u (od pliku źródłowego do zapytania do Qdrant) na małym, kontrolowanym zestawie danych.

### 2.5. Zarządzanie Zależnościami

Plik `requirements.txt` jest niekompletny. Podczas uruchamiania okazało się, że brakuje w nim pakietów `langdetect` i `deep-translator`, mimo że są one importowane i używane w kodzie.

**Rekomendacja:** Należy uzupełnić `requirements.txt` o wszystkie faktyczne zależności.

## 3. Podsumowanie i Priorytety

Projekt "Feniks" ma solidne fundamenty koncepcyjne i wykorzystuje właściwe technologie (AST, wektory, Qdrant). Jednak jego obecna implementacja jest na etapie prototypu, z poważnymi wadami architektonicznymi i jakościowymi.

**Priorytety na fazę refaktoryzacji:**

1.  **(Krytyczny)** Zintegrować silnik Node.js (AST) z resztą pipeline'u, czyniąc go jedynym źródłem chunków i metadanych.
2.  **(Wysoki)** Zrefaktoryzować monolityczny skrypt `build_kb.py` do postaci modułowej.
3.  **(Wysoki)** Wprowadzić testy jednostkowe i integracyjne przy użyciu `pytest`.
4.  **(Średni)** Uzupełnić i uporządkować zależności w `requirements.txt`.
5.  **(Średni)** Zbadać i naprawić problem z obsługą wektorów rzadkich (sparse vectors).
6.  **(Niski)** Ulepszyć strategie chunkowania i wzbogacić metadane.