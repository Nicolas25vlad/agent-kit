"""Diagnóstico rápido do ambiente."""

from __future__ import annotations

import shutil
import sys
from typing import Any

from agent_kit.config import CONFIG_NAME
from agent_kit.exec_util import git_root, run
from agent_kit.output import emit, fail


def doctor(*, verbose: bool, human: bool) -> int:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"tool": name, "ok": ok, "detail": detail})

    add("python", True, sys.version.split()[0])
    add("git", shutil.which("git") is not None)
    add("gh", shutil.which("gh") is not None)
    add("rg", shutil.which("rg") is not None)
    add("fd", shutil.which("fd") is not None)
    add("docker", shutil.which("docker") is not None)

    root = git_root()
    add("git_repo", root is not None, root or "")
    if root:
        from pathlib import Path as P
        cfg_exists = P(root, CONFIG_NAME).is_file()
        add("agent_config", True, "presente" if cfg_exists else "ausente — rode agent config learn")

    if shutil.which("gh"):
        auth = run(["gh", "auth", "status"], timeout=10)
        add("gh_auth", auth.ok, "autenticado" if auth.ok else tail_short(auth.stderr))

    failed = [c for c in checks if not c["ok"]]
    return emit(
        ok=not failed,
        command="doctor",
        summary=f"{len(checks) - len(failed)}/{len(checks)} ok" + (f", {len(failed)} falha(s)" if failed else ""),
        data={"checks": checks},
        next_steps=[f"instalar/corrigir {f['tool']}" for f in failed[:2]] or None,
        verbose=verbose,
        human=human,
    )


def tail_short(s: str, n: int = 80) -> str:
    s = (s or "").strip().splitlines()
    return s[0][:n] if s else ""
