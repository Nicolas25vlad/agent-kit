"""Estado e helpers rápidos de filesystem."""

from __future__ import annotations

import os
import re
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".next", "target"}


@lru_cache(maxsize=1)
def has_rg() -> bool:
    return shutil.which("rg") is not None


@lru_cache(maxsize=1)
def has_fd() -> bool:
    return shutil.which("fd") is not None


def _state_file() -> Path:
    """Cwd persistido: local .agent-kit/ no projeto, senão cache global."""
    local = Path(os.getcwd()) / ".agent-kit" / "cwd"
    for base in (Path(os.getcwd()), Path.home() / ".cache" / "agent-kit"):
        try:
            base.mkdir(parents=True, exist_ok=True)
            if os.access(base, os.W_OK):
                return base / "cwd" if base.name == "agent-kit" else local
        except OSError:
            continue
    return local


def get_agent_cwd() -> str:
    if env := os.environ.get("AGENT_KIT_CWD"):
        return os.path.abspath(os.path.expanduser(env))
    for sf in (_state_file(), Path(os.getcwd()) / ".agent-kit" / "cwd",
               Path.home() / ".cache" / "agent-kit" / "cwd"):
        try:
            if sf.is_file():
                p = sf.read_text(encoding="utf-8").strip()
                if p and Path(p).is_dir():
                    return p
        except OSError:
            continue
    return os.getcwd()


def set_agent_cwd(path: str) -> str:
    resolved = resolve_path(path)
    if not resolved.is_dir():
        raise NotADirectoryError(str(resolved))
    sf = _state_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(str(resolved) + "\n", encoding="utf-8")
    os.environ["AGENT_KIT_CWD"] = str(resolved)
    return str(resolved)


def resolve_path(path: str, base: str | None = None) -> Path:
    base_p = Path(base or get_agent_cwd())
    p = Path(os.path.expanduser(path))
    if p.is_absolute():
        return p.resolve()
    return (base_p / p).resolve()


def list_entries(path: Path, *, limit: int = 120) -> list[dict[str, Any]]:
    dirs: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                name = entry.name
                if name.startswith(".") and name not in (".git", ".gitignore", ".env.example"):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if name in SKIP_DIRS:
                        continue
                    dirs.append({"name": name, "path": entry.path, "type": "dir"})
                elif entry.is_file(follow_symlinks=False):
                    try:
                        size = entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        size = None
                    files.append({"name": name, "path": entry.path, "type": "file", "size": size})
                if len(dirs) + len(files) >= limit:
                    break
    except OSError:
        return []
    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())
    return (dirs + files)[:limit]


def parse_rg_line(line: str) -> dict[str, str] | None:
    m = re.match(r"^(.+?):(\d+):(.*)$", line)
    if not m:
        return None
    return {"file": m.group(1), "line": m.group(2), "text": m.group(3)[:300]}
