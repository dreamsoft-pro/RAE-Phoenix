# RAE-Feniks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Enterprise-grade code analysis, meta-reflection, and refactoring engine**

RAE-Feniks is a powerful system that enables deep code understanding, self-aware agents, and safe automated refactoring through meta-reflection and RAE integration.

## What is RAE-Feniks?

RAE-Feniks goes beyond traditional static analysis by:
- 🔍 **Building deep system models** that capture architecture, dependencies, and capabilities
- 🧠 **Generating meta-reflections** that provide insights into code quality and design
- 🔧 **Automating safe refactorings** through recipe-based workflows with risk assessment
- 🤖 **Enabling self-aware agents** via RAE (Reflective Agent Engine) integration

## Key Features

### Deep Code Analysis
- Multi-language support (JavaScript, TypeScript, Python, etc.)
- AST-based semantic understanding
- Dependency graph extraction
- Automatic capability detection

### Meta-Reflection Layer
- Local per-chunk reflections
- RAE-powered global insights
- Historical learning from refactorings
- Rationale capture for every decision

### Enterprise Refactoring
- Recipe-based workflows (reduce_complexity, extract_function, etc.)
- Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)
- Dry-run mode (safe by default)
- Unified diff patch generation

### Enterprise Grade
- **Observability**: Full metrics collection and reporting
- **Security**: JWT authentication with RBAC
- **Governance**: Budget management and cost control
- **Multi-tenant**: Per-project isolation

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/dreamsoft-pro/RAE-Feniks.git
cd RAE-Feniks

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Verify
feniks --version
```

### Start Qdrant

```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### Run Demo

```bash
cd examples
./run_ingest_and_analyze.sh
```

See [Getting Started Guide](docs/GETTING_STARTED.md) for detailed instructions.

## Example Usage

### 1. Index Your Code

```bash
node scripts/js_html_indexer.mjs \
  --root /path/to/your/project \
  --output code_index.jsonl
```

### 2. Ingest into Knowledge Base

```bash
feniks ingest \
  --jsonl-path code_index.jsonl \
  --collection my_project \
  --reset
```

### 3. Analyze and Generate Meta-Reflections

```bash
feniks analyze \
  --project-id my_project \
  --collection my_project \
  --output analysis_report.txt \
  --meta-reflections meta_reflections.jsonl
```

### 4. Run Refactoring

```bash
# List available recipes
feniks refactor --list-recipes

# Run refactoring (dry-run)
feniks refactor \
  --recipe reduce_complexity \
  --project-id my_project \
  --collection my_project \
  --output refactor_output \
  --dry-run

# Review and apply patch
cat refactor_output/refactor_reduce_complexity.patch
git apply refactor_output/refactor_reduce_complexity.patch
```

### 5. View Metrics

```bash
feniks metrics --project-id my_project
```

## Documentation

- **[Overview](docs/OVERVIEW.md)** - What is RAE-Feniks and why use it
- **[Getting Started](docs/GETTING_STARTED.md)** - Installation and quickstart
- **[Meta-Reflection](docs/REFLECTION_AND_META_REFLECTION.md)** - Understanding meta-reflection
- **[Enterprise Refactoring](docs/ENTERPRISE_REFACTORING.md)** - Refactoring workflows
- **[RAE Integration](docs/RAE_INTEGRATION.md)** - Building self-aware agents
- **[Examples](examples/)** - Sample projects and outputs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAE-Feniks CLI                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│    Ingest    │    │   Analyze    │      │   Refactor   │
│   Pipeline   │    │   Pipeline   │      │    Engine    │
└──────────────┘    └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
        ┌──────────────────────────────────────────┐
        │       System Model & Meta-Reflection     │
        └──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│   Qdrant     │    │     RAE      │      │  Enterprise  │
│  Vector DB   │    │  Self-Model  │      │   Features   │
└──────────────┘    └──────────────┘      └──────────────┘
```

## Use Cases

### 1. Codebase Onboarding
Quickly understand system architecture, dependencies, and technical debt.

### 2. Technical Debt Management
Identify and prioritize refactoring opportunities based on complexity and impact.

### 3. Safe Refactoring
Automated refactoring with risk assessment, dry-run previews, and validation steps.

### 4. Continuous Improvement
Track refactoring outcomes, learn from past decisions, build institutional knowledge.

### 5. Self-Aware Agents
Enable AI agents that understand their own code and propose informed improvements.

## Enterprise Features

### Observability
- Operation tracking (ingest, analyze, refactor)
- Success rates and timing metrics
- Per-project breakdown
- JSON export for dashboards

### Security
- JWT authentication
- Role-based access control (VIEWER, REFACTORER, ADMIN)
- API key management
- Multi-tenant support

### Governance
- Per-project budgets
- Operation cost tracking
- Budget alerts and limits
- Cost reporting

### Configuration

```bash
# .env
RAE_ENABLED=true
RAE_BASE_URL=http://localhost:8000
METRICS_ENABLED=true
AUTH_ENABLED=true
COST_CONTROL_ENABLED=true
```

## Development Status

### Completed Iterations
- ✅ **Iteration 1**: Stabilization and organization
- ✅ **Iteration 2**: Code ingestion pipeline
- ✅ **Iteration 3**: System model layer
- ✅ **Iteration 4**: Meta-reflection layer
- ✅ **Iteration 5**: RAE integration
- ✅ **Iteration 6**: Enterprise refactoring workflows
- ✅ **Iteration 7**: Observability, security, governance
- ✅ **Iteration 8**: Documentation and examples

**Status**: Production-ready for enterprise use

## Requirements

- Python 3.9 or higher
- Node.js 14+ (for JavaScript/TypeScript indexing)
- Docker (for Qdrant)
- 4GB RAM minimum (8GB recommended)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Adding New Features

- **Language Support**: Add new indexer in `scripts/`
- **Refactoring Recipes**: Extend `feniks.refactor.recipe.RefactorRecipe`
- **Capabilities**: Add detection rules in `feniks.core.capability_detector`

## Support

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: https://github.com/dreamsoft-pro/RAE-Feniks/issues

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) file for details.

## Citation

If you use RAE-Feniks in your research or project, please cite:

```bibtex
@software{rae_feniks,
  title = {RAE-Feniks: Enterprise Code Analysis and Refactoring Engine},
  author = {Grzegorz Leśniowski},
  year = {2025},
  url = {https://github.com/dreamsoft-pro/RAE-Feniks}
}
```

## Philosophy

RAE-Feniks is built on three core principles:

1. **Safety First**: All refactorings are dry-run by default with comprehensive risk assessment
2. **Meta-Awareness**: Systems should understand themselves to improve themselves
3. **Enterprise Ready**: Production-grade observability, security, and governance

---

**Built with ❤️ by Grzegorz Leśniowski**

For questions, feedback, or collaboration: [GitHub Issues](https://github.com/dreamsoft-pro/RAE-Feniks/issues)
