# scripts/python_indexer.py
import ast
import os
from typing import Dict, List, Set
from pydantic import BaseModel

class SymbolInfo(BaseModel):
    name: str
    type: str # 'class', 'function', 'import'
    line: int
    dependencies: Set[str] = set()

class ProjectGraph(BaseModel):
    symbols: Dict[str, SymbolInfo] = {}
    file_map: Dict[str, List[str]] = {}

class PythonSymbolIndexer(ast.NodeVisitor):
    """Advanced AST Indexer for Python (DeepMind level dependency analysis)."""
    
    def __init__(self):
        self.current_symbols = []
        self.graph = ProjectGraph()

    def index_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            self.current_file = file_path
            self.file_symbols = []
            self.visit(tree)
            self.graph.file_map[file_path] = self.file_symbols

    def visit_ClassDef(self, node):
        symbol = SymbolInfo(name=node.name, type="class", line=node.lineno)
        self.graph.symbols[node.name] = symbol
        self.file_symbols.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        symbol = SymbolInfo(name=node.name, type="function", line=node.lineno)
        # Track calls as dependencies
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                symbol.dependencies.add(child.func.id)
        
        self.graph.symbols[node.name] = symbol
        self.file_symbols.append(node.name)
        self.generic_visit(node)

    def get_impact_zone(self, symbol_name: str) -> List[str]:
        """Finds all symbols that depend on the given symbol."""
        impacted = []
        for name, info in self.graph.symbols.items():
            if symbol_name in info.dependencies:
                impacted.append(name)
        return impacted

if __name__ == "__main__":
    indexer = PythonSymbolIndexer()
    # Przykład indeksowania rdzenia
    for root, _, files in os.walk("feniks/core"):
        for f in files:
            if f.endswith(".py"):
                indexer.index_file(os.path.join(root, f))
    
    print(f"✅ Indexed {len(indexer.graph.symbols)} symbols.")
    # Przykład analizy wpływu: co zależy od 'RefactorEngine'?
    impact = indexer.get_impact_zone("RefactorEngine")
    print(f"⚠️ Impact Zone for 'RefactorEngine': {impact}")
