"""Detecção de toolchain — usado por test, build e deps."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def pkg_scripts(root: Path) -> dict[str, str]:
    pkg = root / "package.json"
    if not pkg.exists():
        return {}
    try:
        return json.loads(pkg.read_text(encoding="utf-8")).get("scripts") or {}
    except (json.JSONDecodeError, OSError):
        return {}


def node_pm(root: Path) -> str:
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def node_run(root: Path, script: str) -> list[str] | None:
    if script not in pkg_scripts(root):
        return None
    pm = node_pm(root)
    if pm == "npm":
        return ["npm", "run", script]
    return [pm, script]


def detect_all(root: str) -> dict[str, Any]:
    p = Path(root)
    out: dict[str, Any] = {"root": root, "tools": []}

    scripts = pkg_scripts(p)
    if scripts:
        pm = node_pm(p)
        out["node"] = {"pm": pm, "scripts": list(scripts.keys())[:30]}
        for name in ("test", "lint", "typecheck", "build", "dev"):
            if name in scripts:
                out["tools"].append({"kind": name, "cmd": node_run(p, name)})

    if (p / "pyproject.toml").exists() or (p / "pytest.ini").exists():
        out["tools"].append({"kind": "test", "cmd": ["python3", "-m", "pytest", "-q", "--tb=short"], "runner": "pytest"})
    if (p / "requirements.txt").exists() or (p / "pyproject.toml").exists():
        out["tools"].append({"kind": "deps", "cmd": ["python3", "-m", "pip", "install", "-r", "requirements.txt"] if (p / "requirements.txt").exists() else ["python3", "-m", "pip", "install", "-e", "."]})
    if (p / "go.mod").exists():
        out["tools"].append({"kind": "test", "cmd": ["go", "test", "./..."], "runner": "go"})
    if (p / "Cargo.toml").exists():
        out["tools"].append({"kind": "test", "cmd": ["cargo", "test"], "runner": "cargo"})
    if (p / "Makefile").exists() and "test:" in (p / "Makefile").read_text(encoding="utf-8", errors="ignore"):
        out["tools"].append({"kind": "test", "cmd": ["make", "test"], "runner": "make"})

    if scripts:
        pm = node_pm(p)
        install = {"npm": ["npm", "install"], "pnpm": ["pnpm", "install"], "yarn": ["yarn"], "bun": ["bun", "install"]}
        out["install"] = {"cmd": install[pm], "pm": pm}

    out["has_rg"] = shutil.which("rg") is not None
    return out


from agent_kit.config import get_command


def pick_tool(root: str, kind: str) -> list[str] | None:
    cfg_cmd = get_command(kind, root)
    if cfg_cmd:
        return cfg_cmd
    for t in detect_all(root).get("tools", []):
        if t.get("kind") == kind and t.get("cmd"):
            return t["cmd"]
    return None
