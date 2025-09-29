from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing import List, Optional

@dataclass
class Chunk:
    """Represents a chunk of code or HTML, standardized from the AST parser output."""
    id: str
    file_path: str
    module: Optional[str]
    chunk_name: str
    kind: str
    ast_node_type: str
    dependencies_di: List[str]
    anti_patterns: List[str]
    text: str
    start_line: int
    end_line: int
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # --- Nowe, wzbogacone pola ---

    # Pola z rozszerzonego parsera
    api_endpoints: List[str] = field(default_factory=list)
    migration_suggestion: Dict[str, str] = field(default_factory=dict)

    # Pola na przyszłe ulepszenia
    git_info: Optional[Dict[str, str]] = None
    summary_en: Optional[str] = None
    cyclomatic_complexity: Optional[int] = None