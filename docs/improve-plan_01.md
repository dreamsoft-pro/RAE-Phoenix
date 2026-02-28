Krytyczna ocena – czego wyraźnie brakuje / co budzi niepokój

Poniżej rzeczy, które z perspektywy kogoś z zewnątrz byłyby brakami krytycznymi przed szerszą publikacją i marketingiem:

Brak małego, absolutnie powtarzalnego DEMO end-to-end

Masz świetne dokumenty, ale brakuje repozytoryjnego “thin slice” typu:

examples/angularjs-demo/ – mini AngularJS 1.3 app + docelowy Next.js szkielet,

skrypt/README: “krok po kroku uruchom Feniksa, nagraj scenariusze, zbuduj kontrakty, odpal migrację, zobacz raport”.

Teraz czytelnik widzi: Feniks “może” to i tamto, ale nie ma jednego folderu, który odpala tę całą historię w 10 komendach.

Brak jednego prostego CLI pipeline’u dla AngularJS

Recipe są jako klasy Python (ControllerToComponentRecipe, TemplateToJsxRecipe, itd.), ale w README nie ma pokazanej komendy w stylu:

feniks angular migrate --project ./legacy_frontend --out ./next_app


czyli użytkownik musi sam pisać glue-code w Pythonie, co dla OSS-owego usera jest barierą. Z zewnątrz to wygląda jak “framework do budowy narzędzia migracyjnego”, a nie gotowe narzędzie – co jest OK, ale trzeba to uczciwie nazwać albo dodać cienką warstwę CLI.

Rozjazd między tym, co “opisane”, a tym, co na pewno jest spięte w kodzie

Dokumenty JS/PHP/OSS (ngMigrationAssistant, lighthouse-ci, rector, phpstan itd.) są opisane jako: “Feniks może…”, ale w snapshotcie nie widać jeszcze pełnych adapterów dla wszystkich tych narzędzi – to raczej plan + architektura, nie w 100% gotowa implementacja.

Dla kogoś z zewnątrz to tworzy ryzyko “conceptual debt”: dokumentacja jest trochę do przodu względem kodu. Warto jasno oddzielić: Implemented vs Planned i w README dać tabelkę z “realnie działa / w planie”.

Brak ultra-prostej ścieżki wejścia (“hello world”)

README jest bardzo mocny marketingowo i koncepcyjnie, ale dla nowego usera:

Quick Start pokazuje ingest/analyze, a nie Behavior Guard czy migrację AngularJS.

_Project_data_27_11_2025_07_58_…

Brakuje naprawdę małego przykładu: 2 pliki Pythona albo 1 mały moduł JS + komendy Feniksa + wygenerowany raport.

Czyli: dla Ciebie wszystko jest jasne, dla osoby spoza Twojego świata – próg wejścia jest nadal wysoki.

Branding / OSS-owe “dopolerowanie”

README nadal używa placeholdera https://github.com/your-org/feniks.git i “your-org” w badge’ach – przed publikacją to trzeba zmienić na docelowe repo i org.

_Project_data_27_11_2025_07_58_…

Nie widzę w snapshotcie plików typu CODE_OF_CONDUCT.md, SECURITY.md, gotowego CONTRIBUTING.md z konkretnymi zasadami PR / issues (README do niego odsyła, ale dobrze, by był treściwy).

_Project_data_27_11_2025_07_58_…

Roadmapa jest, ale nie ma jeszcze opisu polityki wydań (tagi, semver, jak będą oznaczane breaking changes).

_Project_data_27_11_2025_07_58_…

Granica z RAE – realna integracja vs flaga w .env

W .env.example masz RAE_ENABLED=false i sekcję RAE base URL / API key, ale w tym snapshotcie nie widzę jednego, konkretnego przykładu E2E Feniks↔RAE (np. demo z zapisaniem refleksji jako pamięci w RAE).

Dla świata OSS to ważne: czy RAE jest “nice to have”, czy realnie wspieranym integrałem.

Podsumowanie krytyczne:
Feniks jako rdzeń + Behavior Guard + AngularJS pack wygląda imponująco i “enterprise-grade”. Największe braki to produktowe dopięcie: jedno proste demo, CLI, doprecyzowanie co naprawdę działa dziś, a co jest “vision/roadmap”, plus dopolerowanie OSS-owych szczegółów (org, repo, małe przykłady).