Przerabiam frontend dreamsoft przy pomocy RAE i Feniks. Zespół agentów na node1 przerobił wszystkie serwisy z angularjs na NEXT.js robią to fizycznie modele Qwen i DeepSeek sprawdzą nad nimi są 3 warstwy osobnej kontroli 1) Qwen DeepSeek ollama 2) Gemini 3 + qwen + DeepSeek 3) Gemini 3, Claude 4.5 ChatGPT (płatne modele tylko gdy wcześniejsze nie dochodzą do konsensusu). Ponad 500 plików zostało przerobione w dobę, a teraz Feniks podzielił 117 szablonów HTML na ponad 470 części i agenci próbują to ogarnąć, ale co chwilę wychodzi jakaś blokada. Z pierwszą częścią zeszło mi ze 3 dni na ustawienie by praca agentom szła płynnie. Z szablonami pewnie będzie podobnie. Chcę mieć 1 mądry mechanizm który ogarnia refactor legacy code i pomaga również w pisaniu nowych rzeczy. Czy pamiętasz architekturę tych projektów by coś doradzić? Feniksa trochę przerobiłem dodając mu DeepSeek i Qwen do chunkingu kodu. Repo jeszcze nie zaktualizowałem na github, przypominam Ci poniżej o co mi chodzi:

https://github.com/dreamsoft-pro/RAE-agentic-memory

https://github.com/dreamsoft-pro/RAE-Feniks

Zastanawiam się czy nie udostępnić dreamsoft jako OpenSource mimo że ostatnie 15 lat żyłem z tego kodu.
Oczywiście najpierw chcę go maksymalnie uwspółcześnić. By był mega intuicyjny dla
Userow Google a najbardziej dla agentów AI, myślę że niedługo agenci zdominują rynek handlu internetowego lub coś co ich zastąpi. 
Takie mam myśli na moim tygodniowym urlopie który dziś zacząłem😉 

Tak — pamiętam sens tej architektury i dokładnie to, co opisujesz, jest „naturalnym” momentem, w którym sam chunking + konsensus modeli przestaje wystarczać, bo HTML-y (zwłaszcza legacy AngularJS) nie są „kodem” w tym sensie co serwisy: mają kontekst widoku, scope, includy, transkluzję, dyrektywy, warunki, powtarzalność i ukryte kontrakty UI.

Masz już dwa kluczowe elementy układanki:

RAE = warstwa pamięci / reguł / twardych kontraktów / audytu i “dlaczego tak”

Feniks = warstwa wykonawcza refaktoru (plan → patche → walidacje → iteracje)

Teraz brakuje Ci jednego „mądrego mechanizmu”, który połączy to w powtarzalny pipeline i zrobi z HTML-owych szablonów coś tak samo sterowalnego jak z TS/JS.

Poniżej propozycja, która w praktyce rozwiązuje dokładnie Twoje „blokady co chwilę”.

1) Jeden mechanizm: Contract-First Refactor Orchestrator (CFRO)

Zrób z Feniksa „silnik”, a nad nim dodaj orchestrator kontraktów (to może być moduł w Feniksie albo osobny serwis). Jego rola:

A. Zanim agent dotknie pliku, musi mieć kontrakt

Dla każdego artefaktu (komponentu/strony/fragmentu szablonu) orchestrator tworzy i wersjonuje:

UI Contract (wejścia/wyjścia)

props/parametry, eventy, linki, wymagane dane, warianty widoku

mapowanie: Angular scope → Next props / hooks

Behavior Contract (zachowanie)

co ma się dziać przy interakcjach, walidacji, błędach, stanach pustych

minimum: scenariusze “happy path” + “edge”

Data Contract (API)

jakie endpointy i jakie pola są naprawdę używane w UI

redukuje „przepisywanie w próżnię”

To jest dokładnie to, co u Ciebie robią „hard frames” — tylko zastosowane do UI.

B. „Legacy Behavior Guard” jako bramka

Ty już masz tę koncepcję w głowie (i wcześniej ją zapisywaliśmy): zanim refaktor przejdzie, musi udowodnić zgodność.

Dla HTMLi to znaczy: nie tylko testy unit, ale:

snapshot DOM (po stronie renderera)

visual regression (Playwright) dla kluczowych ekranów

logika danych: czy te same pola są czytane i te same akcje wywoływane

