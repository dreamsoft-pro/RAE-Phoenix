#fenik_collect_intel.py
#!/usr/bin/env python3
"""
Zbiera zawartość projektu do jednego pliku tekstowego i dopisuje podsumowanie.

Cechy:
- Wspiera projekty git: używa `git ls-files` (tracked + nieignorowane untracked),
  co automatycznie respektuje .gitignore.
- Dodatkowo wycina typowe katalogi bibliotek (node_modules, .venv itd.).
- Pomija binaria (heurystyka + rozszerzenia) oraz bardzo duże pliki.
- Każdy plik poprzedzony nagłówkiem: "# relative/path/from/project_root".
- Wynik zapisuje w katalogu uruchomienia jako: _Project_data_DD_MM_YYYY_HH_MM_SS.txt

Użycie:
    python fenik_collect_intel.py                # z katalogu projektu
    python fenik_collect_intel.py --project /ścieżka/do/projektu
"""

from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, List, Set

try:
    from gitignore_parser import parse_gitignore
except ImportError:
    parse_gitignore = None  # Fallback, jeśli biblioteka nie jest zainstalowana

# Katalogi, których nie chcemy w ogóle oglądać (niezależnie od .gitignore)
EXCLUDED_DIRS: Set[str] = {
    ".git", ".hg", ".svn",

    ".venv", "venv", "env", ".env",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".cache",

    "node_modules", "bower_components",

    "dist", "build", "coverage", "htmlcov",

    "runs", "logs",

    "frontend-master",
    "zzz_descriptions",
    "data",   # dostosuj w razie potrzeby
}

# Rozszerzenia, które traktujemy jako "na pewno niepotrzebne" do promptu
SKIP_EXTENSIONS: Set[str] = {
    # Python / binaria
    ".pyc", ".pyo", ".pyd",
    ".so", ".dylib", ".dll", ".exe", ".bin",

    # Archiwa
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",

    # Grafika / media
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".mp4", ".mov", ".avi", ".mkv",
    ".mp3", ".wav", ".ogg", ".flac",

    # Inne ciężkie / niekodowe
    ".pdf",
    ".db", ".sqlite", ".sqlite3",
}

# Limit rozmiaru pojedynczego pliku (w bajtach) – powyżej tego plik jest pomijany.
# Chodzi o to, żeby nie pakować ogromnych zminifikowanych bundle'y itp.
MAX_FILE_SIZE_BYTES: int = 512 * 1024  # 512 KB


def is_binary_file(p: Path, probe_bytes: int = 2048) -> bool:
    """Prosty test binarności: obecność NUL lub niski udział znaków 'tekstopodobnych'."""
    try:
        with p.open("rb") as f:
            chunk = f.read(probe_bytes)
        if not chunk:
            return False
        if b"\x00" in chunk:
            return True
        text_like = sum(
            b in b"\t\n\r\f\b" or 32 <= b <= 126 or 160 <= b for b in chunk
        )
        return text_like / max(1, len(chunk)) < 0.85
    except Exception:
        # Ostrożniej: w razie błędu traktujemy jako binarny
        return True


def read_text_safely(p: Path) -> Optional[str]:
    """Czyta plik jako tekst; zwraca None dla binarnych lub nieczytelnych."""
    if is_binary_file(p):
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def is_in_excluded_dir(project_root: Path, p: Path) -> bool:
    """
    Sprawdza, czy plik leży w którymś z EXCLUDED_DIRS (patrząc po segmentach ścieżki).
    """
    try:
        rel_parts = p.relative_to(project_root).parts
    except ValueError:
        # Nie powinno się zdarzyć, ale na wszelki wypadek
        return False

    # wszystkie segmenty poza samą nazwą pliku
    for part in rel_parts[:-1]:
        if part in EXCLUDED_DIRS:
            return True
    return False


def should_skip_file(project_root: Path, p: Path) -> bool:
    """Logika pomijania plików na podstawie ścieżki, rozszerzenia i rozmiaru."""
    if not p.is_file():
        return True

    if is_in_excluded_dir(project_root, p):
        return True

    suffix = p.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return True

    try:
        size = p.stat().st_size
    except OSError:
        return True

    if size > MAX_FILE_SIZE_BYTES:
        return True

    return False


def try_collect_files_with_git(project_root: Path) -> Optional[List[Path]]:
    """
    Próbuje użyć `git ls-files`, aby zbudować listę plików projektu.
    Zwraca listę ścieżek lub None, jeśli nie uda się (brak git, brak repo, błąd).
    """
    git_dir = project_root / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        return None

    def run_git(args: Iterable[str]) -> Optional[List[str]]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            # git nie jest zainstalowany
            return None

        if result.returncode != 0:
            return None

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines

    tracked = run_git(["ls-files"])
    if tracked is None:
        return None

    # Dodajemy też untracked, ale nieignorowane (exclude-standard respektuje .gitignore, .git/info/exclude itd.)
    others = run_git(["ls-files", "--others", "--exclude-standard"]) or []

    rel_paths = set(tracked) | set(others)
    files: List[Path] = []

    for rel_str in rel_paths:
        p = project_root / rel_str
        if p.is_file():
            files.append(p)

    return files


