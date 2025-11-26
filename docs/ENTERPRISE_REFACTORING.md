# Enterprise Refactoring with RAE-Feniks

## Introduction

RAE-Feniks provides enterprise-grade refactoring workflows that are:
- **Safe**: Dry-run by default with risk assessment
- **Systematic**: Recipe-based approach for consistency
- **Auditable**: Full rationale and validation steps
- **Reversible**: Unified diff patches for easy rollback

This guide explains how to use and extend refactoring workflows.

## Core Concepts

### Refactoring Recipes

A **recipe** is a reusable, parameterized refactoring workflow with three phases:

1. **Analyze**: Identify refactoring opportunities
2. **Execute**: Generate code changes (patches)
3. **Validate**: Verify correctness and safety

### Risk Levels

Every refactoring has a risk assessment:

| Risk Level | Description | Examples |
|------------|-------------|----------|
| `LOW` | Safe, well-tested transformations | Rename variable, extract constant |
| `MEDIUM` | Requires careful review | Extract function, reduce complexity |
| `HIGH` | Significant architectural changes | Split module, refactor inheritance |
| `CRITICAL` | System-wide impact | Change API contract, database schema |

### Dry-Run Mode

By default, all refactorings run in **dry-run mode**:
- Generates patches without modifying files
- Allows review before applying
- Safe exploration of refactoring options

## Built-in Recipes

### 1. Reduce Complexity

**Purpose**: Reduce cyclomatic complexity in high-complexity modules

**Criteria**: Targets modules with complexity > 1.5x system average

**Risk Level**: MEDIUM

**Usage**:
```bash
feniks refactor \
  --recipe reduce_complexity \
  --project-id my_project \
  --collection my_project \
  --dry-run
```

**Example Output**:
```
================================================================================
Refactoring: reduce_complexity
================================================================================
Status: ✓ Success
Risk: MEDIUM

Rationale: Identified 5 modules with complexity above 1.5x system average (6.75)

Files changed: 5
  - src/app/services/auth.service.ts (complexity 12 → 6)
  - src/app/components/dashboard.component.ts (complexity 11 → 5)
  - src/app/utils/data-processor.ts (complexity 10 → 5)

Next steps:
  - Review the generated patch carefully
  - Run your test suite: npm test
  - Check type safety: npm run typecheck
  - Apply patch: git apply refactor_reduce_complexity.patch
================================================================================
```

### 2. Extract Function

**Purpose**: Extract long or complex code into separate functions

**Criteria**:
- Cyclomatic complexity > 10, OR
- Line count > 50, OR
- Dependency count > 5

**Risk Level**: LOW

**Usage**:
```bash
feniks refactor \
  --recipe extract_function \
  --project-id my_project \
  --collection my_project \
  --target-module auth \
  --dry-run
```

**What It Does**:
- Identifies long methods/functions
- Extracts cohesive blocks into new functions
- Updates call sites
- Preserves behavior

**Example Transformation**:

Before:
```typescript
class AuthService {
  login(username: string, password: string): Token {
    // Hash password
    const salt = bcrypt.genSaltSync(10);
    const hash = bcrypt.hashSync(password, salt);

    // Query database
    const user = this.db.findUser(username);
    if (!user || user.passwordHash !== hash) {
      throw new Error('Invalid credentials');
    }

    // Generate token
    const payload = { userId: user.id, role: user.role };
    const token = jwt.sign(payload, SECRET, { expiresIn: '24h' });

    // Log audit
    this.auditLog.record('login', user.id);

    return token;
  }
}
```

After:
```typescript
class AuthService {
  login(username: string, password: string): Token {
    const hash = this.hashPassword(password);
    const user = this.authenticateUser(username, hash);
    const token = this.generateToken(user);
    this.logAudit('login', user.id);
    return token;
  }

  private hashPassword(password: string): string {
    const salt = bcrypt.genSaltSync(10);
    return bcrypt.hashSync(password, salt);
  }

  private authenticateUser(username: string, hash: string): User {
    const user = this.db.findUser(username);
    if (!user || user.passwordHash !== hash) {
      throw new Error('Invalid credentials');
    }
    return user;
  }

  private generateToken(user: User): Token {
    const payload = { userId: user.id, role: user.role };
    return jwt.sign(payload, SECRET, { expiresIn: '24h' });
  }

  private logAudit(action: string, userId: string): void {
    this.auditLog.record(action, userId);
  }
}
```

