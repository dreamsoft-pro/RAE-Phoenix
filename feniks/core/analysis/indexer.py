# feniks/core/analysis/indexer.py
import ast
import os
import glob
from typing import Dict, List, Set, Optional
from pydantic import BaseModel
from feniks.infra.logging import get_logger

logger = get_logger("core.analysis.indexer")

class SymbolInfo(BaseModel):
    name: str
    type: str  # 'class', 'function', 'variable'
    file_path: str
    line: int
    dependencies: Set[str] = set()

class ProjectGraph(BaseModel):
    symbols: Dict[str, SymbolInfo] = {}
    file_map: Dict[str, List[str]] = {}

class SystemIndexer:
    """Advanced System-wide Indexer for Dependency and Impact Analysis."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.graph = ProjectGraph()

    def scan_project(self):
        """Full project scan to build the dependency graph."""
        logger.info(f"Building system graph for: {self.project_root}")
        # Focus on Python files for now, expandable via plugins
        files = glob.glob(os.path.join(self.project_root, "**/*.py"), recursive=True)
        for f in files:
            try:
                self._index_file(f)
            except Exception as e:
                logger.warning(f"Failed to index {f}: {e}")
        logger.info(f"System graph ready. Indexed {len(self.graph.symbols)} symbols across {len(self.graph.file_map)} files.")

    def _index_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
            
            file_symbols = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    symbol_name = node.name
                    symbol = SymbolInfo(
                        name=symbol_name,
                        type="class" if isinstance(node, ast.ClassDef) else "function",
                        file_path=file_path,
                        line=node.lineno
                    )
                    
                    # Simple dependency tracking: what functions/classes are called within this node
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            symbol.dependencies.add(child.func.id)
                    
                    self.graph.symbols[symbol_name] = symbol
                    file_symbols.append(symbol_name)
            
            self.graph.file_map[file_path] = file_symbols

    def get_impact_zone(self, file_path: str) -> Dict[str, Any]:
        """Identifies which parts of the system are affected by changes in this file."""
        symbols_in_file = self.graph.file_map.get(file_path, [])
        impacted_symbols = {}
        
        for source_symbol in symbols_in_file:
            dependents = []
            for name, info in self.graph.symbols.items():
                if source_symbol in info.dependencies and info.file_path != file_path:
                    dependents.append({
                        "symbol": name,
                        "file": info.file_path,
                        "line": info.line
                    })
            if dependents:
                impacted_symbols[source_symbol] = dependents
                
        return {
            "file": file_path,
            "impacted_symbols": impacted_symbols,
            "total_dependents": sum(len(v) for v in impacted_symbols.values())
        }
