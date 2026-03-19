#!/usr/bin/env python3
import ast
import json
import os
import argparse
from pathlib import Path

def get_complexity(node):
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def get_calls(node):
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return list(set(calls))

def get_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module}.{node.names[0].name}")
    return list(set(imports))

def parse_python_file(file_path, root_path):
    rel_path = os.path.relpath(file_path, root_path).replace(os.sep, '/')
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

    chunks = []
    file_lines = code.splitlines()

    # File-level chunk
    chunks.append({
        "id": f"{rel_path}:0-{len(file_lines)}:file:module",
        "filePath": rel_path,
        "name": os.path.basename(file_path),
        "kind": "module",
        "language": "python",
        "nodeType": "Module",
        "start": 1,
        "end": len(file_lines),
        "text": code,
        "dependencies": [{"type": "import", "value": imp} for imp in get_imports(tree)],
        "metadata": {
            "calls_functions": get_calls(tree),
            "cyclomatic_complexity": get_complexity(tree),
            "api_endpoints": [],
            "ui_routes": [],
            "business_tags": []
        }
    })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line + len(ast.dump(node).splitlines()))
            
            chunk_text = "\n".join(file_lines[start_line-1:end_line])
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            
            chunks.append({
                "id": f"{rel_path}:{start_line}-{end_line}:{kind}:{node.name}",
                "filePath": rel_path,
                "name": node.name,
                "kind": kind,
                "language": "python",
                "nodeType": type(node).__name__,
                "start": start_line,
                "end": end_line,
                "text": chunk_text,
                "dependencies": [],
                "metadata": {
                    "calls_functions": get_calls(node),
                    "cyclomatic_complexity": get_complexity(node),
                    "api_endpoints": [],
                    "ui_routes": [],
                    "business_tags": []
                }
            })

    return chunks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_path = Path(args.out).resolve()
    os.makedirs(out_path.parent, exist_ok=True)

    all_chunks = []
    for file_path in root.rglob("*.py"):
        if ".venv" in str(file_path) or "__pycache__" in str(file_path) or ".git" in str(file_path):
            continue
        all_chunks.extend(parse_python_file(file_path, root))

    with open(out_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")

    print(f"Indexed {len(all_chunks)} Python chunks to {out_path}")

if __name__ == "__main__":
    main()
