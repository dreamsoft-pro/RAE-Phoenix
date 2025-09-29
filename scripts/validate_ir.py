#!/usr/bin/env python3
from __future__ import annotations
import json, argparse
from pathlib import Path
from jsonschema import Draft7Validator

def load_schema(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_jsonl(schema_path: Path, data_path: Path) -> int:
    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)
    total = 0; errors = 0; examples = []
    with data_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                errors += 1; examples.append((i, f"Invalid JSON: {e}")); continue
            total += 1
            errs = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            if errs:
                errors += 1
                msgs = [f"{list(e.path)}: {e.message}" for e in errs[:3]]
                examples.append((i, "; ".join(msgs)))
    print(f"[VALIDATE] {data_path} — total={total}, errors={errors}")
    if examples:
        print("Examples:")
        for line_no, msg in examples[:10]:
            print(f"  line {line_no}: {msg}")
    return 0 if errors == 0 else 1

def main():
    ap = argparse.ArgumentParser(description="Validate Feniks IR JSONL against JSON Schema")
    ap.add_argument("--schema", required=True, help="Path to schemas/ir.schema.json")
    ap.add_argument("--in", dest="inp", required=True, help="Path to IR JSONL")
    args = ap.parse_args()
    exit(validate_jsonl(Path(args.schema), Path(args.inp)))

if __name__ == "__main__":
    main()
