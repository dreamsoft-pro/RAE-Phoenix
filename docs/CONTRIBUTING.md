# Contributing to Feniks

Thank you for your interest in contributing to Feniks! We welcome contributions from the community to make this Meta-Reflective Engine even better.

## Development Standards

### 1. Code Style
*   **Python**: We follow PEP 8 guidelines.
*   **Typing**: All new code must have type hints.
*   **Docstrings**: Every public module, class, and method must have a docstring (Google style preferred).

### 2. Testing
*   **Unit Tests**: Every new feature or bug fix must include unit tests covering the logic.
*   **E2E Tests**: For critical flows, verify using end-to-end tests.
*   **Running Tests**:
    ```bash
    ./venv/bin/pytest
    ```

### 3. Architecture
*   Respect the **Hexagonal Architecture**.
*   **Core** must never import from **Adapters** or **Apps**.
*   **Adapters** implement interfaces defined in **Core**.
*   **Apps** wire everything together.

### 4. Pull Request Process
1.  Create a feature branch from `main`.
2.  Implement your changes.
3.  Run tests and ensure they pass.
4.  Submit a PR with a clear description of the problem and solution.
5.  Link related issues.

## Project Structure

*   `feniks/core`: Business logic (pure Python).
*   `feniks/adapters`: Infrastructure implementations (Qdrant, API clients).
*   `feniks/apps`: Entry points (CLI, API).
*   `feniks/infra`: Logging, Metrics, Tracing.

## Setting up Environment

Refer to the [README.md](../README.md) "Quick Start" section for setup instructions.