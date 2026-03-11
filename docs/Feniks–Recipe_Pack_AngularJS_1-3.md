# Feniks – Recipe Pack: AngularJS 1.3 → Next.js (App Router)

## Cel

Ten dokument definiuje **kontrakty recipe’ów** oraz **wymagania implementacyjne** dla modułu Feniksa, który ma pomagać w migracji legacy AngularJS 1.x (w szczególności 1.3.x) do **Next.js (App Router, React 18, TypeScript)**.

Zakres obejmuje:

1. `controllers` → komponenty Next.js (funkcyjne, TSX).
2. `directives` → komponenty/hooki React/Next.
3. `templates` HTML (`ng-repeat`, `ng-if`, filtry, bindingi) → JSX/TSX.
4. AngularJS routing (`$routeProvider` / `ui-router`) → App Router (`app/` layout + segmenty).
5. `$scope` / `$rootScope` / `$watch` → stan w hookach i/lub Context API.

Dokument NIE opisuje front-endowego designu/UX – skupia się na **mapowaniu semantyki** AngularJS → Next.js oraz kontraktach dla recipe engine Feniksa.

---

## Ogólna architektura recipe’ów

Każdy recipe w Feniksie powinien mieć:

- **ID recipe** – np. `angularjs.controller-to-next-component`.
- **Wejście (AST / metadane)**:
  - plik źródłowy AngularJS (JS),
  - powiązany template (HTML),
  - kontekst modułu (moduł AngularJS, zależności, serwisy).
- **Wyjście**:
  - nowy plik TSX/TS,
  - zaktualizowane metadane (IR Feniksa),
  - propozycje zmian dla plików powiązanych (routing, importy).
- **Tryby działania**:
  - `dry_run` – tylko opis zmian (patch, diff, plan),
  - `apply` – generacja plików TSX/TS i aktualizacja struktury projektu.

Wszystkie recipe’y muszą:

- działać **idempotentnie** (powtórne uruchomienie nie psuje projektu),
- mieć **log poziomu „explain”** (dlaczego coś zostało zmapowane w taki, a nie inny sposób),
- mieć możliwość ustawienia **poziomu agresywności**:
  - `conservative` – minimalne zmiany, preferencja ostrzeżeń,
  - `balanced` (default),
  - `aggressive` – dopuszcza bardziej radykalne uproszczenia.

---

## 1. Recipe: Controllers → Komponenty Next.js

### 1.1. Zakres

- AngularJS 1.x `controller`:
  - zarejestrowany przez `.controller('NameCtrl', function(...) { ... })`
  - używany w `ng-controller="NameCtrl as vm"` lub `ng-controller="NameCtrl"` + `$scope`.

- Celem jest wygenerowanie:

  - **komponentu funkcjonalnego** (React 18, TSX),
  - z **typowanymi propsami**,
  - z logiką przepisanych metod z controllera,
  - z obsługą stanu za pomocą hooków (`useState`, `useReducer`, `useEffect`),
  - umieszczonego w strukturze Next.js:
    - preferencyjnie w `app/(legacy)/...` lub `app/_legacy/Angular/...` (konfigurowalne).

### 1.2. Wejście

#### 1.2.1. AST AngularJS controllera

Feniks ma dostarczyć recipe’owi:

- strukturę funkcyjną controllera:
  - nazwa kontrolera (`NameCtrl`),
  - nazwa modułu,
  - lista zależności (DI): `$scope`, `$http`, `SomeService`, `$state`, `$stateParams`, itd.
  - lista właściwości przypisywanych do:
    - `this` (w syntaksie `controllerAs`),
    - `$scope` (klasyczny styl).
  - definicje metod:
    - `this.doSomething = function(...) { ... }`,
    - `$scope.submit = function(...) { ... }`.

- powiązanie z template:
  - nazwa pliku HTML,
  - wykryte bindingi i użycia:

    - `vm.property` / `$scope.property`,
    - `ng-click="vm.doX()"`, `ng-submit="save()"`, itd.

#### 1.2.2. Konfiguracja

- `controller_to_next.target_dir`: docelowy katalog dla komponentów Next (np. `app/_legacy`).
- `controller_to_next.state_strategy`:
  - `useState` | `useReducer` | `external-store` (tylko hint – implementacja może użyć heurystyk).
- `controller_to_next.typing_mode`:
  - `loose` – typy `any` tam, gdzie nie wiadomo,
  - `strict` – generacja interfejsów + `TODO` dla nieznanych typów.

### 1.3. Wyjście

- Nowy plik TSX, np.:

  - z nazwą: `NamePage.tsx` / `NameView.tsx` (konfigurowalne),
  - eksportujący domyślny komponent React:
    ```tsx
    export default function NamePage(props: NamePageProps) { ... }
    ```

