# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
JSONL loader for Feniks - loads and validates chunk data from indexer output.
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from feniks.core.models.types import ApiEndpoint, Chunk, Dependency, Evidence, GitInfo, MigrationSuggestion
from feniks.exceptions import FeniksIngestError
from feniks.infra.logging import get_logger

log = get_logger("ingest.jsonl_loader")


def generate_stable_id(file_path: str, start_line: int, end_line: int, commit_hash: Optional[str] = None) -> str:
    """
    Generates a stable, repeatable ID for a chunk based on its location and commit.

    Args:
        file_path: Relative path to the file
        start_line: Starting line number
        end_line: Ending line number
        commit_hash: Optional git commit hash for additional stability

    Returns:
        str: SHA1 hash of the chunk identifier
    """
    # Normalize path separators
    normalized_path = str(Path(file_path).as_posix())

    # Create stable identifier
    if commit_hash:
        identifier = f"{normalized_path}:{start_line}:{end_line}:{commit_hash}"
    else:
        identifier = f"{normalized_path}:{start_line}:{end_line}"

    # Generate SHA1 hash
    return hashlib.sha1(identifier.encode("utf-8")).hexdigest()


def parse_git_info(data: Optional[Dict[str, Any]]) -> Optional[GitInfo]:
    """Parse git info from JSON data."""
    if not data:
        return None

    try:
        return GitInfo(
            hash=data.get("hash", ""),
            author=data.get("author", ""),
            date=data.get("date", ""),
            summary=data.get("summary", ""),
        )
    except Exception as e:
        log.warning(f"Failed to parse git info: {e}")
        return None


def parse_api_endpoint(data: Dict[str, Any]) -> ApiEndpoint:
    """Parse API endpoint from JSON data."""
    return ApiEndpoint(
        url=data.get("url", ""),
        method=data.get("method", "GET"),
        dataKeys=data.get("dataKeys", []),
        paramKeys=data.get("paramKeys", []),
    )


def parse_dependency(data: Dict[str, Any]) -> Dependency:
    """Parse dependency from JSON data."""
    return Dependency(type=data.get("type", ""), value=data.get("value", ""))


def parse_evidence(data: Dict[str, Any]) -> Evidence:
    """Parse evidence from JSON data."""
    return Evidence(
        source=data.get("source", ""),
        rule=data.get("rule", ""),
        confidence=data.get("confidence", 0.0),
        file=data.get("file", ""),
        start_line=data.get("start_line", 0),
        end_line=data.get("end_line", 0),
    )


def parse_migration_suggestion(data: Optional[Dict[str, Any]]) -> Optional[MigrationSuggestion]:
    """Parse migration suggestion from JSON data."""
    if not data:
        return None

    try:
        return MigrationSuggestion(target=data.get("target", ""), notes=data.get("notes", ""))
    except Exception as e:
        log.warning(f"Failed to parse migration suggestion: {e}")
        return None


