Feniks – Integracje z narzędziami Open Source

Wykorzystanie istniejących narzędzi do analizy, migracji i refaktoryzacji kodu

Feniks jest warstwą meta-refleksji, kontroli jakości i oceny ryzyka dla złożonych systemów kodu i workflow AI.
Jego rolą nie jest implementowanie własnych parserów czy transpilerów, lecz wykorzystanie najlepszych dostępnych narzędzi open source, a następnie ocena ich efektów zgodnie z BehaviorContracts, SystemModel i politykami (PolicyPack).

Ten dokument opisuje:

jakie narzędzia OSS Feniks wykorzystuje,

w jakich scenariuszach,

jak wygląda integracja,

jak Feniks buduje nad nimi warstwę refleksji,

oraz jakich narzędzi użyjemy jako fundament pod refaktory Python / PHP / JS / AngularJS / React / Next.js.

📌 1. Filozofia integracji OSS

Feniks działa jako:

[ KOD ] → [ NARZĘDZIA OSS ] → [ WYNIKI ] → [ FENIKS REFLECTION ] → [ BEHAVIOR REPORT ]


Feniks:

konfiguruje narzędzia,

odpala ich pipeline,

zbiera wyniki,

przekształca je w BehaviorSnapshots,

ocenia je względem kontraktów i polityk,

zapisuje raporty (opcjonalnie w RAE),

proponuje kolejne iteracje refaktoru.

Feniks = orkiestrator + analityk.
OSS = narzędzia operacyjne.

🐍 2. Python – analiza, refaktoryzacja, AST

(Ta sekcja jest kluczowa dla pierwszej realnej integracji Feniksa z projektami Pythonowymi — np. Billboard Splitter i Billboard Marker.)

2.1. Refaktoryzacja strukturalna (AST)
✔️ libcst

Najbardziej stabilne narzędzie do modyfikacji kodu Python bez utraty formatowania.

Użycie w Feniksie:

dzielenie monolitycznych plików/funkcji,

wydzielanie helperów,

generowanie typów,

poprawa importów.

✔️ bowler

Warstwa nad libcst do pisania dużych transformacji (codemods).

Użycie:

masowe zmiany API,

usuwanie martwego kodu,

migracje stylów.

✔️ rope

Refaktory funkcjonalne i obiektowe:

rename,

przenoszenie funkcji/klas,

extract method.

Użycie:

Feniks generuje „plan refaktoru”, rope go wykonuje.

2.2. Analiza jakości
✔️ ruff

Najbardziej kompletny linter/formatter/fixer.

Użycie:

sanity-check przed właściwym refaktorem,

automatyczne naprawy,

analiza „hotspots”.

✔️ mypy / pyright

Analiza typów.

Użycie:

Feniks generuje raport „type pain points”,

klasyfikuje miejsca do refaktoru,

buduje BehaviorContracts na bazie typowania.

2.3. Testy i snapshoty
✔️ pytest + snapshot testing

Feniks używa snapshotów jako BehaviorSnapshots.

Zastosowanie:

wykrywanie subtelnych regresji,

porównywanie wyników przed/po refaktorze.

🧩 3. JavaScript / TypeScript – refaktoryzacja, migracje, UI
3.1. AST & codemods
✔️ jscodeshift

Ramowy mechanizm transformacji kodu (Meta/Facebook).

Użycie:

przepisywanie AngularJS → React,

dzielenie komponentów,

zmiana hooków/lifecycle.

✔️ babel + plugins

Transformacje JS/TS, generowanie JSX.

Użycie:

konwersja template → JSX,

automatyzacja migracji.

✔️ recast

Parser/generator do utrzymania formatowania.

3.2. AngularJS (legacy)
✔️ ng-migration-assistant

Oficjalne narzędzie Google do audytu AngularJS.

Daje Feniksowi:

strukturę widoków,

listę dyrektyw,

zależności między modułami,

punkty ryzyka.

✔️ AngularJS → React codemods

Zestawy transformacji OSS:

ng-repeat → .map(),

ng-click → onClick,

template → JSX skeleton.

Feniks może to używać jako warstwę transformacji statycznych.

