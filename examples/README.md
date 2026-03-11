# RAE-Feniks Examples

This directory contains examples and sample outputs to help you get started with RAE-Feniks.

## Quick Start

The fastest way to see RAE-Feniks in action:

```bash
cd examples
./run_ingest_and_analyze.sh
```

This script will:
1. Check prerequisites (Qdrant, Node.js, etc.)
2. Index your code (if not already done)
3. Ingest into knowledge base
4. Run analysis and generate meta-reflections
5. Execute sample refactoring
6. Display system metrics

## Files in This Directory

### `run_ingest_and_analyze.sh`
Complete end-to-end demo script that demonstrates the entire RAE-Feniks workflow.

**Usage**:
```bash
# Basic usage (uses defaults)
./run_ingest_and_analyze.sh

# Custom project
PROJECT_ROOT=/path/to/your/project ./run_ingest_and_analyze.sh

# Custom output directory
OUTPUT_DIR=./my_output ./run_ingest_and_analyze.sh

# All options
PROJECT_ID=my_app \
PROJECT_ROOT=/path/to/project \
COLLECTION=my_collection \
OUTPUT_DIR=./output \
./run_ingest_and_analyze.sh
```

**Prerequisites**:
- RAE-Feniks installed (`pip install -e .`)
- Qdrant running (`docker run -d -p 6333:6333 qdrant/qdrant`)
- Node.js (for JavaScript/TypeScript indexing)

### `sample_meta_reflections.md`
Example meta-reflections showing different types of insights:
- **Complexity**: High-complexity code that needs refactoring
- **Dependencies**: Circular dependencies and tight coupling
- **Design Patterns**: Both good and bad patterns
- **Technical Debt**: Legacy code that needs modernization
- **Security**: Critical security vulnerabilities
- **Hotspots**: Frequently changing modules
- **Testing**: Missing or inadequate test coverage
- **Architecture**: Good and bad architectural decisions

Use this to understand what meta-reflections look like and how to interpret them.

### `sample_refactor_patch.diff`
Example refactoring patch showing complexity reduction through function extraction.

**Before**: A 75-line login method with complexity 12
**After**: Clean, well-organized code with complexity 5

This demonstrates:
- How RAE-Feniks extracts functions
- Patch format (unified diff)
- Meta-reflection on the refactoring
- Validation steps
- Lessons learned

**To review**:
```bash
cat sample_refactor_patch.diff
```

**To understand patch format**:
```bash
# Lines starting with - are removed
# Lines starting with + are added
# Lines without +/- are context
```

### `angular_project_demo/`
Sample Angular project setup for testing RAE-Feniks.

See [angular_project_demo/README.md](./angular_project_demo/README.md) for details.

## Typical Workflow

### 1. Index Your Code

For JavaScript/TypeScript projects:
```bash
node ../scripts/js_html_indexer.mjs \
  --root /path/to/your/project \
  --output code_index.jsonl
```

For Python projects (when implemented):
```bash
python ../scripts/python_indexer.py \
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

**Options**:
- `--reset`: Clear collection before ingestion
- `--include`: Include patterns (e.g., `*.ts,*.js`)
- `--exclude`: Exclude patterns (e.g., `*.spec.ts`)
- `--skip-errors`: Skip invalid chunks

### 3. Analyze Code

```bash
feniks analyze \
  --project-id my_project \
  --collection my_project \
  --output analysis_report.txt \
  --meta-reflections meta_reflections.jsonl
```

**Outputs**:
- `analysis_report.txt`: System model and analysis summary
- `meta_reflections.jsonl`: Detailed reflections (one per line)

### 4. Review Meta-Reflections

```bash
# All reflections
cat meta_reflections.jsonl | jq .

# High/critical severity only
cat meta_reflections.jsonl | jq 'select(.severity == "high" or .severity == "critical")'

# Refactoring opportunities
cat meta_reflections.jsonl | jq 'select(.tags | contains(["refactoring-opportunity"]))'

# Security issues
cat meta_reflections.jsonl | jq 'select(.reflection_type == "security")'

# Group by module
cat meta_reflections.jsonl | jq -r '.context.module' | sort | uniq -c | sort -rn
```

### 5. Run Refactoring

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

# Review patch
cat refactor_output/refactor_reduce_complexity.patch

# Apply patch (after review!)
git apply refactor_output/refactor_reduce_complexity.patch
```

