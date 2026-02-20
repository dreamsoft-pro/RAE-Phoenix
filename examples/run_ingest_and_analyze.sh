#!/usr/bin/env bash
#
# RAE-Feniks Demo Script
# This script demonstrates the complete workflow from indexing to refactoring
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-demo_project}"
PROJECT_ROOT="${PROJECT_ROOT:-.}"
COLLECTION="${COLLECTION:-feniks_demo}"
OUTPUT_DIR="${OUTPUT_DIR:-./feniks_output}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RAE-Feniks Complete Demo Workflow${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Project ID:    ${GREEN}$PROJECT_ID${NC}"
echo -e "Project Root:  ${GREEN}$PROJECT_ROOT${NC}"
echo -e "Collection:    ${GREEN}$COLLECTION${NC}"
echo -e "Output Dir:    ${GREEN}$OUTPUT_DIR${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

# Check if feniks is installed
if ! command -v feniks &> /dev/null; then
    echo -e "${RED}✗ Error: feniks not found${NC}"
    echo -e "${YELLOW}  Please install: pip install -e .${NC}"
    exit 1
fi
echo -e "${GREEN}✓ feniks installed${NC}"

# Check if Qdrant is running
if ! curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Error: Qdrant not running${NC}"
    echo -e "${YELLOW}  Please start: docker run -d -p 6333:6333 qdrant/qdrant${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Qdrant running${NC}"

# Check if Node.js is available for indexing
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Warning: Node.js not found (needed for JS/TS indexing)${NC}"
fi

echo ""

# Step 2: Index the code (if JSONL doesn't exist)
JSONL_FILE="$OUTPUT_DIR/code_index.jsonl"

if [ ! -f "$JSONL_FILE" ]; then
    echo -e "${BLUE}Step 2: Indexing code...${NC}"
    mkdir -p "$OUTPUT_DIR"

    # Check if indexer script exists
    INDEXER_SCRIPT="./scripts/js_html_indexer.mjs"
    if [ ! -f "$INDEXER_SCRIPT" ]; then
        echo -e "${YELLOW}⚠ Indexer script not found at $INDEXER_SCRIPT${NC}"
        echo -e "${YELLOW}  Skipping indexing. Please provide $JSONL_FILE manually.${NC}"
    else
        echo -e "Indexing project at: ${GREEN}$PROJECT_ROOT${NC}"
        node "$INDEXER_SCRIPT" --root "$PROJECT_ROOT" --output "$JSONL_FILE"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Indexing complete${NC}"
            CHUNK_COUNT=$(wc -l < "$JSONL_FILE")
            echo -e "  Total chunks: ${GREEN}$CHUNK_COUNT${NC}"
        else
            echo -e "${RED}✗ Indexing failed${NC}"
            exit 1
        fi
    fi
else
    echo -e "${BLUE}Step 2: Using existing index${NC}"
    CHUNK_COUNT=$(wc -l < "$JSONL_FILE")
    echo -e "  Found: ${GREEN}$JSONL_FILE${NC} ($CHUNK_COUNT chunks)"
fi

echo ""

# Step 3: Ingest into Qdrant
echo -e "${BLUE}Step 3: Ingesting code into knowledge base...${NC}"

feniks ingest \
    --jsonl-path "$JSONL_FILE" \
    --collection "$COLLECTION" \
    --reset \
    --skip-errors

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ingestion complete${NC}"
else
    echo -e "${RED}✗ Ingestion failed${NC}"
    exit 1
fi

echo ""

# Step 4: Run analysis
echo -e "${BLUE}Step 4: Running code analysis...${NC}"

REPORT_FILE="$OUTPUT_DIR/analysis_report.txt"
REFLECTIONS_FILE="$OUTPUT_DIR/meta_reflections.jsonl"

feniks analyze \
    --project-id "$PROJECT_ID" \
    --collection "$COLLECTION" \
    --output "$REPORT_FILE" \
    --meta-reflections "$REFLECTIONS_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Analysis complete${NC}"
    echo -e "  Report:       ${GREEN}$REPORT_FILE${NC}"
    echo -e "  Reflections:  ${GREEN}$REFLECTIONS_FILE${NC}"