3.3. UI Behavior
✔️ Playwright

Zaawansowane scenariusze UI:

evaluate DOM,

waitFor,

click, type,

screenshoty.

Feniks wykorzystuje Playwright jako:

UI runner,

generator BehaviorSnapshots.

✔️ Cypress (opcjonalnie)

Jeśli projekt już go używa.

🌐 4. PHP – analiza i modernizacja
4.1. Refaktory i modernizacja
✔️ rector

Najważniejsze narzędzie do refaktoryzacji PHP.

Feniks może generować:

reguły do Rectora,

pliki konfiguracyjne,

iteracyjne refaktory.

Typowe użycia:

modernizacja do nowszych wersji PHP,

dodawanie typów,

zmiana API,

wycinanie martwego kodu.

4.2. Analiza statyczna
✔️ phpstan

wykrywanie błędów,

analiza przepływu danych.

✔️ psalm

alternatywa dla phpstan,

bardziej rygorystyczne typowanie.

4.3. Style i forma
✔️ php-cs-fixer

Feniks może używać jako:

sanity-check,

automatyczne porządki w kodzie,

ujednolicenie stylu przed refaktorem.

🎨 5. Web UI / Behavior
5.1. UI Testing Engines
✔️ Playwright / Puppeteer

Do odpalania BehaviorScenario na UI:

snapshot DOM,

network log,

js console log.

Feniks zamienia to w BehaviorSnapshots.

5.2. Performance
✔️ lighthouse-ci

Feniks może:

mierzyć wydajność starego AngularJS,

porównywać z React/Next po migracji.

🧠 6. Jak Feniks wykorzystuje OSS (workflow)

Przykład dla Python:

1. Feniks → „zrób audyt backendu”
2. Feniks odpala:
   - ruff (lint)
   - mypy (typy)
   - bowler (pierwsze refaktory)
   - libcst (precyzyjne transformacje)
3. Feniks → BehaviorSnapshots
4. Feniks → porównanie z BehaviorContracts
5. Feniks → RiskScore + rekomendacje
6. (opcjonalnie) RAE → zapis wyników jako pamięć długoterminowa
7. Feniks → iteracja 2


Przykład dla AngularJS → Next.js:

1. Feniks → „zrób mapping UI”
2. ng-migration-assistant → skan AngularJS
3. Feniks → UiTemplateView (z HTML/CSS)
4. Feniks → BehaviorContracts (UI)
5. jscodeshift/babel → JSX skeleton
6. Feniks → porównanie BehaviorContracts (AngularJS → React)

🚀 7. Dlaczego to działa lepiej niż standalone narzędzia

Feniks dodaje:

warstwę meta-analizy,

kontrolę zgodności z kontraktami,

kontrolę ryzyka,

wyjaśnienia,

pamięć (jeśli zintegrowane z RAE),

możliwość iteracji.

Narzędzia OSS robią pojedyncze operacje.
Feniks robi z nich spójny system jakości.

📎 8. Status integracji / plan wdrożenia
Obszar	Narzędzie	Status w Feniksie	Etap wdrożenia
Python AST	libcst, bowler	w kolejce	po v1.0
Python audyt	ruff, mypy	planowane	przed refaktorem Billboard Splitter
AngularJS skan	ng-migration-assistant	planowane	po warstwie UiTemplateView
JS codemods	jscodeshift, babel	możliwe	refaktor AngularJS → React
PHP modernizacja	rector	możliwe	refaktor backendu PHP
UI behavior	Playwright	planowane	BehaviorGuard UI
performance	lighthouse-ci	opcjonalne	po migracjach UI
📘 9. Podsumowanie

Feniks nie zastępuje narzędzi open source — on podnosi je na wyższy poziom, dodając:

kontekst biznesowy,

kontrakty zachowań,

modele systemu,

analizę ryzyka,

iteracyjne planowanie,

refleksję nad wynikami,

integrację z pamięcią RAE.

To połączenie daje możliwość bezpiecznej refaktoryzacji, migracji i modernizacji dużych systemów — od Pythonowych narzędzi produkcyjnych po złożone fronty AngularJS.