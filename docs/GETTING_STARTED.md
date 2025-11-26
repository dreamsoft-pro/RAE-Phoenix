# Getting Started with RAE-Feniks

This guide will walk you through installing RAE-Feniks and running your first code analysis in under an hour.

## Prerequisites

- Python 3.9 or higher
- Node.js 14+ (for JavaScript/TypeScript indexing)
- Docker (for Qdrant vector database)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dreamsoft-pro/RAE-Feniks.git
cd RAE-Feniks
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Feniks

```bash
pip install -e .
```

Verify installation:

```bash
feniks --version
```

You should see:
```
Feniks v0.1.0 - RAE Code Analysis and Refactoring Engine
Profile: dev
Project root: /path/to/feniks
RAE Integration: disabled
Metrics: enabled
Auth: disabled
Cost Control: disabled
```

### 4. Start Qdrant Vector Database

```bash
docker run -d -p 6333:6333 \
  --name qdrant \
  qdrant/qdrant:latest
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

### 5. Configure Environment

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` to match your setup:

```bash
# Profile
FENIKS_PROFILE=dev

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=code_chunks

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Enterprise Features (optional)
METRICS_ENABLED=true
AUTH_ENABLED=false
COST_CONTROL_ENABLED=false
```

## Quick Start: Analyzing a JavaScript Project

Let's analyze a sample Angular project to see RAE-Feniks in action.

### Step 1: Index the Code

First, we need to index the code using the JavaScript indexer:

```bash
# Navigate to your project
cd /path/to/your/angular/project

# Run the indexer
node /path/to/feniks/scripts/js_html_indexer.mjs \
  --root . \
  --output code_index.jsonl
```

This creates a `code_index.jsonl` file containing all code chunks.

**Example output:**
```
Indexed 1247 chunks from 156 files
Output: code_index.jsonl
```

### Step 2: Ingest into Knowledge Base

Now ingest the indexed code into Qdrant:

```bash
feniks ingest \
  --jsonl-path code_index.jsonl \
  --collection my_project \
  --reset
```

**Output:**
```
[INFO] Step 1/5: Loading chunks from JSONL...
[INFO] Loaded 1247 chunks
[INFO] Step 2/5: Filtering chunks...
[INFO] After filtering: 1247 chunks remaining
[INFO] Step 3/5: Creating embeddings...
[INFO] Created dense embeddings: shape=(1247, 384)
[INFO] Step 4/5: Connecting to Qdrant...
[INFO] Connected to Qdrant
[INFO] Step 5/5: Upserting points to Qdrant...
[INFO] Successfully ingested 1247 chunks
```

### Step 3: Analyze the Code

Run analysis to build the system model:

```bash
feniks analyze \
  --project-id my_project \
  --collection my_project \
  --output analysis_report.txt \
  --meta-reflections meta_reflections.jsonl
```

**Output:**
```
[INFO] === Feniks Analysis Pipeline ===
[INFO] Project ID: my_project
[INFO] Collection: my_project
[INFO] Building system model...
[INFO] Detecting capabilities...
[INFO] Generating meta-reflections...
[INFO] === Analysis Complete ===
[INFO] Modules: 45
[INFO] Dependencies: 178
[INFO] Capabilities: 12
[INFO] Central modules: 8
[INFO] Hotspot modules: 5
```

### Step 4: View the Results

#### System Model Report

```bash
cat analysis_report.txt
```

You'll see:
- Module structure
- Dependency graph
- Detected capabilities (auth, API, UI components)
- Central modules (architectural keystones)
- Hotspot modules (high complexity/change)

#### Meta-Reflections

```bash
head -5 meta_reflections.jsonl | jq .
```

Example meta-reflection:
```json
{
  "chunk_id": "auth.service.ts:15-89",
  "reflection_type": "complexity",
  "content": "This authentication service has cyclomatic complexity of 12, above the system average of 4.5. Consider extracting token refresh logic into a separate method.",
  "severity": "medium",
  "tags": ["complexity", "refactoring-opportunity"],
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### Step 5: List Available Refactorings

```bash
feniks refactor --list-recipes
```

**Output:**
```
Available refactoring recipes:
  - reduce_complexity: Reduce cyclomatic complexity in high-complexity modules
    Risk: medium
  - extract_function: Extract long or complex code into separate functions
    Risk: low
```

### Step 6: Run a Refactoring (Dry-Run)

```bash
feniks refactor \
  --recipe reduce_complexity \
  --project-id my_project \
  --collection my_project \
  --output refactor_output \
  --dry-run