- Szkielet komponentu:
  - importy dla hooków, typów i serwisów,
  - definicja `props` (jeśli wyniknie z routing params lub użycia),
  - mapowanie pola controllera na `useState` / `useReducer`,
  - mapowanie metod controllera na funkcje wewnętrzne komponentu.

### 1.4. Zasady mapowania

1. **`this` / alias controllera**:

   - Jeśli `ng-controller="NameCtrl as vm"`:
     - wszystkie `vm.someProperty` → stan komponentu (`useState`),
     - wszystkie `vm.someMethod()` → funkcje wewnątrz komponentu.

   - Jeśli `ng-controller="NameCtrl"` + `$scope`:
     - `$scope.someProperty` → stan komponentu,
     - `$scope.someMethod = function...` → funkcja w komponencie.

2. **DI serwisów**:

   - Serwisy (`SomeService`, `OrderService`) **nie są przepisywane** – są injektowane przez importy TS:

     ```tsx
     import { OrderService } from "@/legacy/services/OrderService";
     ```

   - Recipe generuje stuby importów i `TODO`, jeśli nie znajdzie deklaracji.

3. **Asynchroniczność / $http / $resource**:

   - `$http.get/post/...` → `fetch` lub klient HTTP używany w projekcie (konfigurowalne).
   - `$q` → natywne Promise.

4. **Nawigacja ($state, $stateParams, $location)**:

   - mapowana do `next/navigation`:

     ```tsx
     import { useRouter, useSearchParams } from "next/navigation";
     ```

5. **Lifecycle**:

   - `$scope.$on('$destroy', ...)` → `useEffect` z cleanupem.
   - `$timeout` → `setTimeout` w `useEffect` lub dedykowany hook.

### 1.5. Artefakty dodatkowe

- `behavior_contract` – snapshot starych interakcji (opcjonalnie),
- `component_mapping.json` – mapowanie `controller_name` → `path/to/Component.tsx`.

---

## 2. Recipe: Dyrektywy → Komponenty / Hooki

### 2.1. Zakres

Obsługujemy:

- klasyczne dyrektywy rejestrowane przez `.directive('dsWidget', function() { ... })`,
- szczególnie:

  - `restrict: 'E' | 'A' | 'C'`,
  - `scope`:

    - izolowany (`scope: { ... }`),
    - dziedziczony (`scope: true`),
    - brak (`scope: false`).

  - `template` / `templateUrl`,
  - `link` / `compile`,
  - `controller` i `controllerAs`.

### 2.2. Strategie mapowania

1. **Dyrektywy strukturalne / layoutowe**:
   - → **komponenty React** (funkcyjne),
   - inputy dyrektywy → `props`,
   - transkluzja (`ng-transclude`) → `props.children`.

2. **Dyrektywy „zachowaniowe” (tylko `link` na istniejącym DOM)**:
   - → **hooki** (np. `useResizeObserver`, `useOnClickOutside`) lub dedykowane `useLegacyXxx`.

3. **Dyrektywy modyfikujące DOM niskopoziomowo**:
   - generujemy komponent/hook z **oznaczonym poziomem ryzyka** i `TODO`,
   - w Behavior Guard ustawiamy wyższy risk score threshold.

### 2.3. Wejście

- AST dyrektywy:
  - nazwa (`dsWidget`),
  - `restrict`,
  - definicja `scope`,
  - `template` / `templateUrl`,
  - `link` / `compile` body,
  - powiązania z controllerem (jeśli istnieją).

- Wystąpienia w template:
  - `<ds-widget some-attr="vm.x">` (element),
  - `ds-widget` jako atrybut.

### 2.4. Wyjście

