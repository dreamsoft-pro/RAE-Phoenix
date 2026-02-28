import argparse
import json
import sys
from pathlib import Path

from jsonschema import validate, ValidationError

# Add project root to allow sibling imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from feniks.infra.logging import log

def main():
    parser = argparse.ArgumentParser(description="Validate a Feniks IR JSONL file against the canonical schema.")
    parser.add_argument("--schema", type=Path, required=True, help="Path to the ir.schema.json file.")
    parser.add_argument("--in", dest="input_path", type=Path, required=True, help="Path to the IR JSONL file to validate.")
    args = parser.parse_args()

    log.info(f"Loading schema from {args.schema}")
    try:
        with args.schema.open("r") as f:
            schema = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        log.error(f"Failed to load or parse schema file: {e}")
        sys.exit(1)

    log.info(f"Validating IR file: {args.input_path}")
    error_count = 0
    line_num = 0
    with args.input_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                instance = json.loads(line)
                validate(instance=instance, schema=schema)
            except json.JSONDecodeError as e:
                log.error(f"L{line_num}: JSON parse error: {e}")
                error_count += 1
            except ValidationError as e:
                log.error(f"L{line_num}: Schema validation error for chunk '{instance.get('id', 'N/A')}': {e.message} (path: {list(e.path)}) ")
                error_count += 1

    if error_count > 0:
        log.error(f"Validation failed with {error_count} errors.")
        sys.exit(1)
    else:
        log.info(f"Successfully validated {line_num} records.")

if __name__ == "__main__":
    main()