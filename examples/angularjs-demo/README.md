# AngularJS to Next.js Migration Demo 🚀

This is a **complete, repeatable end-to-end demonstration** of using Feniks to migrate a legacy AngularJS 1.3 application to Next.js 14 with App Router.

## 📋 What's Included

- **Legacy AngularJS 1.3 App**: A fully functional TODO application demonstrating common AngularJS patterns
  - Controller-as syntax
  - $routeProvider routing
  - Services with $http (simulated)
  - Custom filters
  - Templates with ng-directives
  - $scope and $rootScope usage

- **Migration Scripts**: Step-by-step scripts to run Feniks migration recipes
- **Behavior Scenarios**: YAML scenarios for testing migration correctness
- **Reports**: Generated migration reports and behavior test results

## 🎯 Demo Goals

By following this demo, you will:

1. ✅ Run a working AngularJS 1.3 application
2. ✅ Record behavior contracts before migration
3. ✅ Execute Feniks migration recipes automatically
4. ✅ Generate Next.js 14 components with TypeScript
5. ✅ Validate migration correctness with Behavior Guard
6. ✅ See detailed migration reports

## ⚡ Quick Start (10 Commands)

```bash
# 1. Navigate to demo directory
cd examples/angularjs-demo

# 2. Install legacy app dependencies
cd legacy-app && npm install && cd ..

# 3. Run legacy app (opens browser at http://localhost:8080)
cd legacy-app && npm run serve-node

# 4. In another terminal, prepare Feniks
cd ../.. && source venv/bin/activate

# 5. Run the complete migration demo script
python examples/angularjs-demo/migrate.py

# 6. View generated Next.js components
ls -la examples/angularjs-demo/migrated-app/

# 7. View migration report
cat examples/angularjs-demo/reports/migration-report.md

# 8. Run behavior tests
feniks behavior check \
  --project-id todo-app \
  --contracts examples/angularjs-demo/contracts/contracts.jsonl \
  --snapshots examples/angularjs-demo/scenarios/snapshots.jsonl \
  --output examples/angularjs-demo/reports/behavior-results.jsonl

# 9. View behavior test results
cat examples/angularjs-demo/reports/behavior-results.jsonl

# 10. Compare before/after
diff -r legacy-app/js/ migrated-app/
```

## 📚 Detailed Step-by-Step Guide

### Step 1: Understand the Legacy Application

The legacy AngularJS app is a TODO application with the following structure:

```
legacy-app/
├── index.html                          # Main HTML with ng-app
├── js/
│   ├── app.js                         # App config with $routeProvider
│   ├── controllers/
│   │   └── TodoController.js          # Main controller with $scope
│   ├── services/
│   │   └── TodoService.js             # Service with $http (simulated)
│   └── filters/
│       └── TodoFilters.js             # Custom filters
├── views/
│   ├── todo-list.html                 # Template with ng-repeat, ng-if, ng-click
│   └── todo-detail.html               # Detail view template
└── css/
    └── styles.css                     # Styling
```

**Key AngularJS Patterns Demonstrated:**
- `$routeProvider` with route parameters
- Controller-as syntax (`controllerAs: 'vm'`)
- Dependency injection
- `$scope` and `$rootScope`
- `$http` service (simulated with `$timeout`)
- Custom filters (capitalize, priorityLabel, dateFormat)
- ng-directives (ng-repeat, ng-if, ng-model, ng-click, ng-show)
- Route resolve functions
- Event broadcasting with `$broadcast`

**Try it yourself:**
```bash
cd legacy-app
npm install
npm run serve-node
# Visit http://localhost:8080
```

### Step 2: Create Code Inventory

Before migration, we need to parse and understand the codebase structure.

```bash
# Create JSONL inventory of all source files
python scripts/create-inventory.py \
  --source examples/angularjs-demo/legacy-app \
  --output examples/angularjs-demo/inventory.jsonl
```

This creates a structured inventory that Feniks recipes will consume.

### Step 3: Record Behavior Contracts (Optional but Recommended)

Before refactoring, record how the application currently behaves:

```bash
# Record behavior snapshots from the running legacy app
feniks behavior record \
  --project-id todo-app \
  --scenario-id ui-flow \
  --environment legacy \
  --output examples/angularjs-demo/scenarios/legacy-snapshots.jsonl

# Build behavior contracts from snapshots
feniks behavior build-contracts \
  --project-id todo-app \
  --input examples/angularjs-demo/scenarios/legacy-snapshots.jsonl \
  --output examples/angularjs-demo/contracts/contracts.jsonl
```