- Komponent TSX w `components/legacy/`:

  ```tsx
  export interface DsWidgetProps {
    // wygenerowane z isolate scope
  }

  export function DsWidget(props: DsWidgetProps) { ... }
Jeżeli dyrektywa jest „behavior-only”:

hook:

tsx
Skopiuj kod
export function useDsWidget(ref: React.RefObject<HTMLElement>, options: DsWidgetOptions) { ... }
Mapowanie użyć:

automatyczny patch template’ów (AngularJS → JSX) opcjonalne,

inaczej: generowanie sugestii w raporcie.

2.5. Reguły mapowania scope
scope: { someProp: '=' } → props.someProp: T (dwukierunkowe bindowanie → zależne od strategii stanu).

scope: { onClick: '&' } → props.onClick: () => void.

scope: { label: '@' } → props.label: string.

3. Recipe: Template HTML → JSX/TSX
3.1. Zakres
Konwersja AngularJS template:

bindingi:

{{ vm.value }},

ng-bind="...",

dyrektywy:

ng-repeat, ng-if, ng-show, ng-hide, ng-class, ng-style,

eventy:

ng-click, ng-change, ng-submit, itd.

filtry:

{{ expr | filterName:arg }} do funkcji pomocniczych,

atrybuty specjalne:

ng-model, ng-disabled, ng-checked, etc.

→ do JSX (TSX) kompatybilnego z React/Next.

3.2. Ogólne zasady mapowania
Interpolacja {{ ... }}:

{{ vm.value }} → {vm.value}

wielokrotne interpolacje w tekście:

"Hello {{vm.user.name}}" → {"Hello "}{vm.user.name} lub użycie template stringa w logice.

ng-repeat:

ng-repeat="item in vm.items track by item.id":

jsx
Skopiuj kod
{vm.items.map((item) => (
  <li key={item.id}>...</li>
))}
bez track by:

domyślnie key={index} z ostrzeżeniem w logach Feniksa.

ng-if / ng-show / ng-hide:

ng-if="expr" → {expr && <Element ... />}

ng-show="expr" → style/className lub conditional rendering (konfigurowalne).

ng-hide="expr" → odwrotność !expr.

Eventy:

ng-click="vm.submit(item)" → onClick={() => vm.submit(item)}

ng-submit="save()" → onSubmit={(e) => { e.preventDefault(); save(); }}

ng-model:

mapowanie do controlled component:

jsx
Skopiuj kod
<input
  value={vm.form.name}
  onChange={(e) => setForm({ ...form, name: e.target.value })}
/>
recipe nie implementuje pełnej logiki form – generuje skeleton + TODO, chyba że jest podpięty dedykowany form-engine.

Filtry:

{{ amount | currency:'PLN' }} → formatCurrency(amount, "PLN")

{{ date | date:'yyyy-MM-dd' }} → formatDate(date, "yyyy-MM-dd")

Recipe generuje importy:

tsx
Skopiuj kod
import { formatCurrency, formatDate } from "@/legacy/filters";
Jeżeli filtr jest customowy (np. | myFilter):

generuje TODO i stub w legacy/filters/myFilter.ts.

3.3. Wejście
DOM/AST HTML template’u,

mapowanie użytych identyfikatorów (vm, $ctrl, $scope),

kontekst controllera.

3.4. Wyjście
plik .tsx z JSX,

mapping template.html → Component.tsx:

json
Skopiuj kod
{
  "template": "src/views/orders.html",
  "component": "app/_legacy/orders/OrdersPage.tsx",
  "mappings": [
    { "from": "ng-repeat", "to": "map()" },
    { "from": "ng-click", "to": "onClick" }
  ]
}
4. Recipe: Routing AngularJS → Next.js App Router
4.1. Zakres
Obsługujemy:

$routeProvider (ngRoute):

js
Skopiuj kod
$routeProvider
  .when("/orders", { templateUrl: "orders.html", controller: "OrdersCtrl" })
  .when("/orders/:id", { ... })
  .otherwise({ redirectTo: "/orders" });
ui-router ($stateProvider / $urlRouterProvider):

js
Skopiuj kod
$stateProvider
  .state("orders", { url: "/orders", templateUrl: "orders.html", controller: "OrdersCtrl" })
  .state("orders.detail", { url: "/:id", ... });
4.2. Cel
Generacja:

struktury katalogów w app/:

app/orders/page.tsx

app/orders/[id]/page.tsx

layouty (layout.tsx) dla grup routów.

mapowania parametrów:

:id → [id] w ścieżce,

vm.$stateParams.id → użycie useParams() w Next.

4.3. Wejście
AST definicji routingu:

lista ścieżek (/orders, /orders/:id),

nazwy stanów (orders, orders.detail),

templateUrl,

controller.

Aktualne mappingi template→component (z poprzednich recipe).

4.4. Wyjście
plan migracji:

json
Skopiuj kod
{
  "routes": [
    {
      "legacy": "/orders",
      "nextPath": "/orders",
      "file": "app/orders/page.tsx",
      "sourceController": "OrdersCtrl",
      "sourceTemplate": "orders.html"
    },
    {
      "legacy": "/orders/:id",
      "nextPath": "/orders/[id]",
      "file": "app/orders/[id]/page.tsx",
      "sourceController": "OrderDetailCtrl",
      "sourceTemplate": "order-detail.html"
    }
  ]
}
wygenerowane pliki page.tsx:

importujące odpowiedni komponent przeniesiony z controllera/template,

używające useParams / searchParams dla parametrów i query.

4.5. Zasady mapowania
Parametry ścieżki:

:id → [id],

wiele parametrów – np. /orders/:id/:tab → [id]/[tab] albo [...slug] (do wyboru, konfigurowalne).

Nazwy stanów (ui-router):

orders (url /orders) → app/orders/page.tsx,

orders.detail (url /:id) → app/orders/[id]/page.tsx,

hierarchia stanów → layouty i nested routes (jeśli chcemy skorzystać z nested layouts App Routera).

Redirects:

otherwise({ redirectTo: "/orders" }) → middleware lub redirect() w odpowiednim miejscu (opisane w planie, implementacja może być manualna).

5. Recipe: $scope / $rootScope / $watch → state & hooks
5.1. Zakres
Obsługujemy:

$scope w controllerach i dyrektywach,

$rootScope (globalne eventy / shared state),

$watch, $watchCollection, $watchGroup.

5.2. Strategie mapowania
Lokalny stan componentu:

$scope → useState / useReducer w komponencie.

Globalny/shared state:

$rootScope:

docelowo → Context API (React.createContext + useContext) albo dedykowany store (np. Zustand/Redux) – zależne od konfiguracji.

recipe generuje szkielety contextów / store’ów oraz ostrzeżenia dla patternów trudnych (np. event bus).

Watchery:

$scope.$watch("vm.value", fn):

tsx
Skopiuj kod
const valueRef = useRef(value);
useEffect(() => {
  if (value !== valueRef.current) {
    valueRef.current = value;
    fn(value);
  }
}, [value]);
uproszczona wersja: useEffect(fn, [value]), jeśli brakuje logiki z oldVal.

$watchCollection / $watchGroup:

useEffect z tablicą dependencies,

fallback do JSON.stringify przy braku lepszej heurystyki (z ostrzeżeniem).

5.3. Wejście
Lista użyć:

$scope.$watch(expr, callback, deep?),

$rootScope.$on(eventName, handler),

przypisania do $rootScope.someGlobal.

Kontekst: w jakich controllerach/dyrektywach występuje.

5.4. Wyjście
plan + skeleton kodu w TSX/TS:

hooki w komponencie lokalnym,

definicje contextów/global stores, np.:

tsx
Skopiuj kod
const GlobalContext = createContext<GlobalState | undefined>(undefined);

export function GlobalProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<GlobalState>(/* init from legacy */);
  // TODO: map $rootScope events here
  return <GlobalContext.Provider value={{ state, setState }}>{children}</GlobalContext.Provider>;
}

export function useGlobal() {
  const ctx = useContext(GlobalContext);
  if (!ctx) throw new Error("useGlobal must be used within GlobalProvider");
  return ctx;
}
mapping:

json
Skopiuj kod
{
  "rootScopeEvents": [
    {
      "event": "order:created",
      "source": "OrdersCtrl",
      "targetContext": "GlobalProvider",
      "notes": "Check how many consumers; event-bus pattern – consider refactor."
    }
  ]
}
5.5. Ostrożne miejsca
Recipe powinno oznaczać jako ryzykowne:

masowe $rootScope.$broadcast / $emit – proponować docelowo bardziej jawny przepływ danych,

$watch na złożonych wyrażeniach ("vm.a + vm.b"),

deep: true ($watch('vm.obj', fn, true)).

W raportach Feniksa te przypadki wchodzą do sekcji „High-Risk AngularJS Patterns”.

6. Integracja z Legacy Behavior Guard
Dla każdego z opisanych recipe’ów:

przed migracją:

rejestrujemy scenariusze E2E (Playwright) na starym AngularJS dla krytycznych ekranów,

generujemy BehaviorContract (DOM snapshot + HTTP + logi).

po migracji:

odpalamy te same scenariusze na nowym Next.js,

porównujemy z BehaviorContract:

róznice klasyfikujemy jako:

kosmetyczne (tekst, kolejność),

akceptowalne (poprawa UX),

krytyczne (brak funkcji, inny status HTTP, błędy).

Recipe migracyjne MUSZĄ:

emitować metadane, które pozwolą zmapować:

stary URL → nowy URL,

stary controller/template → nowy komponent/route,

aby Behavior Guard wiedział, gdzie odpalić scenariusze.

7. Priorytety implementacyjne (propozycja)
MVP: controllers + templates + prosty routing

controllers → komponenty Next.js,

template → JSX,

routing /path/:id → app/path/[id]/page.tsx.

bez pełnej obsługi $rootScope i złożonych dyrektyw.

Dyrektywy layoutowe + proste scope

isolate scope → props,

ng-transclude → props.children.

Watchers + $rootScope (konwersja minimalna)

mapowanie $watch → useEffect + TODO,

skeleton global context/stores dla $rootScope.

Zaawansowane dyrektywy i custom filtry

generacja stubów + ostrzeżenia w raportach.

Każdy etap powinien mieć:

testy jednostkowe (input AngularJS → output TSX/TS),

fixture’y z realnych komponentów/ekranów,

integrację z Behavior Guard.
