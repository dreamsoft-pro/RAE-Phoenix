CZĘŚĆ 1: Plan Fazy 2.5 (Semantyczna Konsolidacja)
  Cel: Zamiana „worka puzli” (470 kawałków) w „zestaw montażowy” z instrukcją.


   1. Symbol Table Recovery (Odzyskiwanie Prawdy):
       * Agent Extractor (Qwen 32B) skanuje giganty (np. CalcCtrl.js).
       * Tworzy listę Scope Map: co jest w $scope, co jest wstrzykiwane (AuthService, PriceService), co jest zmienną lokalną.
       * Output: symbols.json dla każdego dużego modułu.
   2. UI Contract Building (Definicja Styków):
       * Agent Planner (Gemini 2.5 Pro) łączy symbols.json z fragmentami HTML.
       * Definiuje interfejsy TypeScript: jakie props musi przyjąć dany fragment, aby działał samodzielnie.
       * Output: component_contracts.json (np. „Sekcja Podsumowania Ceny potrzebuje pól: net, gross, vat”).
   3. Semantic Re-assembly (Logiczne Sklejanie):
       * Grupujemy te 470 atomowych fragmentów w większe, sensowne pliki (np. z 10 chunków powstaje jeden CalculatorForm.tsx), dbając o to, by każdy z nich miał domknięty kontrakt
         danych.
   4. Legacy Guard (Weryfikacja Behawioralna):
       * Generujemy testy Playwright, które sprawdzają, czy po wpisaniu wartości w nowym CalculatorForm.tsx wywołuje on te same metody PriceEngine, co oryginał.

  ---


  CZĘŚĆ 2: Manifest Fabryki Dreamsoft Pro 2.0 (Stan na Node 1)


  1. Klasyfikacja Kodu (Jak system widzi pliki)
  System automatycznie przydziela plik do jednej z trzech ścieżek na podstawie rozmiaru w bazie RAE:
   * Standard (< 20kB): Proste komponenty (np. Button, Icon, małe serwisy).
   * Giants (20kB - 100kB): Złożone kontrolery (np. CartCtrl, OrderService).
   * Super-Giants (> 100kB): Monolity (np. CalcCtrl, calc.html).


  2. Metody Podziału (Jak tniemy kod)
   * Standard Path: Bezpośrednia zamiana 1:1.
   * Hierarchical Decomposition: Podział na foldery (np. Auth/ zawiera Login.tsx, Register.tsx, useAuth.ts).
   * Atomic Slicing (v76): Cięcie na równe fragmenty 3000 znaków bezpośrednio z dysku (używane tylko dla Super-Giants, aby ominąć limity AI).


  3. Proces Produkcji i Kontroli (Cykl 3x3x3)
  Każdy plik przechodzi przez trzy etapy:
   1. Thinking Step (Blueprint): Model Gemini Pro projektuje architekturę (co zamienić na hook, co na state).
   2. Production (Writing): Model Qwen lub Gemini 3.1 Pro pisze czysty kod źródłowy.
   3. Consensus (Audit): Sprawdzenie, czy kod jest poprawny i czy nie „streszcza” logiki.


  4. Trzy Warstwy Oceny (Modele AI)
  System jest w pełni konfigurowalny przez tagi w RAE i plik .env.



  ┌────────────────────────┬─────────────────────────────────────┬───────────────────────────────────────────────────────────────┐
  │ Warstwa                │ Modele                              │ Rola                                                          │
  ├────────────────────────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ L1: Robocza (Local)    │ Qwen 2.5 (14B/32B), DeepSeek Coder  │ Szybkie szkice, sprawdzanie błędów składni, prosty kod.       │
  │ L2: Ekspercka (Hybrid) │ Gemini 2.5 Flash + Qwen             │ Budowa struktur, wstrzykiwanie zależności, Smart Naming.      │
  │ L3: Sądowa (Supreme)   │ Gemini 2.5 Pro, Claude 4.5, GPT-5.2 │ Rozstrzyganie konfliktów, planowanie gigantów, trudna logika. │
  └────────────────────────┴─────────────────────────────────────┴───────────────────────────────────────────────────────────────┘

  ---

  CZĘŚĆ 3: Ustawienia na Node 1 (Lumina)


   * Lokalizacja Silnika: /mnt/extra_storage/RAE-agentic-memory/agent_hive/
   * Magazyn Wyników: .../work_dir/components/ (Tu lądują Twoje pliki .tsx).
   * Baza Wiedzy: Kontener rae-postgres (PostgreSQL + pgvector).
   * Monitoring:
       * Jaeger: Port 16686 (Widzisz każdą decyzję AI jako kropkę na wykresie).
       * Supervisor: Proces w tle pilnujący, czy fabryka nie stoi (logi w /tmp/supervisor.log).
   * Konfigurowalność:
       * Plik hive_engine.py – Tu zmieniamy parametry CHUNK_SIZE, offset i limit.
       * Plik .env – Tu definiujemy, które modele są „Supreme”, a które „Local”.


  Moja opinia:
  Mamy potężną maszynę, która „przemieliła” kod, ale musimy teraz dołożyć jej mózg architektoniczny (Faza 2.5), aby te fragmenty zaczęły do siebie pasować. Bez tego będziesz miał 1000
  pięknych cegieł, ale nie będziesz miał planu budowy domu.


  Czy akceptujesz ten Manifest i Plan 2.5? Jeśli tak, zapisuję to jako nadrzędną instrukcję dla wszystkich agentów. 🕵️‍♂️🚀