### 6. View Metrics

```bash
# System-wide metrics
feniks metrics

# Project-specific metrics
feniks metrics --project-id my_project

# Export metrics
feniks metrics --export metrics.json
```

## Sample Output

### Analysis Report
```
=== RAE-Feniks Analysis Report ===
Project ID: my_project
Analysis Date: 2025-11-26T10:30:00Z

System Model Summary:
- Total Modules: 45
- Total Dependencies: 178
- Average Complexity: 4.5
- Dependency Depth: 3

Capabilities Detected:
- authentication
- REST API
- UI components
- database access
- file upload
- email notifications

Central Modules (architectural keystones):
1. auth.service.ts (8 dependents)
2. api.service.ts (12 dependents)
3. database.service.ts (15 dependents)

Hotspot Modules (high change frequency):
1. api.service.ts (47 changes, 3 months)
2. auth.service.ts (32 changes, 3 months)

High-Complexity Modules:
1. auth.service.ts (complexity: 12, 2.67x average)
2. dashboard.component.ts (complexity: 11, 2.44x average)
```

### Meta-Reflections Summary
```
Total Reflections: 342

By Severity:
  critical: 3
  high: 45
  medium: 123
  low: 89
  info: 82

By Type:
  complexity: 78
  dependency: 42
  tech-debt: 67
  testing: 34
  security: 8
  pattern: 45

Refactoring Opportunities: 89
```

## Tips and Best Practices

### 1. Start Small
Begin with a small module or package to understand the workflow before analyzing your entire codebase.

### 2. Prioritize Critical Issues
Focus on `critical` and `high` severity reflections first:
```bash
cat meta_reflections.jsonl | jq 'select(.severity == "critical" or .severity == "high")' > priority.jsonl
```

### 3. Track Progress
Re-run analysis after refactorings to measure improvement:
```bash
# Before
feniks analyze --project-id my_project --meta-reflections before.jsonl
wc -l before.jsonl  # 342 reflections

# After refactoring
feniks analyze --project-id my_project --meta-reflections after.jsonl
wc -l after.jsonl  # 289 reflections (15% improvement!)
```

### 4. Use Tags for Planning
Group refactorings by tag:
```bash
# Extract function opportunities
cat meta_reflections.jsonl | jq 'select(.tags | contains(["extract-function"]))' > extract_function.jsonl

# Circular dependencies
cat meta_reflections.jsonl | jq 'select(.tags | contains(["circular-dependency"]))' > circular_deps.jsonl
```

### 5. Integrate with CI/CD
Add analysis to your pipeline to catch issues early:
```yaml
# .github/workflows/analysis.yml
- name: Run Feniks Analysis
  run: |
    feniks analyze --project-id ${{ github.repository }} --meta-reflections reflections.jsonl

    CRITICAL=$(cat reflections.jsonl | jq 'select(.severity == "critical")' | wc -l)
    if [ $CRITICAL -gt 0 ]; then
      echo "Found $CRITICAL critical issues"
      exit 1
    fi
```

## Troubleshooting

### Qdrant Connection Failed
```
Error: Failed to connect to Qdrant at localhost:6333
```
**Solution**: Start Qdrant:
```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### No Chunks After Filtering
```
Error: No chunks remaining after filtering
```
**Solutions**:
- Check your include/exclude patterns
- Use `--skip-errors` to skip invalid chunks
- Verify JSONL format

### Module Not Found
```
ModuleNotFoundError: No module named 'feniks'
```
**Solution**: Install Feniks:
```bash
source .venv/bin/activate
pip install -e .
```

### Indexer Script Not Found
```
Error: Indexer script not found
```
**Solution**: Ensure you're in the project root:
```bash
cd /path/to/feniks
ls scripts/js_html_indexer.mjs  # Should exist
```

## Next Steps

After exploring these examples:

1. Read the [full documentation](../docs/)
2. Try analyzing your own project
3. Experiment with different refactoring recipes
4. Integrate RAE-Feniks into your development workflow
5. Consider [RAE integration](../docs/RAE_INTEGRATION.md) for self-aware agents

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: https://github.com/dreamsoft-pro/RAE-Feniks/issues
- **Getting Started**: [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md)

Happy refactoring! 🚀