def build_gitignore_matcher(project_root: Path):
    """
    Buduje matcher dla .gitignore w katalogu głównym projektu (jeśli istnieje i mamy gitignore_parser).
    Zwraca funkcję matcher(path_str) -> bool lub None.
    """
    if parse_gitignore is None:
        return None

    gitignore_path = project_root / ".gitignore"
    if gitignore_path.is_file():
        try:
            return parse_gitignore(str(gitignore_path))
        except Exception:
            return None
    return None


def walk_project_with_gitignore(project_root: Path) -> Iterable[Path]:
    """
    Fallback, gdy nie możemy użyć git:
    - przechodzi po drzewie katalogów,
    - wycina EXCLUDED_DIRS,
    - respektuje root .gitignore (jeśli mamy gitignore_parser),
    - zwraca ścieżki plików (jeszcze nie przefiltrowane przez should_skip_file).
    """
    matcher = build_gitignore_matcher(project_root)

    for current_root, dirs, files in os.walk(
        project_root, topdown=True, followlinks=False
    ):
        # Modyfikujemy dirs in-place, żeby os.walk nie wchodził w wykluczone katalogi
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        current_root_path = Path(current_root)
        for fname in files:
            p = current_root_path / fname

            # Respektuj .gitignore (root) jeśli dostępny
            if matcher is not None:
                try:
                    rel_str = str(p.relative_to(project_root).as_posix())
                except ValueError:
                    rel_str = str(p)
                if matcher(rel_str):
                    continue

            yield p


def build_output_filename(prefix: str = "_Project_data_") -> str:
    # DD_MM_YYYY_HH_MM_SS
    now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    return f"{prefix}{now}.txt"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Zbierz zawartość projektu do jednego pliku tekstowego "
            "z podziałem na pliki (# relative/path)."
        )
    )
    ap.add_argument(
        "--project",
        "-p",
        default=".",
        help="Ścieżka do katalogu projektu (domyślnie bieżący katalog).",
    )
    args = ap.parse_args()

    project_root = Path(args.project).resolve()
    if not project_root.is_dir():
        raise SystemExit(f"⛔ Podana ścieżka nie jest katalogiem: {project_root}")

    # Najpierw spróbujmy git (jeśli dostępny i repo wygląda OK)
    files_via_git = try_collect_files_with_git(project_root)
    if files_via_git is not None:
        candidate_files = files_via_git
        used_git = True
    else:
        # Fallback: os.walk + (opcjonalnie) .gitignore
        candidate_files = list(walk_project_with_gitignore(project_root))
        used_git = False

    out_name = build_output_filename()
    out_path = Path.cwd() / out_name

    count_files = 0
    skipped_binaries = 0
    skipped_large = 0
    skipped_by_filter = 0
    total_source_lines = 0

    with out_path.open("w", encoding="utf-8") as out:
        for file_path in sorted(candidate_files):
            if should_skip_file(project_root, file_path):
                skipped_by_filter += 1
                continue

            content = read_text_safely(file_path)
            if content is None:
                skipped_binaries += 1
                continue

            rel = file_path.relative_to(project_root).as_posix()

            # Liczba linii z oryginalnego pliku (bez naszych nagłówków)
            file_lines = len(content.splitlines())
            total_source_lines += file_lines

            # Nagłówek z nazwą pliku
            out.write(f"# {rel}\n")
            # Zawartość pliku
            out.write(content)
            # Upewnij się, że każdy plik kończy się co najmniej jedną pustą linią
            if not content.endswith("\n"):
                out.write("\n")
            out.write("\n")

            count_files += 1

        # --- PODSUMOWANIE NA KOŃCU PLIKU ---
        out.write("# --- PODSUMOWANIE ---\n")
        out.write(f"# Katalog projektu: {project_root}\n")
        out.write(f"# Plików zebranych: {count_files}\n")
        out.write(f"# Łącznie linii (oryginalne pliki): {total_source_lines}\n")
        out.write(f"# Użyto git ls-files: {used_git}\n")
        out.write(f"# Pomięto plików (binaria / nieczytelne): {skipped_binaries}\n")
        out.write(f"# Pomięto plików przez filtry (rozmiar/rozszerzenie/katalog): {skipped_by_filter}\n")
        out.write(f"# Maksymalny rozmiar pliku: {MAX_FILE_SIZE_BYTES} bajtów\n")

    print(
        f"✅ Zakończono. Zebrano {count_files} plików tekstowych "
        f"(pomięto binarnych/nieczytelnych: {skipped_binaries}, "
        f"pomięto przez filtry: {skipped_by_filter})."
    )
    print(f"🧮 Łącznie linii (oryginalne pliki): {total_source_lines}")
    print(f"📄 Plik wyjściowy: {out_path}")
    print(f"🐙 Użyto git ls-files: {used_git}")


if __name__ == "__main__":
    main()
