# Versioning Policy

This document describes Feniks' versioning strategy, release process, and how we handle breaking changes.

## Semantic Versioning

Feniks follows [Semantic Versioning 2.0.0](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH
```

### Version Components

- **MAJOR**: Incompatible API changes or significant breaking changes
- **MINOR**: New features added in a backwards-compatible manner
- **PATCH**: Backwards-compatible bug fixes

### Examples

- `0.4.0` → `0.4.1`: Bug fix release
- `0.4.1` → `0.5.0`: New feature release (AngularJS recipes added)
- `0.5.0` → `1.0.0`: Major release with breaking changes

## Pre-1.0 Versioning

**Current Status**: Feniks is in `0.x` versioning, indicating pre-1.0 development status.

### What This Means

- **API Stability**: APIs may change between minor versions
- **Breaking Changes**: Can occur in `0.x.0` releases
- **Production Use**: The project is production-ready despite `0.x` version
- **1.0.0 Milestone**: Will be released when API is considered fully stable

### Pre-1.0 Guidelines

- `0.x.0` releases **may** include breaking changes
- Breaking changes will be clearly documented in CHANGELOG.md
- Migration guides will be provided for significant breaking changes
- `0.x.y` patch releases will only include bug fixes

## Release Process

### Version Bumping Rules

**MAJOR Version** (`x.0.0`):
- Breaking API changes
- Removed features or endpoints
- Major architectural changes
- Significant behavior changes that may break existing usage

**MINOR Version** (`0.x.0`):
- New features added
- New API endpoints
- New CLI commands
- New refactoring recipes
- Enhancements to existing features
- Deprecations (with backward compatibility)

**PATCH Version** (`0.0.x`):
- Bug fixes
- Security patches
- Documentation improvements
- Performance improvements (without API changes)
- Dependency updates

### Release Checklist

Before releasing a new version:

1. **Update Version Numbers**
   - `pyproject.toml` or `setup.py`
   - `feniks/__init__.py`
   - Documentation references

2. **Update CHANGELOG.md**
   - Add release date
   - Categorize changes:
     - `[BREAKING]` - Breaking changes
     - `[FEATURE]` - New features
     - `[FIX]` - Bug fixes
     - `[DOCS]` - Documentation
     - `[SECURITY]` - Security fixes

3. **Run Full Test Suite**
   ```bash
   pytest
   pytest --cov=feniks --cov-report=html
   ```

4. **Run Linters**
   ```bash
   black feniks/ tests/
   isort feniks/ tests/
   flake8 feniks/ tests/
   mypy feniks/
   ```

5. **Update Documentation**
   - Ensure README reflects new features
   - Update migration guides if needed
   - Generate API documentation

6. **Create Git Tag**
   ```bash
   git tag -a v0.4.0 -m "Release v0.4.0: AngularJS Migration Ready"
   git push origin v0.4.0
   ```

7. **Create GitHub Release**
   - Use CHANGELOG entry as release notes
   - Attach distribution files if applicable
   - Mark as pre-release for `0.x` versions

8. **Publish to PyPI** (when ready)
   ```bash
   python -m build
   twine upload dist/*
   ```

## Breaking Changes

### Definition

A breaking change is any modification that:
- Removes or renames public APIs, functions, or classes
- Changes function signatures (parameters, return types)
- Changes default behavior in incompatible ways
- Removes CLI commands or changes their behavior
- Changes configuration file formats
- Requires code modifications to upgrade

### Handling Breaking Changes

**1. Documentation**
- Clearly mark breaking changes with `[BREAKING]` in CHANGELOG
- Provide migration guide in release notes
- Update documentation with upgrade instructions

**2. Deprecation Process**
When possible, deprecate before removing:

```python
import warnings

def old_function():
    warnings.warn(
        "old_function() is deprecated, use new_function() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

**3. Communication**
- Announce breaking changes in release notes
- Provide examples of old vs new usage
- Give advance warning in previous release when possible

### Example Breaking Change Announcement

```markdown
## [0.5.0] - 2025-12-01

### [BREAKING] Changes

#### API Endpoint Renaming

**OLD**: `POST /analyze`
**NEW**: `POST /analysis`

**Migration**: Update all API client code:
```python
# Before
response = client.post("/analyze", data=payload)

# After
response = client.post("/analysis", data=payload)
```

**Reason**: Consistency with REST naming conventions.
```

## Version Lifecycle

### Support Policy

| Version Status | Support Level | Duration |
|----------------|---------------|----------|
| **Current** | Full support (features + fixes) | Until next minor release |
| **Previous Minor** | Security fixes only | 3 months after next release |
| **Older** | No support | - |

### Example Timeline

```
0.4.0 released (2025-11-27)
├─ 0.4.1 (bug fixes only)
├─ 0.4.2 (bug fixes only)
└─ 0.5.0 released (2026-01-15)
    ├─ 0.4.x: Security fixes until 2026-04-15
    ├─ 0.5.1 (bug fixes)
    └─ 0.6.0 released (2026-03-01)
        └─ 0.5.x: Security fixes until 2026-06-01
```

## Deprecation Policy

### Deprecation Process

1. **Announce**: Mark feature as deprecated in code with warnings
2. **Document**: Add to CHANGELOG with `[DEPRECATED]` tag
3. **Wait**: Keep deprecated feature for at least one minor version
4. **Remove**: Remove in next major version (or next minor in 0.x)

### Deprecation Notice Format

```python
@deprecated(
    reason="Use new_api() instead",
    version="0.5.0",
    remove_in="0.6.0"
)
def old_api():
    """Old API method (deprecated)."""
    pass
```

### Documentation

```markdown
## [0.5.0] - 2026-01-15

### [DEPRECATED] Features

- `old_api()` - Use `new_api()` instead. Will be removed in 0.6.0.
- `--old-flag` - Use `--new-flag` instead. Will be removed in 0.6.0.
```

## Git Tags

### Tag Format

- Release tags: `v0.4.0`, `v0.5.0`, `v1.0.0`
- Pre-release tags: `v0.5.0-beta.1`, `v1.0.0-rc.1`

### Tag Message

```bash
git tag -a v0.4.0 -m "Release v0.4.0: AngularJS Migration Ready

Major Features:
- AngularJS to Next.js migration recipes
- CLI migration command
- End-to-end demo
- Implementation status documentation

See CHANGELOG.md for full details.
"
```

## CHANGELOG.md Format

### Structure

```markdown
# Changelog

All notable changes to Feniks will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes

## [0.4.0] - 2025-11-27

### Added
- AngularJS to Next.js migration recipes
- CLI command: `feniks angular migrate`
- End-to-end migration demo
- Implementation status table in README

### Changed
- Enhanced CONTRIBUTING.md with concrete guidelines
- Updated branding URLs from placeholder to actual

### Security
- Added SECURITY.md with vulnerability reporting policy

## [0.3.0] - 2025-11-26

...
```

### Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes
- **[BREAKING]**: Breaking changes (prefix in title)

## Version Queries

### Python

```python
import feniks
print(feniks.__version__)  # "0.4.0"
```

### CLI

```bash
feniks --version
# Feniks v0.4.0 - RAE Code Analysis and Refactoring Engine
```

### API

```bash
curl http://localhost:8000/version
# {"version": "0.4.0", "build": "abc123"}
```

## Roadmap

### Current: 0.4.x (AngularJS Migration Ready)
- Stable AngularJS migration recipes
- CLI migration command
- Bug fixes and improvements

### Next: 0.5.0 (Planned Q1 2026)
- React migration recipes
- Enhanced behavior guard features
- Performance improvements

### Future: 1.0.0 (Planned Q2-Q3 2026)
- Stable public API
- Full API documentation
- Production-grade all features
- Long-term support commitment

## Questions?

For questions about versioning:
- **Issues**: [GitHub Issues](https://github.com/glesniowski/feniks/issues)
- **Discussions**: [GitHub Discussions](https://github.com/glesniowski/feniks/discussions)
- **Email**: grzegorz.lesniowski@gmail.com

---

**Last Updated**: 2025-11-27
**Policy Version**: 1.0