## Refactoring Workflow

### Step 1: List Available Recipes

```bash
feniks refactor --list-recipes
```

Output shows all recipes with descriptions and risk levels.

### Step 2: Analyze Opportunities

Run analysis to identify refactoring opportunities:

```bash
feniks analyze \
  --project-id my_project \
  --collection my_project \
  --meta-reflections reflections.jsonl
```

Review meta-reflections for suggestions:

```bash
cat reflections.jsonl | jq 'select(.tags | contains(["refactoring-opportunity"]))'
```

### Step 3: Run Dry-Run Refactoring

Execute recipe in dry-run mode:

```bash
feniks refactor \
  --recipe reduce_complexity \
  --project-id my_project \
  --collection my_project \
  --output refactor_output \
  --dry-run
```

This generates:
- `refactor_output/refactor_reduce_complexity.patch` - Unified diff patch
- `refactor_output/refactor_report_reduce_complexity.md` - Detailed report

### Step 4: Review the Patch

```bash
cat refactor_output/refactor_reduce_complexity.patch
```

Example patch:
```diff
--- a/src/services/auth.service.ts
+++ b/src/services/auth.service.ts
@@ -15,20 +15,28 @@
 class AuthService {
-  login(username: string, password: string): Token {
-    const salt = bcrypt.genSaltSync(10);
-    const hash = bcrypt.hashSync(password, salt);
-    const user = this.db.findUser(username);
-    if (!user || user.passwordHash !== hash) {
-      throw new Error('Invalid credentials');
-    }
-    const payload = { userId: user.id, role: user.role };
-    const token = jwt.sign(payload, SECRET, { expiresIn: '24h' });
-    this.auditLog.record('login', user.id);
+  login(username: string, password: string): Token {
+    const hash = this.hashPassword(password);
+    const user = this.authenticateUser(username, hash);
+    const token = this.generateToken(user);
+    this.logAudit('login', user.id);
     return token;
   }
+
+  private hashPassword(password: string): string {
+    const salt = bcrypt.genSaltSync(10);
+    return bcrypt.hashSync(password, salt);
+  }
+  ...
```

### Step 5: Run Tests

Before applying, run your test suite:

```bash
# Save current state
git stash

# Apply patch to test branch
git checkout -b refactor/reduce-complexity
git apply refactor_output/refactor_reduce_complexity.patch

# Run tests
npm test
npm run typecheck
npm run lint

# If tests pass, commit
git add .
git commit -m "refactor: reduce complexity in auth module"

# If tests fail, investigate and fix
```

### Step 6: Apply Changes

If tests pass, merge the changes:

```bash
git checkout main
git merge refactor/reduce-complexity
```

## Refactoring Report

Each refactoring generates a detailed report:

```markdown
# Refactoring Report: reduce_complexity

## Summary
- **Recipe**: reduce_complexity
- **Project**: my_project
- **Status**: ✓ Success
- **Risk Level**: MEDIUM
- **Date**: 2025-11-26T10:30:00Z

## Rationale
Identified 5 modules with complexity above 1.5x system average (6.75):
- auth.service.ts: 12 (1.78x)
- dashboard.component.ts: 11 (1.63x)
- data-processor.ts: 10 (1.48x)

## Changes Applied

### src/services/auth.service.ts
- Extracted `hashPassword()` method
- Extracted `authenticateUser()` method
- Extracted `generateToken()` method
- Extracted `logAudit()` method
- **Complexity**: 12 → 6 (50% reduction)

### src/components/dashboard.component.ts
- Extracted `loadUserData()` method
- Extracted `refreshDashboard()` method
- **Complexity**: 11 → 5 (55% reduction)

## Validation Steps
1. ✓ Run unit tests: `npm test`
2. ✓ Run integration tests: `npm run test:e2e`
3. ✓ Check TypeScript compilation: `npm run typecheck`
4. ✓ Verify linting: `npm run lint`
5. ✓ Manual smoke test of login flow
6. ✓ Review code coverage (should remain ≥ current)

## Risks
- **Medium Risk**: Extracted methods change call graph
- **Mitigation**: All original tests should still pass
- **Rollback**: `git revert <commit-sha>`

## Meta-Reflection
This refactoring reduces complexity by extracting cohesive blocks of logic into well-named private methods. This improves:
- **Readability**: Each method has a single, clear purpose
- **Testability**: Individual methods can be tested in isolation
- **Maintainability**: Changes to password hashing only affect one method

## Lessons Learned
- Auth logic was mixing concerns (hashing, validation, token generation)
- Extraction improved testability significantly
- No behavior changes, all tests passed
```

## Targeting Specific Modules

To refactor a specific module:

```bash
feniks refactor \
  --recipe reduce_complexity \
  --project-id my_project \
  --collection my_project \
  --target-module auth \
  --dry-run
```

This focuses the refactoring on the `auth` module only.

## Custom Recipes

You can create custom refactoring recipes by extending the `RefactorRecipe` base class.

### Recipe Structure

```python
from typing import Optional, List, Dict, Any
from feniks.refactor.recipe import RefactorRecipe, RefactorPlan, RefactorResult, RefactorRisk
from feniks.types import SystemModel, Chunk

class MyCustomRecipe(RefactorRecipe):
    @property
    def name(self) -> str:
        return "my_custom_recipe"

    @property
    def description(self) -> str:
        return "Description of what this recipe does"

    @property
    def default_risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(
        self,
        system_model: SystemModel,
        target: Optional[Dict[str, Any]] = None
    ) -> Optional[RefactorPlan]:
        """
        Analyze the system and identify refactoring opportunities.

        Returns:
            RefactorPlan if opportunities found, None otherwise
        """
        # 1. Analyze system model
        # 2. Identify modules/chunks that need refactoring
        # 3. Calculate risk level
        # 4. Generate refactoring plan

        if no_opportunities:
            return None

        return RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=["module1", "module2"],
            target_files=["file1.ts", "file2.ts"],
            rationale="Why this refactoring is needed",
            risks=["Risk 1", "Risk 2"],
            risk_level=RefactorRisk.MEDIUM,
            estimated_changes=5,
            validation_steps=[
                "Run unit tests",
                "Check type safety",
                "Manual smoke test"
            ]
        )

    def execute(
        self,
        plan: RefactorPlan,
        chunks: List[Chunk],
        dry_run: bool = True
    ) -> RefactorResult:
        """
        Execute the refactoring based on the plan.

        Returns:
            RefactorResult with success/failure and changes
        """
        # 1. Filter chunks based on plan.target_files
        # 2. Apply transformations to each chunk
        # 3. Generate file changes
        # 4. Return result

        file_changes = []
        for chunk in target_chunks:
            # Transform chunk content
            new_content = self._transform(chunk.content)

            file_changes.append(FileChange(
                file_path=chunk.file_path,
                old_content=chunk.content,
                new_content=new_content,
                change_type="modify"
            ))

        return RefactorResult(
            plan=plan,
            success=True,
            changes=file_changes,
            meta_reflection={
                "rationale": plan.rationale,
                "outcome": "Successfully refactored N modules",
                "lessons_learned": "Key insights from this refactoring"
            }
        )

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the refactoring result.

        Returns:
            True if validation passes, False otherwise
        """
        # 1. Check that changes are well-formed
        # 2. Verify no syntax errors
        # 3. Validate against business rules

        return True
```

### Registering Custom Recipes

```python
from feniks.refactor.refactor_engine import RefactorEngine

engine = RefactorEngine()
engine.register_recipe(MyCustomRecipe())

# Now available via CLI
# feniks refactor --recipe my_custom_recipe ...
```