**What this does:**
- Records HTTP responses, DOM state, console logs
- Creates contracts for expected behavior
- Enables automatic regression detection after migration

### Step 4: Run Migration Recipes

Now run the Feniks migration recipes in sequence:

#### 4a. Controller to Component

```bash
# Run the migration script
python examples/angularjs-demo/scripts/migrate-controllers.py
```

**What happens:**
- Analyzes `TodoController.js` and `TodoDetailController.js`
- Extracts dependencies, methods, state
- Generates Next.js functional components with TypeScript
- Converts `$scope` → `useState`
- Maps DI services → import statements
- Generates lifecycle hooks from `$scope.$on` → `useEffect`

**Output:**
```
migrated-app/app/_legacy/components/
├── TodoComponent.tsx
├── TodoDetailComponent.tsx
└── types.ts
```

#### 4b. Template to JSX

```bash
python examples/angularjs-demo/scripts/migrate-templates.py
```

**What happens:**
- Parses `todo-list.html` and `todo-detail.html`
- Converts ng-directives to JSX:
  - `ng-repeat` → `map()`
  - `ng-if` → `{condition && <element>}`
  - `ng-click` → `onClick`
  - `{{ }}` → `{ }`
- Generates filter utility functions
- Generates JSX/TSX files

**Output:**
```
migrated-app/app/_legacy/components/
├── TodoListView.tsx
├── TodoDetailView.tsx
└── utils/
    └── filters.ts
```

#### 4c. Routing to App Router

```bash
python examples/angularjs-demo/scripts/migrate-routing.py
```

**What happens:**
- Analyzes `$routeProvider` configuration in `app.js`
- Converts routes to Next.js App Router structure:
  - `/todos` → `app/todos/page.tsx`
  - `/todos/:id` → `app/todos/[id]/page.tsx`
- Generates redirects in `middleware.ts`
- Maps route resolve → Server Components

**Output:**
```
migrated-app/app/
├── todos/
│   ├── page.tsx
│   ├── active/
│   │   └── page.tsx
│   ├── completed/
│   │   └── page.tsx
│   └── [id]/
│       └── page.tsx
└── middleware.ts
```

#### 4d. Scope to Hooks Analysis

```bash
python examples/angularjs-demo/scripts/analyze-scope.py
```

**What happens:**
- Analyzes `$scope` and `$rootScope` usage patterns
- Generates `GlobalContext.tsx` boilerplate
- Generates event bus hook (`useEventBus`)
- Creates migration guide document
- **Note**: This is analysis + infrastructure generation, NOT automatic conversion

**Output:**
```
migrated-app/app/_legacy/context/
├── GlobalContext.tsx
├── useEventBus.ts
└── MIGRATION_GUIDE.md
```

#### 4e. Service Migration

```bash
python examples/angularjs-demo/scripts/migrate-services.py
```

**What happens:**
- Analyzes `TodoService.js`
- Generates TypeScript service with fetch/axios
- Converts promises to async/await
- Generates TypeScript interfaces

**Output:**
```
migrated-app/app/_legacy/services/
├── TodoService.ts
└── types.ts
```

### Step 5: Review Generated Code

```bash
# View complete migrated structure
tree migrated-app/

# View a migrated component
cat migrated-app/app/_legacy/components/TodoComponent.tsx

# View migration report
cat reports/migration-report.md
```

**Migration Report includes:**
- Files migrated
- Patterns converted
- Manual work required (TODOs)
- Risk assessment
- Success metrics

### Step 6: Validate with Behavior Guard

After migration, validate that behavior is preserved:

```bash
# Run behavior tests against migrated app
feniks behavior check \
  --project-id todo-app \
  --contracts contracts/contracts.jsonl \
  --snapshots scenarios/migrated-snapshots.jsonl \
  --output reports/behavior-results.jsonl \
  --fail-on-violations

# View results
cat reports/behavior-results.jsonl | jq '.'
```

**What this validates:**
- HTTP responses match contracts
- DOM elements present/absent as expected
- Console errors/warnings within thresholds
- Behavior risk score < threshold

### Step 7: Complete Manual Work

The migration generates TODOs for patterns that require manual work:

```bash
# Find all TODOs in migrated code
grep -r "TODO:" migrated-app/
```

**Common TODOs:**
- Service implementations (convert $http to fetch)
- Complex ng-model patterns
- ng-class dynamic class logic
- Link functions in directives
- Route guards implementation

**Refer to:**
```bash
cat migrated-app/app/_legacy/context/MIGRATION_GUIDE.md
```

### Step 8: Run Migrated Application

```bash
# Install Next.js dependencies
cd migrated-app
npm install

# Run development server
npm run dev

# Visit http://localhost:3000
```

### Step 9: Run Tests

```bash
# Run unit tests for migrated components
cd migrated-app
npm test

# Run E2E tests with Playwright
npm run test:e2e
```

## 📊 Expected Results

### Migration Success Metrics

| Metric | Expected Value |
|--------|----------------|
| **Controllers Migrated** | 2/2 (100%) |
| **Templates Converted** | 2/2 (100%) |
| **Routes Mapped** | 4/4 (100%) |
| **Services Migrated** | 1/1 (100%) |
| **Filters Converted** | 4/4 (100%) |
| **Automation Level** | 70-75% |
| **Manual Work Required** | 25-30% |
| **Behavior Tests Passing** | 95%+ |

### Generated Files

```
migrated-app/
├── app/
│   ├── todos/
│   │   ├── page.tsx                 # Main todos list
│   │   ├── active/page.tsx          # Active filter
│   │   ├── completed/page.tsx       # Completed filter
│   │   └── [id]/page.tsx           # Todo detail
│   ├── layout.tsx
│   └── page.tsx
├── app/_legacy/
│   ├── components/
│   │   ├── TodoComponent.tsx        # Migrated controller
│   │   ├── TodoDetailComponent.tsx
│   │   └── types.ts
│   ├── services/
│   │   ├── TodoService.ts          # Migrated service
│   │   └── types.ts
│   ├── utils/
│   │   └── filters.ts              # Migrated filters
│   └── context/
│       ├── GlobalContext.tsx       # Generated context
│       └── useEventBus.ts          # Generated hook
├── middleware.ts                    # Route redirects
├── package.json
├── tsconfig.json
└── next.config.js
```

## 🔍 Understanding the Migration

### What Gets Automated (70-75%)

✅ **Fully Automated:**
- Basic controller structure → component
- Simple state management ($scope → useState)
- Event handlers (ng-click → onClick)
- Basic routing (routes → app/ structure)
- Filter functions
- TypeScript interface generation
- Import statements
- JSX conversion for simple directives

### What Requires Manual Work (25-30%)

⚠️ **Manual Work Needed:**
- Service implementations ($http → fetch)
- Complex ng-model patterns
- ng-class dynamic classes
- Link functions in directives
- Complex $watch expressions
- Route guards logic
- Resolve functions
- Complex directive compile functions

### Risk Assessment

The migration report includes risk scoring:

| Risk Level | Description | Action |
|------------|-------------|--------|
| **Low (0.0-0.3)** | Mostly automated, minimal manual work | Proceed |
| **Medium (0.3-0.6)** | Some manual work, review generated TODOs | Review carefully |
| **High (0.6-1.0)** | Significant manual work required | Plan additional development time |

## 📝 Migration Report Example

```markdown
# Migration Report: TODO App

**Date**: 2025-11-27
**Duration**: 2.3 seconds
**Success**: ✅ Yes

## Summary

- **Files Analyzed**: 7
- **Files Generated**: 12
- **Patterns Converted**: 45
- **Manual Work Items**: 8
- **Overall Risk**: 0.35 (Medium)

## Controllers Migrated

1. **TodoController** → `TodoComponent.tsx`
   - State: 5 variables converted to useState
   - Methods: 7 methods converted
   - Lifecycle: 2 useEffect hooks generated
   - Risk: 0.3 (Low-Medium)

2. **TodoDetailController** → `TodoDetailComponent.tsx`
   - State: 3 variables converted to useState
   - Methods: 3 methods converted
   - Risk: 0.2 (Low)

## Templates Converted

1. **todo-list.html** → `TodoListView.tsx`
   - ng-repeat: ✅ Converted to map()
   - ng-if: ✅ Converted to conditional rendering
   - ng-click: ✅ Converted to onClick
   - ng-model: ⚠️ TODO - requires controlled components

2. **todo-detail.html** → `TodoDetailView.tsx`
   - Full conversion: ✅ 95% complete

## Manual Work Required

1. **TODO [HIGH]**: Implement fetch calls in TodoService.ts:8
2. **TODO [MEDIUM]**: Convert ng-model to controlled components in TodoListView.tsx:45
3. **TODO [LOW]**: Review event bus usage in GlobalContext.tsx

## Behavior Validation

- **Contracts Created**: 12
- **Tests Passing**: 11/12 (92%)
- **Violations**: 1 (minor - console warning)
- **Risk Score**: 0.15 (Low)
```