Wtedy agent nie „zgaduje”, tylko “dowodzi”.

2) Dlaczego szablony HTML się klinują i jak to odblokować
Problem: 117 szablonów → 470 kawałków

To typowa pułapka: chunking dzieli tekst, ale nie dzieli kontraktów.

W AngularJS szablon często ma:

implicit $scope (dziedziczenie)

dyrektywy (ukryta logika)

includy/partials zależne od kontekstu

filtry, ng-if/ng-repeat z efektami ubocznymi w controllerze

Rozwiązanie: zamiast „dzielić HTML”, najpierw rób UI Dependency Graph.

Minimalny algorytm, który robi różnicę

Parsujesz szablon do AST (HTML parser, nie regex).

Wyciągasz:

listę bindingów {{ }} i atrybutów ng-*

nazwy funkcji z ng-click, ng-change, itp.

zależności od dyrektyw/custom elementów

Budujesz graf: fragment → wymagane symbole scope / wywołania / dyrektywy

Dopiero wtedy tniesz na komponenty tak, żeby każdy komponent miał domknięty kontrakt danych.

To jest „chunking semantyczny”, a nie tekstowy.

W praktyce: 470 części pewnie sklei Ci się z powrotem do np. 150–220 sensownych komponentów, bo część fragmentów nie ma sensu jako samodzielne byty.

3) Jak spiąć Twoje 3 warstwy modeli w sposób stabilny

Masz dobre piętrowanie (local → Gemini → paid). Dodałbym jedną rzecz, która zwykle zmienia wszystko:

Wymuś role agentów i artefakty wyjściowe

Niech nie “wszyscy robią wszystko”.

Proponowany podział:

Extractor (lokalny, szybki)
generuje kontrakt + graf zależności + listę ryzyk.

Planner (Gemini/Qwen/DeepSeek)
układa plan migracji: jakie komponenty najpierw, jakie testy, jakie stuby danych.

Implementer (lokalne + eskalacja)
robi patch.

Verifier (zawsze osobny)
odpala testy + porównania + ocenia zgodność kontraktu.

Arbiter (dopiero płatne)
tylko gdy Verifier wykryje konflikt i nie ma konsensusu.

Klucz: Verifier nie może być tym samym modelem/agentem co Implementer.

4) “Refactor legacy i pisanie nowych rzeczy” jednym mechanizmem

Jeśli CFRO ma być też do nowych feature’ów, to pipeline jest ten sam, tylko startujesz od kontraktu “greenfield”:

UI Contract + Data Contract powstają od razu

Behavior Contract jest równocześnie specyfikacją testów E2E

Feniks generuje kod i od razu generuje “guardy” (testy, storybook, snapshots)

Czyli: ten sam proces, różni się tylko źródłem prawdy (legacy vs spec).

5) Open Source Dreamsoft: jak to ugryźć bez samobója biznesowego

Jeśli żyłeś 15 lat z tego kodu, to “otworzyć wszystko” w jednym ruchu zwykle jest zbyt ryzykowne. Masz kilka bezpieczniejszych wariantów:

Opcja A: Open-core (najczęstsza i praktyczna)

Core: silnik wyceny / katalog produktów / UI framework / integracje podstawowe

Closed: integracje klienckie, konektory ERP, płatności specyficzne, automatyzacje produkcyjne, SLA

Plus: budujesz community i standard, nie oddajesz marży z wdrożeń.

Opcja B: “Source-available” najpierw

kod widoczny, ale licencja ogranicza użycie komercyjne bez umowy

daje Ci efekt „AI-friendly + audytowalne”, ale kontrolujesz komercję

Opcja C: Otwierasz tylko NOWY frontend (Next.js) + kontrakty API

A backend zostaje na razie zamknięty.
To często najlepszy kompromis, jeśli celem jest “mega dla agentów, Google i userów”.

Jeśli chcesz, mogę Ci rozpisać krótką matrycę decyzji: co otwierać, kiedy, z jaką licencją, jakie ryzyka IP/RODO/sekrety handlowe — ale już teraz moja intuicja: najpierw otwórz warstwę, która tworzy standard (UI + kontrakty), nie tę, która tworzy przewagę wdrożeniową.

6) Co bym zrobił u Ciebie w najbliższych 7–14 dniach (bez „heroic effort”)

Dodać do Feniksa moduł: UI Contract Extractor dla AngularJS templates
(graf zależności + symbol table scope).

