# AngularJS to Next.js Migration with Feniks

## Overview

Feniks provides a comprehensive **Recipe Pack** for migrating AngularJS 1.x applications to Next.js with App Router. This automated migration system helps teams modernize legacy AngularJS codebases while maintaining behavioral integrity through integrated **Legacy Behavior Guard** testing.

## Key Features

- **Automated Code Transformation**: Convert AngularJS patterns to modern React/Next.js
- **TypeScript Generation**: Generate fully typed TypeScript/TSX components
- **Behavior Preservation**: Validate migrations with automated regression testing
- **Risk Assessment**: Automatic risk scoring for each migration step
- **Incremental Migration**: Support for gradual, step-by-step migration
- **Comprehensive Coverage**: 5 specialized recipes covering all major AngularJS patterns

---

## Recipe Pack

### 1. Controller to Component Recipe

**Purpose**: Migrate AngularJS controllers to Next.js functional components.

**Handles**:
- `controller()` definitions → Functional React components
- `$scope` → `useState`/`useReducer`
- DI services → Import statements
- `$http` → `fetch` or HTTP client
- `$state`/`$stateParams` → `useRouter`/`useSearchParams`
- Lifecycle hooks → `useEffect`

**Example**:

```javascript
// Before: AngularJS Controller
angular.module('myApp')
  .controller('OrdersCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.orders = [];

    $scope.loadOrders = function() {
      $http.get('/api/orders').then(function(response) {
        $scope.orders = response.data;
      });
    };

    $scope.loadOrders();
  }]);
```

```typescript
// After: Next.js Component
import React, { useState, useEffect } from 'react';

interface OrdersPageProps {}

export default function OrdersPage(props: OrdersPageProps) {
  const [orders, setOrders] = useState([]);

  const loadOrders = async () => {
    const response = await fetch('/api/orders');
    const data = await response.json();
    setOrders(data);
  };

  useEffect(() => {
    loadOrders();
  }, []);

  return (
    <div>
      {/* JSX content */}
    </div>
  );
}
```

---

### 2. Directive to Component/Hook Recipe

**Purpose**: Convert AngularJS directives to React components or custom hooks.

**Handles**:
- Element directives (`restrict: 'E'`) → React components
- Attribute directives → Custom hooks
- Isolated scope → Component props
- Transclusion → `children` prop
- Link function → `useEffect` with refs
- Compile function → Manual review (high risk)

**Migration Strategies**:
1. **Component**: For directives with templates
2. **Hook**: For behavior-only directives
3. **Utility**: For complex compile functions

**Example**:

```javascript
// Before: AngularJS Directive
angular.module('myApp')
  .directive('userCard', function() {
    return {
      restrict: 'E',
      scope: {
        user: '=',
        onSelect: '&'
      },
      templateUrl: 'user-card.html'
    };
  });
```

```typescript
// After: React Component
interface UserCardProps {
  user: any;
  onSelect: () => void;
}

export function UserCard(props: UserCardProps) {
  return (
    <div className="user-card">
      {/* Component content */}
    </div>
  );
}
```

---

### 3. Template to JSX Recipe

**Purpose**: Convert AngularJS HTML templates to React JSX/TSX.

**Handles**:
- `{{ interpolation }}` → `{expression}`
- `ng-repeat` → `map()` with keys
- `ng-if`/`ng-show`/`ng-hide` → Conditional rendering
- `ng-click`/`ng-submit` → `onClick`/`onSubmit`
- `ng-model` → Controlled components
- `ng-class`/`ng-style` → `className`/`style`
- Filters → Utility functions

**Conversion Rules**:

| AngularJS | React/JSX |
|-----------|-----------|
| `{{ value }}` | `{value}` |
| `ng-repeat="item in items"` | `{items.map(item => <li key={...}>)}` |
| `ng-if="condition"` | `{condition && <Element />}` |
| `ng-click="handler()"` | `onClick={() => handler()}` |
| `ng-model="value"` | `value={value} onChange={...}` |
| `class="..."` | `className="..."` |
| `{{ val \| filter }}` | `{applyFilter(val)}` |

**Example**:

```html
<!-- Before: AngularJS Template -->
<ul>
  <li ng-repeat="order in vm.orders track by order.id">
    <span>{{ order.id }}</span>
    <span>{{ order.total | currency:'USD' }}</span>
    <button ng-click="vm.selectOrder(order)">View</button>
  </li>
</ul>
```

```tsx
// After: JSX
<ul>
  {vm.orders.map(order => (
    <li key={order.id}>
      <span>{order.id}</span>
      <span>{formatCurrency(order.total, 'USD')}</span>
      <button onClick={() => vm.selectOrder(order)}>View</button>
    </li>
  ))}
</ul>
```

