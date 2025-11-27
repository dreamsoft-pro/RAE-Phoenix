# Contributing to Feniks

Thank you for your interest in contributing to Feniks! We welcome contributions from the community to make this Meta-Reflective Engine even better.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Standards](#development-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Commit Message Format](#commit-message-format)
- [Project Structure](#project-structure)
- [Getting Help](#getting-help)

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](../CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [grzegorz.lesniowski@gmail.com](mailto:grzegorz.lesniowski@gmail.com).

## 🤝 How to Contribute

### Ways to Contribute

- **Report Bugs**: Open an issue with the `bug` label
- **Suggest Features**: Open an issue with the `enhancement` label
- **Improve Documentation**: Submit PRs for docs improvements
- **Write Code**: Fix bugs or implement features
- **Write Tests**: Improve test coverage
- **Review PRs**: Help review pull requests from other contributors

### First Time Contributors

Look for issues labeled `good first issue` - these are beginner-friendly tasks that are a great way to start contributing.

## 🛠️ Development Standards

### 1. Code Style

**Python:**
- Follow **PEP 8** guidelines strictly
- Use **Black** for code formatting: `black feniks/`
- Use **isort** for import sorting: `isort feniks/`
- Run **flake8** for linting: `flake8 feniks/`

**Type Hints:**
- All new code **must** have type hints
- Use `mypy` for type checking: `mypy feniks/`
- For complex types, import from `typing` module

**Docstrings:**
- Every public module, class, and method must have a docstring
- Use **Google style** docstrings
- Include:
  - Brief description
  - Args with types
  - Returns with type
  - Raises (if applicable)
  - Example usage (for complex functions)

**Example:**
```python
def migrate_controller(source_path: str, output_path: str) -> MigrationResult:
    """
    Migrate AngularJS controller to Next.js component.

    Args:
        source_path: Path to the AngularJS controller file
        output_path: Path where the Next.js component will be written

    Returns:
        MigrationResult object containing success status and file changes

    Raises:
        FeniksError: If source file is invalid or migration fails

    Example:
        >>> result = migrate_controller("app.js", "component.tsx")
        >>> print(result.success)
        True
    """
```

### 2. Testing

**Requirements:**
- **Unit Tests**: Every new feature or bug fix must include tests
- **Test Coverage**: Maintain at least **80%** coverage
- **E2E Tests**: Critical flows must have end-to-end tests

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=feniks --cov-report=html

# Run specific test file
pytest tests/core/refactor/test_controller.py

# Run tests matching pattern
pytest -k "test_migration"
```

**Test Naming:**
- Test files: `test_*.py`
- Test functions: `test_<what_it_tests>()`
- Use descriptive names: `test_controller_migration_generates_typescript()`

### 3. Architecture

**Hexagonal Architecture Rules:**
- **Core** must never import from **Adapters** or **Apps**
- **Adapters** implement interfaces defined in **Core**
- **Apps** wire everything together
- Use dependency injection for all external dependencies

**Dependency Direction:**
```
Apps → Adapters → Core
         ↑         ↑
         └─────────┘
    (Implements interfaces)
```

**Example:**
```python
# ✅ GOOD - Core defines interface
class StoragePort(ABC):
    @abstractmethod
    def save(self, data: Data) -> None: ...

# ✅ GOOD - Adapter implements interface
class QdrantStorage(StoragePort):
    def save(self, data: Data) -> None:
        # Implementation

# ❌ BAD - Core importing adapter
from feniks.adapters.storage.qdrant import QdrantStorage  # In core module
```

## 📝 Pull Request Process

### Before Submitting

1. **Create an Issue** (for significant changes)
2. **Fork the repository** and create your branch from `main`
3. **Run tests** locally and ensure they pass
4. **Update documentation** if you changed APIs or functionality
5. **Add tests** for new functionality
6. **Run linters** (black, isort, flake8, mypy)

### Branch Naming

Use descriptive branch names following this pattern:
```
<type>/<short-description>

Examples:
- feat/angular-migration-cli
- fix/behavior-guard-snapshot-bug
- docs/improve-contributing-guide
- refactor/simplify-recipe-interface
```

**Types:**
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### PR Title Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

Examples:
- feat(angular): add CLI migration command
- fix(behavior): handle null snapshots gracefully
- docs(readme): update implementation status table
- refactor(recipes): simplify controller recipe logic
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Fixes #<issue_number>
Relates to #<issue_number>

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] E2E tests added/updated (if applicable)
- [ ] All tests pass locally
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated (if applicable)
- [ ] No new warnings generated
- [ ] Tests provide adequate coverage
```

### Review Process

1. **Automated Checks**: CI must pass (tests, linting, type checking)
2. **Code Review**: At least one maintainer approval required
3. **Changes Requested**: Address all review comments
4. **Approval**: Maintainer will merge when ready

### After Merge

- Your PR will be included in the next release
- You'll be added to the contributors list
- Breaking changes will be documented in CHANGELOG.md

## 🐛 Issue Guidelines

### Before Creating an Issue

- **Search existing issues** to avoid duplicates
- **Check documentation** - your question may already be answered
- **Verify the bug** - make sure it's reproducible

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug.

## To Reproduce
Steps to reproduce the behavior:
1. Run command '...'
2. With config '....'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- Feniks Version: [e.g., 0.4.0]
- Python Version: [e.g., 3.10.5]
- OS: [e.g., Ubuntu 22.04]
- Qdrant Version: [e.g., 1.7.0]

## Additional Context
- Error messages
- Stack traces
- Configuration files
- Screenshots (if applicable)
```

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature you'd like to see.

## Motivation
Why is this feature needed? What problem does it solve?

## Proposed Solution
How do you think this should work?

## Alternatives Considered
Other solutions you've considered.

## Additional Context
Any other context, mockups, or examples.
```

## ✉️ Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Scopes:**
- `angular`: AngularJS migration
- `behavior`: Behavior Guard
- `recipes`: Refactoring recipes
- `cli`: Command-line interface
- `api`: REST API
- `core`: Core business logic
- `docs`: Documentation

**Examples:**
```
feat(angular): add directive to component recipe

Implement recipe that converts AngularJS directives to React components.
Handles isolated scope, transclusion, and link functions.

fix(behavior): handle null snapshots in contract builder

Fixes crash when processing snapshots with null observations.
Adds validation and logging for invalid snapshots.

Fixes #123

docs(readme): add implementation status table

Provides clear overview of what's implemented vs planned.

BREAKING CHANGE: API endpoint /analyze renamed to /analysis
```

## 📂 Project Structure

```
feniks/
├── feniks/
│   ├── core/              # Business logic (pure Python)
│   │   ├── reflection/    # System model, meta-reflection
│   │   ├── evaluation/    # Analysis pipeline
│   │   ├── refactor/      # Refactoring engine, recipes
│   │   ├── policies/      # Quality policies, cost control
│   │   └── models/        # Data models, types
│   ├── adapters/          # Infrastructure implementations
│   │   ├── storage/       # Qdrant, Postgres
│   │   ├── llm/           # Embedding, LLM clients
│   │   ├── ingest/        # Data ingestion
│   │   └── runners/       # Behavior test runners
│   ├── apps/              # Entry points
│   │   ├── cli/           # Command-line interface
│   │   ├── api/           # FastAPI REST API
│   │   └── workers/       # Background workers
│   ├── infra/             # Cross-cutting concerns
│   │   ├── logging/       # Structured logging
│   │   ├── metrics/       # Prometheus metrics
│   │   └── tracing/       # OpenTelemetry tracing
│   └── config/            # Configuration (Pydantic)
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example projects
└── scripts/               # Utility scripts
```

## 🆘 Getting Help

### Documentation

- **README**: [README.md](../README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **AngularJS Migration**: [ANGULARJS_MIGRATION.md](ANGULARJS_MIGRATION.md)
- **Behavior Guard**: [LEGACY_BEHAVIOR_GUARD.md](LEGACY_BEHAVIOR_GUARD.md)

### Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/glesniowski/feniks/issues)
- **GitHub Discussions**: [Ask questions, share ideas](https://github.com/glesniowski/feniks/discussions)
- **Email**: grzegorz.lesniowski@gmail.com

### Development Questions

When asking for help:
1. **Search existing issues/discussions** first
2. **Provide context**: What you're trying to do
3. **Include details**: Code snippets, error messages, environment
4. **Be respectful**: Remember maintainers are volunteers

---

## 📄 License

By contributing to Feniks, you agree that your contributions will be licensed under the [Apache License 2.0](../LICENSE).

---

**Thank you for contributing to Feniks! 🦅**