Ustawić Legacy Behavior Guard dla 10 najważniejszych ekranów:

Playwright: screenshoty + flows

snapshot DOM

Zmienić “470 fragmentów” w “komponenty domykające kontrakt danych”.

Dopiero wtedy pozwolić agentom masowo migrować.

To zamienia “praca idzie, ale co chwilę blokada” w “taśmę produkcyjną”.

Jeżeli chcesz, w kolejnym kroku mogę Ci od razu zaproponować konkretną strukturę folderów i format plików kontraktów (np. contracts/ui/*.yml, contracts/behavior/*.spec.md, contracts/data/*.jsonschema) + jak to wpiąć w RAE tak, żeby kontrakty były pamięcią semantyczną i żeby Verifier umiał pytać RAE “czy to dalej spełnia zasady”.

A na urlopie: te myśli są sensowne — to jest dokładnie ten moment, kiedy z “refaktoru” robisz platformę, a z platformy robi się albo przewaga, albo community.

Ast Feniks robi, to zaplanowałem już pół roku temu

No i super — to znaczy, że masz już “materiał nośny”. Problem, który opisujesz, nie wynika z braku AST, tylko z tego, że AST w legacy UI nie wystarcza, jeśli nie masz jeszcze warstwy kontraktów + walidacji + grafu zależności semantycznych.

Masz AST → więc teraz najczęściej brakuje jednego z 3 elementów (albo wszystkich naraz):

1) AST bez “symbol table” i bez rozwiązywania kontekstu

Dla AngularJS template samo drzewo HTML/atributów to za mało. Potrzebujesz tablicy symboli:

jakie identyfikatory pochodzą z $scope (dziedziczenie!)

które są lokalne dla ng-repeat (aliasy, $index, itd.)

które są z dyrektyw / transkluzji

które funkcje wywołują się w ng-click/ng-change i gdzie są zdefiniowane

Jeśli tego nie wyprowadzisz, agent tnie “poprawnie składniowo”, ale semantycznie robi fragmenty bez domknięcia danych → i masz blokady.

Heurystyka: jeśli po podziale na komponenty rośnie liczba “TODO: pass this” / “unknown prop” / “not defined”, to znaczy że symbol table jest niepełna.

2) Brak “UI dependency graph” jako źródła prawdy dla chunkingu

Feniks może robić AST, ale jeśli chunking jest oparty o:

długość tekstu

layout

arbitralne “granice sekcji”
to wyjdą Ci te 470 puzzli, które nie składają się w całość.

Masz AST, więc zrób z niego graf:

węzeł = kandydat na komponent
krawędzie = zależności: uses(symbol), calls(fn), requires(directive), includes(partial)

Dopiero na grafie robisz cięcie tak, żeby:

minimalizować zależności zewnętrzne

minimalizować liczbę wymaganych symboli z rodzica

maksymalizować spójność (cohesion)

To jest moment, w którym refaktor przestaje być “próbami”, a robi się “mechaniką”.

3) Brak “Legacy Behavior Guard” dla UI

Nawet przy idealnym grafie i symbolach, UI refaktor bez bramki regresji kończy się spiralą:
“agent przerobił — coś działa — potem okazuje się że w edge-case nie”.

Dla 10–20 kluczowych ekranów musisz mieć minimum:

Playwright flows (happy path + 1–2 edge)

snapshot DOM lub snapshot komponentów (w jakiejś ustalonej formie)

porównanie: jakie pola danych są czytane i jakie akcje są wywoływane

Wtedy blokady zamieniają się w “fail fast” z jednoznaczną przyczyną.

Co bym zrobił “na Twoim poziomie” (czyli bez cofania się do zera)

Skoro AST już jest:

Dopisz etap: Symbol Table Builder (template → scope symbols)
Output: template_symbols.json (lista symboli + źródło + zakres: global/repeat/if).

Dopisz etap: UI Dependency Graph Builder (AST + symbol table)
Output: ui_graph.json (nodes/components + edges).

Zmień chunking: nie “cięcie HTML”, tylko “cięcie grafu”
(algorytm: domykanie zależności + minimalny cut).

Wepnij Guard: testy E2E dla top ekranów jako gate w CI Feniksa.

To jest ta “jedna mądra rzecz”, której szukasz: AST → (symbols) → graph → contracts → refactor → guard.