else
    echo -e "${RED}✗ Analysis failed${NC}"
    exit 1
fi

echo ""

# Step 5: Show summary of meta-reflections
echo -e "${BLUE}Step 5: Meta-Reflection Summary${NC}"

if [ -f "$REFLECTIONS_FILE" ]; then
    TOTAL_REFLECTIONS=$(wc -l < "$REFLECTIONS_FILE")
    echo -e "Total reflections: ${GREEN}$TOTAL_REFLECTIONS${NC}"

    if command -v jq &> /dev/null; then
        echo ""
        echo "By severity:"
        cat "$REFLECTIONS_FILE" | jq -r '.severity' | sort | uniq -c | while read count severity; do
            echo -e "  $severity: ${GREEN}$count${NC}"
        done

        echo ""
        echo "By type:"
        cat "$REFLECTIONS_FILE" | jq -r '.reflection_type' | sort | uniq -c | while read count type; do
            echo -e "  $type: ${GREEN}$count${NC}"
        done

        echo ""
        echo -e "${YELLOW}High/Critical issues:${NC}"
        cat "$REFLECTIONS_FILE" | jq -r 'select(.severity == "high" or .severity == "critical") | "  [\(.severity)] \(.content)"' | head -5

        REFACTOR_OPS=$(cat "$REFLECTIONS_FILE" | jq 'select(.tags | contains(["refactoring-opportunity"]))' | wc -l)
        if [ "$REFACTOR_OPS" -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}Found $REFACTOR_OPS refactoring opportunities${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Install 'jq' for detailed reflection analysis${NC}"
    fi
fi

echo ""

# Step 6: List available refactoring recipes
echo -e "${BLUE}Step 6: Available Refactoring Recipes${NC}"

feniks refactor --list-recipes

echo ""

# Step 7: Run sample refactoring (dry-run)
echo -e "${BLUE}Step 7: Running sample refactoring (dry-run)...${NC}"

REFACTOR_OUTPUT="$OUTPUT_DIR/refactor_output"
mkdir -p "$REFACTOR_OUTPUT"

feniks refactor \
    --recipe reduce_complexity \
    --project-id "$PROJECT_ID" \
    --collection "$COLLECTION" \
    --output "$REFACTOR_OUTPUT" \
    --dry-run

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Refactoring analysis complete${NC}"

    # Check if patch was generated
    PATCH_FILE="$REFACTOR_OUTPUT/refactor_reduce_complexity.patch"
    if [ -f "$PATCH_FILE" ]; then
        echo -e "  Patch: ${GREEN}$PATCH_FILE${NC}"
        echo ""
        echo -e "${YELLOW}To apply the patch:${NC}"
        echo -e "  ${GREEN}git apply $PATCH_FILE${NC}"
        echo ""
        echo -e "${YELLOW}To review the patch:${NC}"
        echo -e "  ${GREEN}cat $PATCH_FILE${NC}"
    else
        echo -e "${YELLOW}  No refactoring needed (code is already optimal!)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Refactoring analysis completed with warnings${NC}"
fi

echo ""

# Step 8: View metrics
echo -e "${BLUE}Step 8: System Metrics${NC}"

feniks metrics --project-id "$PROJECT_ID"

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Demo Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Generated files:"
echo -e "  ${GREEN}$JSONL_FILE${NC} - Indexed code chunks"
echo -e "  ${GREEN}$REPORT_FILE${NC} - Analysis report"
echo -e "  ${GREEN}$REFLECTIONS_FILE${NC} - Meta-reflections"
echo -e "  ${GREEN}$REFACTOR_OUTPUT/${NC} - Refactoring patches"
echo ""
echo -e "Next steps:"
echo -e "  1. Review analysis report: ${GREEN}cat $REPORT_FILE${NC}"
echo -e "  2. Explore meta-reflections: ${GREEN}cat $REFLECTIONS_FILE | jq .${NC}"
echo -e "  3. Review refactoring patch: ${GREEN}cat $REFACTOR_OUTPUT/*.patch${NC}"
echo -e "  4. Read documentation: ${GREEN}docs/${NC}"
echo ""
echo -e "${GREEN}Happy refactoring! 🎉${NC}"