```

**Output:**
```
[INFO] === Feniks Refactoring Workflow ===
[INFO] Recipe: reduce_complexity
[INFO] Project ID: my_project
[INFO] Dry run: True
[INFO] Step 1/3: Loading system model...
[INFO] Loaded 1247 chunks
[INFO] Built system model: 45 modules
[INFO] Step 2/3: Running refactoring workflow...
[INFO] Step 3/3: Refactoring complete

================================================================================
Refactoring: reduce_complexity
================================================================================
Status: ✓ Success
Risk: MEDIUM

Rationale: Identified 5 modules with complexity above 1.5x system average

Files changed: 5
  - src/app/services/auth.service.ts
  - src/app/components/dashboard/dashboard.component.ts
  - src/app/utils/data-processor.ts
  - src/app/services/api.service.ts
  - src/app/components/form/form.component.ts

Patch saved to: refactor_output/refactor_reduce_complexity.patch
Report saved to: refactor_output/refactor_report_reduce_complexity.md

Next steps:
  - Review the generated patch carefully
  - Run your test suite
  - Apply the patch if tests pass
================================================================================
```

### Step 7: Review the Patch

```bash
cat refactor_output/refactor_reduce_complexity.patch
```

You'll see a unified diff patch with all proposed changes.

### Step 8: Apply the Patch (Optional)

⚠️ **Only after reviewing and testing!**

```bash
git apply refactor_output/refactor_reduce_complexity.patch
```

## View Metrics

Check system metrics:

```bash
feniks metrics
```

**Output:**
```
================================================================================
Feniks Metrics Summary
================================================================================
Uptime: 3600.0s
Total Projects: 1
Total Operations: 3

Ingests:
  Total: 1
  Successful: 1
  Success Rate: 100.0%
  Avg Duration: 45.23s
  Total Chunks: 1247

Analyses:
  Total: 1
  Successful: 1
  Success Rate: 100.0%
  Avg Duration: 28.67s
  Total Meta-Reflections: 342

Refactorings:
  Total: 1
  Successful: 1
  Success Rate: 100.0%
  Avg Duration: 12.45s
  Total Patches: 1
================================================================================
```

Export metrics to JSON:

```bash
feniks metrics --export metrics.json
```

## Next Steps

Now that you've completed your first analysis, explore:

1. **[Reflection & Meta-Reflection](./REFLECTION_AND_META_REFLECTION.md)** - Understanding the meta-reflection layer
2. **[Enterprise Refactoring](./ENTERPRISE_REFACTORING.md)** - Deep dive into refactoring workflows
3. **[RAE Integration](./RAE_INTEGRATION.md)** - Connecting with RAE for self-aware agents

## Common Issues

### Qdrant Connection Failed

**Error**: `Failed to connect to Qdrant at localhost:6333`

**Solution**: Ensure Qdrant is running:
```bash
docker ps | grep qdrant
# If not running:
docker start qdrant
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'feniks'`

**Solution**: Ensure you've activated the virtual environment and installed feniks:
```bash
source .venv/bin/activate
pip install -e .
```

### No Chunks After Filtering

**Error**: `No chunks remaining after filtering`

**Solution**: Check your include/exclude patterns or use `--skip-errors`:
```bash
feniks ingest --jsonl-path code_index.jsonl --skip-errors
```

## Configuration Options

### Ingestion

```bash
feniks ingest --help
```

Key options:
- `--reset`: Reset collection before ingestion
- `--include`: Include patterns (e.g., `*.ts,*.js`)
- `--exclude`: Exclude patterns (e.g., `*.spec.ts,*.test.js`)
- `--skip-errors`: Skip invalid chunks

### Analysis

```bash
feniks analyze --help
```

Key options:
- `--limit`: Limit chunks for testing
- `--rae-enabled`: Enable/disable RAE integration
- `--output`: Output path for report
- `--meta-reflections`: Output path for meta-reflections

### Refactoring

```bash
feniks refactor --help
```

Key options:
- `--list-recipes`: List available recipes
- `--recipe`: Recipe name to execute
- `--target-module`: Target specific module
- `--dry-run`: Dry run mode (default: true)

## Support

- **Documentation**: `docs/`
- **Examples**: `examples/`
- **Issues**: https://github.com/dreamsoft-pro/RAE-Feniks/issues

## What's Next?

You've successfully:
- ✅ Installed RAE-Feniks
- ✅ Indexed and ingested code
- ✅ Run analysis and viewed meta-reflections
- ✅ Generated refactoring patches
- ✅ Viewed metrics

Continue learning:
- Understand [meta-reflection concepts](./REFLECTION_AND_META_REFLECTION.md)
- Master [enterprise refactoring workflows](./ENTERPRISE_REFACTORING.md)
- Integrate with [RAE for self-aware agents](./RAE_INTEGRATION.md)