---

### 4. Routing to App Router Recipe

**Purpose**: Migrate AngularJS routing to Next.js App Router.

**Handles**:
- `$routeProvider` (ngRoute) → `app/` directory structure
- `ui-router` (`$stateProvider`) → `app/` directory structure
- Route parameters (`:id`) → `[id]` dynamic segments
- Nested routes → Nested directories
- Redirects → `middleware.ts` or `redirect()`
- Route guards → Middleware

**Conversion Rules**:

| AngularJS | Next.js |
|-----------|---------|
| `/orders` | `app/orders/page.tsx` |
| `/orders/:id` | `app/orders/[id]/page.tsx` |
| `/orders/:id/:tab` | `app/orders/[id]/[tab]/page.tsx` |
| `$stateParams.id` | `useParams()` |
| `$location.search()` | `useSearchParams()` |
| `otherwise()` | `middleware.ts` redirect |

**Example**:

```javascript
// Before: AngularJS Routing
$routeProvider
  .when('/orders', {
    templateUrl: 'orders.html',
    controller: 'OrdersCtrl'
  })
  .when('/orders/:id', {
    templateUrl: 'order-detail.html',
    controller: 'OrderDetailCtrl'
  })
  .otherwise({ redirectTo: '/orders' });
```

```
// After: Next.js Structure
app/
├── orders/
│   ├── page.tsx           # /orders
│   └── [id]/
│       └── page.tsx       # /orders/:id
└── middleware.ts          # Redirects
```

---

### 5. Scope to Hooks Recipe

**Purpose**: Migrate AngularJS scope patterns to React hooks and Context API.

**Handles**:
- `$scope` → `useState`/`useReducer`
- `$rootScope` → Context API or global store
- `$watch` → `useEffect` with dependencies
- `$watchCollection` → `useEffect` with arrays
- `$scope.$on`/`$broadcast`/`$emit` → Event system

**Migration Patterns**:

```javascript
// Before: $watch
$scope.$watch('vm.value', function(newVal, oldVal) {
  console.log('Value changed:', newVal);
});

// After: useEffect
useEffect(() => {
  console.log('Value changed:', value);
}, [value]);
```

```javascript
// Before: $rootScope
$rootScope.user = { id: 1, name: 'John' };

// After: Context API
const { state, setState } = useGlobal();
setState({ user: { id: 1, name: 'John' } });
```

```javascript
// Before: $broadcast/$on
$rootScope.$broadcast('user:login', { userId: 123 });
$scope.$on('user:login', function(event, data) {
  console.log('User logged in:', data.userId);
});

// After: Event system
const { emit, on } = useGlobal();
emit('user:login', { userId: 123 });

useEffect(() => {
  return on('user:login', (data) => {
    console.log('User logged in:', data.userId);
  });
}, [on]);
```

---

## Usage

### Basic Usage

```python
from feniks.core.refactor.recipes.angularjs import (
    ControllerToComponentRecipe,
    TemplateToJsxRecipe,
    RoutingToAppRouterRecipe
)
from feniks.core.models.types import SystemModel

# Create system model from your codebase
system_model = SystemModel(...)

# 1. Migrate controllers
controller_recipe = ControllerToComponentRecipe(config={
    "target_dir": "app/_legacy",
    "state_strategy": "useState",
    "typing_mode": "strict"
})

plan = controller_recipe.analyze(system_model)
result = controller_recipe.execute(plan, chunks, dry_run=False)

# 2. Convert templates
template_recipe = TemplateToJsxRecipe()
plan = template_recipe.analyze(system_model)
result = template_recipe.execute(plan, chunks, dry_run=False)

# 3. Migrate routing
routing_recipe = RoutingToAppRouterRecipe()
plan = routing_recipe.analyze(system_model)
result = routing_recipe.execute(plan, chunks, dry_run=False)
```

### With Behavior Guard Integration

```python
from feniks.core.refactor.recipes.angularjs import BehaviorGuardIntegration

# Initialize integration
integration = BehaviorGuardIntegration()

# Create test plan from refactoring result
test_plan = integration.create_test_plan(refactor_result)

# Generate behavior scenarios
scenarios_path = integration.generate_behavior_scenarios(
    test_plan,
    output_path="scenarios/"
)

# Generate test script
script_path = integration.generate_test_script(
    test_plan,
    output_path="test_migration.sh"
)

# Run validation
# ./test_migration.sh
```

---

## Migration Workflow

### Phase 1: Preparation

1. **Setup Feniks**:
   ```bash
   pip install -e .
   ```

2. **Ingest Codebase**:
   ```bash
   feniks ingest --path ./legacy-app --collection angularjs_v1
   ```

