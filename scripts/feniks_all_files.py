#!/usr/bin/env python3
"""
Zbiera zawartość projektu 'feniks' do jednego pliku tekstowego i dopisuje podsumowanie liczby linii.

- Pomija katalogi: frontend-master, .venv, .pytest_cache, .git, zzz_descriptions, __pycache__
- W katalogu głównym projektu uwzględnia tylko: test.js, requirements.txt, README.md, pytest.ini, package.json
- Każdy plik poprzedza nagłówkiem: "# relative/path"
- Wynik zapisuje w katalogu uruchomienia skryptu jako: _Fenik_data_DD_MM_YYYY_HH_MM_SS.txt

Użycie:
    python fenik_collect.py                # z katalogu projektu
    python fenik_collect.py --project /ścieżka/do/feniks
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
from datetime import datetime

EXCLUDED_DIRS = {
    "frontend-master",
    "node_modules",
    "data",
    "docs",
    "runs",
    ".venv",
    ".pytest_cache",
    ".git",
    "zzz_descriptions",
    "__pycache__",
}

ALLOWED_ROOT_FILES = {
    "test.js",
    "requirements.txt",
    "README.md",
    "pytest.ini",
    "package.json",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin"
}

def is_binary_file(p: Path, probe_bytes: int = 2048) -> bool:
    """Prosty test binarności: obecność NUL lub wysoki udział znaków nienadrukowalnych."""
    try:
        with p.open("rb") as f:
            chunk = f.read(probe_bytes)
        if not chunk:
            return False
        if b"\x00" in chunk:
            return True
        # Heurystyka: odsetek "tekstopodobnych" bajtów
        text_like = sum(b in b"\t\n\r\f\b" or 32 <= b <= 126 or 160 <= b for b in chunk)
        return text_like / max(1, len(chunk)) < 0.85
    except Exception:
        # W razie problemu z odczytem – traktuj jako binarny, by nie psuć wyjścia
        return True

def should_skip_file(root: Path, p: Path) -> bool:
    """Reguły pomijania plików."""
    if p.suffix.lower() in SKIP_EXTENSIONS:
        return True
    # Jeśli to plik w katalogu głównym projektu – musi być na białej liście
    if p.parent.resolve() == root.resolve():
        return p.name not in ALLOWED_ROOT_FILES
    return False

def walk_project(project_root: Path):
    """Generator plików do zebrania, z wykluczeniami katalogów."""
    for current_root, dirs, files in os.walk(project_root, topdown=True, followlinks=False):
        # Wytnij katalogi po nazwie (basename)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        current_root_path = Path(current_root)
        for fname in files:
            p = current_root_path / fname
            if should_skip_file(project_root, p):
                continue
            yield p

def read_text_safely(p: Path) -> str | None:
    """Czyta plik jako tekst; zwraca None dla binarnych lub nieczytelnych."""
    if is_binary_file(p):
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

def build_output_filename() -> str:
    # DD_MM_YYYY_HH_MM_SS
    now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    return f"_Fenik_data_{now}.txt"

def main():
    ap = argparse.ArgumentParser(description="Zbierz zawartość projektu feniks do jednego pliku tekstowego.")
    ap.add_argument("--project", "-p", default=".", help="Ścieżka do katalogu projektu (domyślnie bieżący katalog).")
    args = ap.parse_args()

    project_root = Path(args.project).resolve()
    if not project_root.is_dir():
        raise SystemExit(f"⛔ Podana ścieżka nie jest katalogiem: {project_root}")

    out_name = build_output_filename()
    out_path = Path.cwd() / out_name

    count_files = 0
    skipped_binaries = 0
    total_source_lines = 0  # łączna liczba linii z oryginalnych plików (bez nagłówków)

    with out_path.open("w", encoding="utf-8") as out:
        for file_path in sorted(walk_project(project_root)):
            rel = file_path.relative_to(project_root).as_posix()

            content = read_text_safely(file_path)
            if content is None:
                skipped_binaries += 1
                continue

            # Policz linie z oryginalnego pliku (bez nagłówków/pustych linii dodawanych w wyjściu)
            file_lines = len(content.splitlines())
            total_source_lines += file_lines

            # Nagłówek z nazwą pliku
            out.write(f"# {rel}\n")
            # Zawartość pliku
            out.write(content)
            # Upewnij się, że każdy plik kończy się przynajmniej jedną pustą linią
            if not content.endswith("\n"):
                out.write("\n")
            out.write("\n")

            count_files += 1

        # --- PODSUMOWANIE NA KOŃCU PLIKU ---
        out.write("# --- PODSUMOWANIE ---\n")
        out.write(f"# Plików zebranych: {count_files}\n")
        out.write(f"# Łącznie linii (oryginalne pliki): {total_source_lines}\n")

    print(f"✅ Zakończono. Zebrano {count_files} plików tekstowych"
          f"{f', pominięto binarnych: {skipped_binaries}' if skipped_binaries else ''}.")
    print(f"🧮 Łącznie linii (oryginalne pliki): {total_source_lines}")
    print(f"📄 Plik wyjściowy: {out_path}")

if __name__ == "__main__":
    main()
