from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing import List, Optional

@dataclass
class GitInfo:
    hash: str
    author: str
    date: str
    summary: str

@dataclass
class MigrationSuggestion:
    target: str
    notes: str

@dataclass
class Evidence:
    source: str
    rule: str
    confidence: float
    file: str
    start_line: int
    end_line: int

@dataclass
class Chunk:
    id: str
    file_path: str
    start_line: int
    end_line: int
    text: str
    chunk_name: str
    
    # --- Wzbogacone Metadane ---
    module: Optional[str] = None
    kind: Optional[str] = None # service, controller, directive, filter, route, template
    ast_node_type: Optional[str] = None
    
    # Relacje
    dependencies_di: List[str] = field(default_factory=list)
    calls_functions: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    ui_routes: List[str] = field(default_factory=list)

    # Jakość i Kontekst
    cyclomatic_complexity: int = 0
    business_tags: List[str] = field(default_factory=list)
    git_last_commit: Optional[GitInfo] = None

    # --- Nowe Pola IR ---
    evidence: List[Evidence] = field(default_factory=list)
    confidence: float = 1.0
    criticality_score: float = 0.0
    migration_target: Optional[str] = None
    migration_suggestion: Optional[MigrationSuggestion] = None
    invariants: List[str] = field(default_factory=list)
    io_contract: Dict[str, Any] = field(default_factory=dict)
    api_contract_ref: Optional[str] = None