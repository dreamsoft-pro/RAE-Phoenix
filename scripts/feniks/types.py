from dataclasses import dataclass
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