## 🎓 Learning Resources

### Understanding Generated Code

Each generated file includes:
- **Header comments**: Explain what was converted
- **TODO markers**: Indicate manual work needed
- **Type definitions**: TypeScript interfaces
- **Migration notes**: Inline comments about conversions

### Common Patterns

#### Before (AngularJS):
```javascript
angular.module('todoApp')
  .controller('TodoController', ['$scope', 'TodoService',
    function($scope, TodoService) {
      $scope.todos = [];

      $scope.loadTodos = function() {
        TodoService.getAllTodos().then(function(todos) {
          $scope.todos = todos;
        });
      };

      $scope.loadTodos();
    }
  ]);
```

#### After (Next.js):
```typescript
'use client';

import { useState, useEffect } from 'react';
import { TodoService } from '@/legacy/services/TodoService';
import type { Todo } from './types';

export default function TodoComponent() {
  const [todos, setTodos] = useState<Todo[]>([]);

  const loadTodos = async () => {
    const todos = await TodoService.getAllTodos();
    setTodos(todos);
  };

  useEffect(() => {
    loadTodos();
  }, []);

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

## 🐛 Troubleshooting

### Issue: Migration script fails

**Solution**: Ensure Feniks is properly installed and Python environment is activated:
```bash
source venv/bin/activate
pip install -e .
```

### Issue: Behavior tests fail

**Solution**: Ensure legacy app is running and accessible:
```bash
curl http://localhost:8080
```

### Issue: Generated code has TypeScript errors

**Solution**: This is expected. Review TODOs and complete manual work:
```bash
grep -r "TODO:" migrated-app/
```

## 📦 Package Contents

```
angularjs-demo/
├── README.md                    # This file
├── legacy-app/                  # Source AngularJS application
├── migrated-app/                # Generated Next.js application
├── scripts/                     # Migration scripts
│   ├── migrate.py              # Main migration script
│   ├── migrate-controllers.py
│   ├── migrate-templates.py
│   ├── migrate-routing.py
│   ├── analyze-scope.py
│   └── create-inventory.py
├── scenarios/                   # Behavior test scenarios
│   ├── scenarios.yaml
│   ├── legacy-snapshots.jsonl
│   └── migrated-snapshots.jsonl
├── contracts/                   # Behavior contracts
│   └── contracts.jsonl
├── reports/                     # Generated reports
│   ├── migration-report.md
│   └── behavior-results.jsonl
└── inventory.jsonl             # Code inventory

```

## 🚀 Next Steps

After completing this demo:

1. ✅ Read the generated migration report
2. ✅ Review generated TypeScript code
3. ✅ Complete manual work items (TODOs)
4. ✅ Run tests and fix any failures
5. ✅ Deploy migrated application

## 💡 Tips

- **Start Small**: Migrate one route at a time
- **Test Incrementally**: Validate after each recipe
- **Review TODOs**: Don't skip manual work items
- **Use Behavior Guard**: Catch regressions early
- **Read Reports**: Migration reports have valuable insights

## 📚 Additional Documentation

- [AngularJS Migration Guide](../../docs/ANGULARJS_MIGRATION.md)
- [Behavior Guard Documentation](../../docs/LEGACY_BEHAVIOR_GUARD.md)
- [Known Limitations](../../docs/ANGULARJS_MIGRATION.md#known-limitations)
- [Recipe Documentation](../../docs/Feniks–Recipe_Pack_AngularJS_1-3.md)

## 🤝 Getting Help

- **Issues**: [GitHub Issues](https://github.com/glesniowski/feniks/issues)
- **Documentation**: [docs/](../../docs/)
- **Examples**: This demo + [docs/examples/](../../docs/examples/)

---

**Feniks Team** - Making Legacy Migration Manageable

🦅 **This demo proves that AngularJS → Next.js migration can be 70-75% automated!**