## Best Practices

### 1. Always Dry-Run First

Never apply refactorings directly to main branch:

```bash
# ✓ Good
feniks refactor --recipe reduce_complexity --dry-run

# ✗ Bad
feniks refactor --recipe reduce_complexity --no-dry-run
```

### 2. Test Thoroughly

After applying patch, run comprehensive tests:

```bash
# Unit tests
npm test

# Integration tests
npm run test:e2e

# Type checking
npm run typecheck

# Linting
npm run lint

# Coverage (should not decrease)
npm run test:coverage
```

### 3. Incremental Refactoring

Refactor incrementally, not all at once:

```bash
# ✓ Good: One module at a time
feniks refactor --recipe reduce_complexity --target-module auth
# Review, test, commit
feniks refactor --recipe reduce_complexity --target-module api
# Review, test, commit

# ✗ Bad: Everything at once
feniks refactor --recipe reduce_complexity
# Too many changes to review safely
```

### 4. Use Feature Branches

Always refactor on feature branches:

```bash
git checkout -b refactor/reduce-complexity
feniks refactor --recipe reduce_complexity --dry-run
git apply refactor_output/*.patch
npm test
git commit -m "refactor: reduce complexity"
git push origin refactor/reduce-complexity
# Create PR for review
```

### 5. Monitor Metrics

Track improvements after refactoring:

```bash
# Before refactoring
feniks analyze --project-id my_project --meta-reflections before.jsonl
cat before.jsonl | jq 'select(.reflection_type == "complexity")' | wc -l
# 42 complexity issues

# After refactoring
feniks analyze --project-id my_project --meta-reflections after.jsonl
cat after.jsonl | jq 'select(.reflection_type == "complexity")' | wc -l
# 28 complexity issues (33% reduction!)
```

### 6. Document Rationale

Always document why you're refactoring:

```bash
git commit -m "refactor: extract authentication logic

Rationale: AuthService had complexity of 12 (2.67x system average).
Extracted token validation, password hashing, and audit logging into
separate methods to improve testability and maintainability.

Risk: LOW - All existing tests pass, no behavior changes.

Validation: Ran full test suite, manual smoke test, code review."
```

## Integration with CI/CD

Add refactoring analysis to your CI pipeline:

```yaml
# .github/workflows/refactor-analysis.yml
name: Refactor Analysis

on:
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Feniks
        run: pip install -e .

      - name: Start Qdrant
        run: docker run -d -p 6333:6333 qdrant/qdrant

      - name: Run Analysis
        run: |
          feniks analyze \
            --project-id ${{ github.repository }} \
            --collection pr-${{ github.event.number }} \
            --meta-reflections reflections.jsonl

      - name: Check for Critical Issues
        run: |
          CRITICAL=$(cat reflections.jsonl | jq 'select(.severity == "critical")' | wc -l)
          if [ $CRITICAL -gt 0 ]; then
            echo "::error::Found $CRITICAL critical issues"
            cat reflections.jsonl | jq 'select(.severity == "critical")'
            exit 1
          fi

      - name: Suggest Refactorings
        run: |
          cat reflections.jsonl | \
            jq 'select(.tags | contains(["refactoring-opportunity"]))' > opportunities.jsonl

          if [ -s opportunities.jsonl ]; then
            echo "## Refactoring Opportunities" >> $GITHUB_STEP_SUMMARY
            cat opportunities.jsonl | jq -r '.content' | while read line; do
              echo "- $line" >> $GITHUB_STEP_SUMMARY
            done
          fi
```

## Summary

RAE-Feniks refactoring workflows:
- **Safe by default** with dry-run mode
- **Risk-assessed** at every step
- **Auditable** with detailed reports
- **Reversible** via unified diff patches
- **Extensible** with custom recipes
- **Enterprise-ready** with CI/CD integration

Next: Learn how to integrate with [RAE for self-aware agents](./RAE_INTEGRATION.md)
