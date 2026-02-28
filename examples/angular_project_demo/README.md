# Angular Project Demo

This directory is a placeholder for an Angular project to demonstrate RAE-Feniks analysis capabilities.

## Setup

To use this demo:

### Option 1: Use Your Own Angular Project

```bash
# Point RAE-Feniks to your Angular project
cd /path/to/feniks/examples
PROJECT_ROOT=/path/to/your/angular/project ./run_ingest_and_analyze.sh
```

### Option 2: Create a Sample Angular Project

```bash
# Install Angular CLI
npm install -g @angular/cli

# Create new project
cd angular_project_demo
ng new sample-app --routing --style=scss

# Index and analyze
cd ..
PROJECT_ROOT=./angular_project_demo/sample-app ./run_ingest_and_analyze.sh
```

### Option 3: Clone an Existing Angular Project

```bash
# Clone a sample Angular project
cd angular_project_demo
git clone https://github.com/angular/angular-tour-of-heroes.git
cd ..

# Run analysis
PROJECT_ROOT=./angular_project_demo/angular-tour-of-heroes ./run_ingest_and_analyze.sh
```

## What to Expect

RAE-Feniks will analyze:
- **Components**: Angular components (*.component.ts)
- **Services**: Angular services (*.service.ts)
- **Modules**: NgModules (*.module.ts)
- **Templates**: HTML templates (*.component.html)
- **Routing**: Routing configuration
- **Pipes**: Custom pipes
- **Directives**: Custom directives
- **Guards**: Route guards
- **Interceptors**: HTTP interceptors

## Typical Analysis Results

For a medium-sized Angular app (~50 components, ~30 services):

### System Model
- **Total Modules**: ~80
- **Central Modules**:
  - `app.module.ts` (main module)
  - `core.module.ts` (core services)
  - `shared.module.ts` (shared components)
  - `auth.service.ts` (authentication)
  - `api.service.ts` (API communication)

- **Capabilities Detected**:
  - UI components (Angular components)
  - REST API (HttpClient usage)
  - Authentication (AuthService, guards)
  - Routing (Router, routes)
  - State management (if using NgRx/Akita)
  - Form handling (Reactive/Template forms)

### Common Meta-Reflections

1. **Component Complexity**
   ```
   DashboardComponent has high complexity (15) due to mixing
   business logic with presentation. Consider extracting logic
   to a service.
   ```

2. **Service Coupling**
   ```
   Circular dependency detected: AuthService ↔ UserService.
   This makes testing difficult and violates single responsibility.
   ```

3. **Template Complexity**
   ```
   dashboard.component.html has complex *ngIf chains.
   Consider using ng-container or extracting sub-components.
   ```

4. **Missing Error Handling**
   ```
   HTTP calls in ApiService don't handle errors consistently.
   Implement a centralized error handler or HttpInterceptor.
   ```

5. **Unused Imports**
   ```
   Module imports CommonModule but doesn't use any directives.
   Remove unused imports to reduce bundle size.
   ```

## Sample Refactorings

### 1. Extract Service Logic

**Before**:
```typescript
export class DashboardComponent {
  loadData() {
    this.http.get('/api/dashboard').subscribe(data => {
      this.processData(data);
      this.calculateMetrics(data);
      this.updateCharts(data);
    });
  }

  private processData(data: any) { /* ... */ }
  private calculateMetrics(data: any) { /* ... */ }
  private updateCharts(data: any) { /* ... */ }
}
```

**After**:
```typescript
// dashboard.component.ts
export class DashboardComponent {
  constructor(private dashboardService: DashboardService) {}

  loadData() {
    this.dashboardService.loadData().subscribe(data => {
      this.data = data;
    });
  }
}

// dashboard.service.ts
export class DashboardService {
  loadData() {
    return this.http.get('/api/dashboard').pipe(
      map(data => this.processData(data)),
      tap(data => this.calculateMetrics(data))
    );
  }
}
```

### 2. Break Circular Dependencies

**Before**:
```typescript
// auth.service.ts
import { UserService } from './user.service';

export class AuthService {
  constructor(private userService: UserService) {}
}

// user.service.ts
import { AuthService } from './auth.service';

export class UserService {
  constructor(private authService: AuthService) {}
}
```

**After**:
```typescript
// auth.interface.ts
export interface IAuthService {
  isAuthenticated(): boolean;
  getToken(): string;
}

// auth.service.ts
export class AuthService implements IAuthService { /* ... */ }

// user.service.ts
export class UserService {
  constructor(@Inject('IAuthService') private auth: IAuthService) {}
}
```

## Metrics to Watch

After refactoring, track these metrics:

1. **Complexity Reduction**: Target 20-30% reduction
2. **Dependency Depth**: Should be ≤ 3 levels
3. **Bundle Size**: Watch for size increases
4. **Test Coverage**: Maintain or increase coverage
5. **Build Time**: Should not significantly increase

## Running Tests After Refactoring

```bash
cd /path/to/angular/project

# Unit tests
ng test

# E2E tests
ng e2e

# Build (production)
ng build --prod

# Check bundle size
du -sh dist/
```

## Best Practices for Angular Projects

1. **Keep components thin**: Move logic to services
2. **Use smart/dumb pattern**: Container components + presentational components
3. **Lazy load modules**: Reduce initial bundle size
4. **Implement OnPush**: Improve change detection performance
5. **Use trackBy**: For *ngFor with large lists
6. **Unsubscribe properly**: Use takeUntil or async pipe
7. **Type your data**: Avoid `any`, use interfaces
8. **Handle errors globally**: Use HttpInterceptor

## Next Steps

1. Run the demo script: `./run_ingest_and_analyze.sh`
2. Review meta-reflections in `feniks_output/meta_reflections.jsonl`
3. Examine the system model in `feniks_output/analysis_report.txt`
4. Try refactoring recipes: `feniks refactor --list-recipes`
5. Read the [Angular Style Guide](https://angular.io/guide/styleguide)

## Resources

- [Angular Documentation](https://angular.io/docs)
- [Angular Style Guide](https://angular.io/guide/styleguide)
- [RAE-Feniks Documentation](../../docs/)
- [Enterprise Refactoring Guide](../../docs/ENTERPRISE_REFACTORING.md)

Happy Angular refactoring! 🎯
