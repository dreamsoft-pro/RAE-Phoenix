import argparse
import json
import sys
from pathlib import Path

# Add project root to allow sibling imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from feniks.logger import log

def calculate_criticality(chunk: dict) -> float:
    """Heuristically calculate a criticality score."""
    score = 0.0
    score += chunk.get("cyclomatic_complexity", 0) * 0.5
    if "/api/" in chunk.get("text", ""):
        score += 10
    # Simple heuristic: more dependencies, more critical
    score += len(chunk.get("dependencies_di", [])) * 0.2
    return round(score, 2)

def determine_migration_target(chunk: dict) -> str:
    """Heuristically determine the migration target."""
    kind = chunk.get("kind")
    if kind == "service":
        return "React Hook (useSWR or React Query)"
    if kind == "controller":
        return "React Component (Client)"
    if kind == "directive":
        return "React Component (Server or Client)"
    if kind == "filter":
        return "Utility Function"
    return "Undetermined"

def main():
    parser = argparse.ArgumentParser(description="Convert enriched chunks to the Feniks IR format.")
    parser.add_argument("--in", dest="input_path", type=Path, required=True, help="Path to the enriched JSONL file.")
    parser.add_argument("--out", dest="output_path", type=Path, required=True, help="Path to write the IR JSONL file.")
    args = parser.parse_args()

    log.info(f"Converting {args.input_path} to IR format at {args.output_path}")

    records_written = 0
    with args.input_path.open("r", encoding="utf-8") as infile, \
         args.output_path.open("w", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                chunk = json.loads(line)

                # --- Transformation to IR ---
                ir_record = {
                    # Passthrough fields
                    "id": chunk.get("id"),
                    "file_path": chunk.get("filePath"),
                    "start_line": chunk.get("start"),
                    "end_line": chunk.get("end"),
                    "text": chunk.get("text"),
                    "chunk_name": chunk.get("name"),
                    "module": chunk.get("module"),
                    "kind": chunk.get("kind"),
                    "ast_node_type": chunk.get("ast_node_type"),
                    "dependencies_di": chunk.get("dependencies_di", []),
                    "calls_functions": chunk.get("calls_functions", []),
                    "api_endpoints": chunk.get("api_endpoints", []),
                    "ui_routes": chunk.get("ui_routes", []),
                    "cyclomatic_complexity": chunk.get("cyclomatic_complexity", 0),
                    "business_tags": chunk.get("business_tags", []),
                    "git_last_commit": chunk.get("git_last_commit"),

                    # New IR fields (with heuristics)
                    "confidence": 0.85, # Placeholder confidence
                    "criticality_score": calculate_criticality(chunk),
                    "migration_target": determine_migration_target(chunk),
                    "evidence": [], # To be filled by more advanced steps
                    "invariants": [],
                    "io_contract": {},
                    "api_contract_ref": None
                }

                outfile.write(json.dumps(ir_record) + "\n")
                records_written += 1

            except (json.JSONDecodeError, KeyError) as e:
                log.warning(f"Skipping corrupted or incomplete line: {e} -> {line.strip()}")

    log.info(f"Successfully converted {records_written} records to IR format.")

if __name__ == "__main__":
    main()