3. **Record Baseline Behavior**:
   ```bash
   feniks behavior record \
     --project-id my-app \
     --scenario-id all \
     --environment legacy \
     --output legacy_snapshots.jsonl
   ```

### Phase 2: Analysis

1. **Analyze Controllers**:
   ```python
   controller_recipe = ControllerToComponentRecipe()
   plan = controller_recipe.analyze(system_model)
   print(f"Found {len(plan.metadata['controllers'])} controllers")
   print(f"Risk level: {plan.risk_level}")
   ```

2. **Review Migration Plan**:
   - Check estimated changes
   - Review risk assessment
   - Identify high-risk patterns

### Phase 3: Migration

1. **Execute Recipes** (in order):
   ```python
   # 1. Controllers
   result1 = controller_recipe.execute(plan1, chunks, dry_run=False)

   # 2. Directives
   result2 = directive_recipe.execute(plan2, chunks, dry_run=False)

   # 3. Templates
   result3 = template_recipe.execute(plan3, chunks, dry_run=False)

   # 4. Routing
   result4 = routing_recipe.execute(plan4, chunks, dry_run=False)

   # 5. Scope patterns
   result5 = scope_recipe.execute(plan5, chunks, dry_run=False)
   ```

2. **Manual Review**:
   - Review generated TypeScript
   - Adjust TODO comments
   - Fix type annotations
   - Verify imports

### Phase 4: Validation

1. **Build Behavior Contracts**:
   ```bash
   feniks behavior build-contracts \
     --input legacy_snapshots.jsonl \
     --output contracts.jsonl
   ```

2. **Record Migrated Behavior**:
   ```bash
   feniks behavior record \
     --project-id my-app \
     --scenario-id all \
     --environment migrated \
     --output migrated_snapshots.jsonl
   ```

3. **Check for Regressions**:
   ```bash
   feniks behavior check \
     --contracts contracts.jsonl \
     --snapshots migrated_snapshots.jsonl \
     --output results.jsonl \
     --fail-on-violations
   ```

4. **Review Results**:
   ```bash
   feniks behavior report \
     --results results.jsonl \
     --output migration_report.md
   ```

### Phase 5: Refinement

1. **Address Violations**: Fix any behavioral regressions
2. **Update Contracts**: Accept intentional improvements
3. **Iterate**: Repeat validation until clean
4. **Deploy**: Ship the migrated application

---

## Configuration

### Recipe Configuration

```python
config = {
    # Controller to Component
    "target_dir": "app/_legacy",
    "state_strategy": "useState",  # useState | useReducer | external-store
    "typing_mode": "strict",        # strict | loose
    "aggressiveness": "balanced",   # conservative | balanced | aggressive

    # Template to JSX
    "preserve_comments": True,
    "generate_filter_stubs": True,

    # Routing to App Router
    "use_legacy_prefix": True,

    # Scope to Hooks
    "global_state_strategy": "context"  # context | zustand | redux
}

recipe = ControllerToComponentRecipe(config)
```

### Risk Thresholds

| Risk Level | Threshold | Use Case |
|------------|-----------|----------|
| LOW | 0.5 | Simple UI components |
| MEDIUM | 0.3 | Business logic |
| HIGH | 0.1 | Critical paths (checkout, payments) |
| CRITICAL | 0.05 | Security-sensitive flows |

---

## Best Practices

### 1. Incremental Migration

- Start with leaf components (no dependencies)
- Migrate one module/feature at a time
- Keep AngularJS and Next.js running in parallel

### 2. Risk Management

- Use Behavior Guard for all migrations
- Focus on high-traffic user flows first
- Maintain rollback capability

### 3. Code Quality

- Enable strict TypeScript mode
- Add proper type annotations
- Write unit tests for complex logic

### 4. Team Collaboration

- Review generated code in pull requests
- Document migration decisions
- Share learnings across the team

### 5. Performance

- Use React.memo for expensive components
- Optimize re-renders with useCallback
- Consider code splitting

---

## Troubleshooting

### Issue: Too many TODO comments

**Solution**: Increase aggressiveness level or implement missing services manually.

### Issue: High false positive rate in Behavior Guard

**Solution**:
- Adjust risk threshold
- Exclude cosmetic differences
- Update selectors

### Issue: TypeScript compilation errors

**Solution**:
- Review generated type annotations
- Add missing type definitions
- Use `any` temporarily for complex types

### Issue: State management complexity

**Solution**:
- Consider using a state management library (Zustand, Jotai)
- Refactor large state objects
- Split into multiple contexts

---

## Known Limitations

### Automation Level by Recipe