def parse_chunk_from_json(data: Dict[str, Any], normalize_paths: bool = True) -> Chunk:
    """
    Parse a single chunk from JSON data.

    Args:
        data: JSON object representing a chunk
        normalize_paths: Whether to normalize file paths

    Returns:
        Chunk: Validated chunk object

    Raises:
        FeniksIngestError: If required fields are missing or invalid
    """
    try:
        # Required fields - support both snake_case and camelCase
        file_path = data.get("file_path", data.get("filePath", data.get("file", "")))
        if not file_path:
            raise FeniksIngestError("Missing required field: file_path, filePath, or file")

        # Normalize path if requested
        if normalize_paths:
            file_path = str(Path(file_path).as_posix())

        start_line = data.get("start_line", data.get("start", data.get("startLine", 0)))
        end_line = data.get("end_line", data.get("end", data.get("endLine", 0)))
        text = data.get("text", data.get("code", ""))
        chunk_name = data.get("chunk_name", data.get("name", data.get("symbol", "")))
        language = data.get("language", "javascript")

        # Parse nested objects
        git_info = parse_git_info(data.get("git_last_commit"))

        # Parse API endpoints
        api_endpoints_data = data.get("api_endpoints", data.get("apiCalls", []))
        if "metadata" in data and "api_endpoints" in data["metadata"]:
            api_endpoints_data = data["metadata"]["api_endpoints"]
        api_endpoints = [parse_api_endpoint(ep) for ep in api_endpoints_data]

        # Parse dependencies - support both formats
        dependencies_data = data.get("dependencies", data.get("dependenciesDI", []))
        # Convert simple string list to Dependency objects
        if dependencies_data and isinstance(dependencies_data[0] if dependencies_data else None, str):
            dependencies = [Dependency(type="injection", value=dep) for dep in dependencies_data]
        else:
            dependencies = [parse_dependency(dep) for dep in dependencies_data]

        # Parse evidence
        evidence_data = data.get("evidence", [])
        evidence = [parse_evidence(ev) for ev in evidence_data]

        # Parse migration suggestion
        migration_suggestion = parse_migration_suggestion(data.get("migration_suggestion"))

        # Generate stable ID
        commit_hash = git_info.hash if git_info else None
        stable_id = generate_stable_id(file_path, start_line, end_line, commit_hash)

        # Create chunk
        chunk = Chunk(
            id=stable_id,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            text=text,
            chunk_name=chunk_name,
            language=language,
            module=data.get("module"),
            kind=data.get("kind"),
            ast_node_type=data.get("ast_node_type", data.get("nodeType", data.get("astNodeType", ""))),
            dependencies=dependencies,
            calls_functions=data.get(
                "calls_functions", data.get("callsFunctions", data.get("metadata", {}).get("calls_functions", []))
            ),
            api_endpoints=api_endpoints,
            ui_routes=data.get("ui_routes", data.get("uiRoutes", data.get("metadata", {}).get("ui_routes", []))),
            cyclomatic_complexity=data.get(
                "cyclomatic_complexity",
                data.get("complexity", data.get("metadata", {}).get("cyclomatic_complexity", 0)),
            ),
            business_tags=data.get("business_tags", data.get("businessTags", [])),
            git_last_commit=git_info,
            evidence=evidence,
            confidence=data.get("confidence", 1.0),
            criticality_score=data.get("criticality_score", data.get("criticalityScore", 0.0)),
            migration_target=data.get("migration_target"),
            migration_suggestion=migration_suggestion,
            invariants=data.get("invariants", []),
            io_contract=data.get("io_contract", {}),
            api_contract_ref=data.get("api_contract_ref"),
        )

        return chunk

    except FeniksIngestError:
        raise
    except Exception as e:
        raise FeniksIngestError(f"Failed to parse chunk: {e}") from e


def load_jsonl(jsonl_path: Path, normalize_paths: bool = True, skip_errors: bool = False) -> List[Chunk]:
    """
    Load chunks from a JSONL file.

    Args:
        jsonl_path: Path to the JSONL file
        normalize_paths: Whether to normalize file paths
        skip_errors: Whether to skip invalid lines or raise an error

    Returns:
        List[Chunk]: List of validated chunks

    Raises:
        FeniksIngestError: If file doesn't exist or contains invalid data
    """
    if not jsonl_path.exists():
        raise FeniksIngestError(f"JSONL file not found: {jsonl_path}")

    chunks = []
    errors = []

    log.info(f"Loading chunks from {jsonl_path}")

    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    chunk = parse_chunk_from_json(data, normalize_paths=normalize_paths)
                    chunks.append(chunk)

                except json.JSONDecodeError as e:
                    error_msg = f"Line {line_num}: Invalid JSON - {e}"
                    if skip_errors:
                        log.warning(error_msg)
                        errors.append(error_msg)
                    else:
                        raise FeniksIngestError(error_msg) from e

                except FeniksIngestError as e:
                    error_msg = f"Line {line_num}: {e}"
                    if skip_errors:
                        log.warning(error_msg)
                        errors.append(error_msg)
                    else:
                        raise FeniksIngestError(error_msg) from e

    except Exception as e:
        if not isinstance(e, FeniksIngestError):
            raise FeniksIngestError(f"Failed to read JSONL file: {e}") from e
        raise

    log.info(f"Loaded {len(chunks)} chunks from {jsonl_path}")

    if errors:
        log.warning(f"Skipped {len(errors)} invalid lines")

    if not chunks:
        raise FeniksIngestError("No valid chunks found in JSONL file")

    return chunks
