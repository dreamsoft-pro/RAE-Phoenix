# src/feniks/types.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Chunk:
    """
    Standardowy kawałek (kod/HTML) pochodzący z parsera AST lub fallbacku.
    Pola zostają kompatybilne z Twoim stanem: dependencies_di, anti_patterns itd.
    """
    id: str
    file_path: str
    module: Optional[str]
    chunk_name: str
    kind: str                 # component|service|directive|route|filter|template|style|util
    ast_node_type: str
    dependencies_di: List[str]
    anti_patterns: List[str]
    text: str
    start_line: int
    end_line: int
    route: Optional[str] = None
    symbol: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # i18nKeys, commit_hash, ts, etc.
