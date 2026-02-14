from __future__ import annotations

from pathlib import Path
import os


def load_dotenv(*, dotenv_path: Path) -> None:
    """
    Minimal dotenv loader (no external dependency).

    - Ignores blank lines and comments
    - Supports KEY=VALUE (VALUE may be quoted)
    - Does not override existing environment variables
    """
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
            v = v[1:-1]
        os.environ.setdefault(k, v)


def load_default_dotenv(*, project_dir: Path) -> None:
    load_dotenv(dotenv_path=project_dir / ".env")

