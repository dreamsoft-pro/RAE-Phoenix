import hashlib
import re
from pathlib import Path


def ensure_dir(p: Path) -> None:
    """Ensures that a directory exists, creating it if necessary."""
    p.mkdir(parents=True, exist_ok=True)


def sha1(s: str) -> str:
    """Computes the SHA1 hash of a string."""
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()


def extract_module_from_path(path: Path) -> str | None:
    """Extracts the AngularJS module name from a file path."""
    p = path.as_posix()
    # This regex looks for a pattern like /app/src/MODULE_NAME/
    m = re.search(r"(?:^|/)app/src/([^/]+)/", p)
    return m.group(1) if m else None