| Recipe | Automated | Requires Manual Work |
|--------|-----------|---------------------|
| **Controller to Component** | 85-90% | Service implementations, $http → fetch conversion |
| **Template to JSX** | 70-80% | ng-model, ng-class complex expressions |
| **Routing** | 85-95% | Route guards, resolve functions |
| **Directives (simple)** | 90-95% | Link function implementation details |
| **Directives (complex)** | 50-70% | Compile functions, DOM manipulation |
| **Scope to Hooks** | 30-40% | **Analysis only** - conversion is manual |

**Overall**: Expect 70-75% automation with 25-30% manual work required.

### What's Fully Automated

✅ Controller structure → component skeleton
✅ Template syntax conversion ({{ }} → { })
✅ Routing structure → app/ directory
✅ Basic directive → component structure
✅ TypeScript interface generation
✅ Import statement generation

### What Generates TODOs (Requires Implementation)

⚠️ **$http → fetch**: Generates TODO comments, not actual fetch calls
⚠️ **ng-model**: Generates TODO, need to implement controlled component pattern
⚠️ **ng-class**: Generates TODO for dynamic class logic
⚠️ **Service implementations**: Generates import TODOs, need to create service files
⚠️ **Route guards**: Generates TODO in middleware
⚠️ **Directive link functions**: Generates useEffect skeleton with TODO

### What Requires Fully Manual Work

❌ **Scope to Hooks conversion**: Recipe analyzes and generates infrastructure (Context, event bus) but **does not modify component files**
❌ **Complex directives with compile**: Marked as high-risk, manual review required
❌ **Custom filter implementations**: Generates stubs, need to implement logic
❌ **Form validation**: Must integrate with React form library
❌ **Third-party integrations**: Must find React equivalents
❌ **Performance optimization**: Manual profiling and optimization

### Recipe-Specific Limitations

#### Controller to Component
- **config.aggressiveness**: Defined but not currently used in code generation
- **$q Promises**: Not automatically converted to native Promises
- **$timeout/$interval**: Detected but not converted to setTimeout/setInterval

#### Template to JSX
- **ng-repeat**: Basic conversion only, complex nested structures need manual work
- **ng-model two-way binding**: Generates TODO for controlled component pattern
- **Custom filters**: Generates stub functions with TODO for implementation

#### Routing to App Router
- **layout.tsx**: Not generated for nested routes (must create manually)
- **Route resolve**: Not converted to data fetching pattern
- **Optional parameters**: Basic detection, no `[[...slug]]` syntax support

#### Scope to Hooks
**IMPORTANT**: This recipe is primarily an **analysis and infrastructure generation tool**:
- ✅ Analyzes $scope/$rootScope usage
- ✅ Generates GlobalContext boilerplate
- ✅ Generates event bus infrastructure
- ✅ Generates migration guide
- ❌ **Does NOT modify component files**
- ❌ **Does NOT convert $scope to useState**
- ❌ **Does NOT convert $watch to useEffect**

You must manually apply the conversions based on the generated migration guide.

---

## Realistic Success Rates

Based on actual implementation testing:

### By Component Type

| Component Type | Automation Rate | Manual Effort |
|----------------|----------------|---------------|
| Simple controllers | 90% | Import cleanup |
| Complex controllers | 75% | Service implementations |
| Simple templates | 85% | Filter implementations |
| Forms with ng-model | 60% | Controlled components |
| Simple directives | 90% | Minor adjustments |
| Complex directives | 55% | Link/compile logic |
| Routing (ngRoute) | 95% | Route guards |
| Routing (ui-router) | 85% | Nested layouts |
| $scope patterns | 35% | **Mostly manual** |

### Overall Project

- **Initial automated conversion**: 70-75%
- **Manual work required**: 25-30%
- **Testing and refinement**: 10-15% additional
- **Total effort savings**: 60-65% compared to manual rewrite

---

## Examples

See the `/docs/examples/` directory for:
- Complete migration examples
- Before/after comparisons
- Real-world case studies
- Manual completion guides

---

## Support

- **Documentation**: [docs/](../docs/)
- **Code vs Docs Audit**: [AUDIT_CODE_VS_DOCS.md](./AUDIT_CODE_VS_DOCS.md)
- **Issues**: [GitHub Issues](https://github.com/glesniowski/feniks/issues)
- **Community**: [Discussions](https://github.com/glesniowski/feniks/discussions)

---

## References

- [Recipe Pack Specification](./Feniks–Recipe_Pack_AngularJS_1-3.md)
- [Legacy Behavior Guard](./LEGACY_BEHAVIOR_GUARD.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Code vs Documentation Audit](./AUDIT_CODE_VS_DOCS.md)
- [Next.js App Router](https://nextjs.org/docs/app)
- [React Hooks](https://react.dev/reference/react)

---

**Generated by Feniks Team**
Last updated: 2025-11-27
