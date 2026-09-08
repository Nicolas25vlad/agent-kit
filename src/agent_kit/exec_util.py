"""Execução de subprocessos com timeout e captura compacta."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Sequence


@dataclass
class CmdResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run(
    cmd: Sequence[str],
    *,
    cwd: str | None = None,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> CmdResult:
    import time
    from agent_kit.fs_util import get_agent_cwd

    if cwd is None:
        cwd = get_agent_cwd()
    start = time.monotonic()
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            list(cmd),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return CmdResult(
            cmd=list(cmd),
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return CmdResult(
            cmd=list(cmd),
            returncode=124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=f"timeout after {timeout}s",
            duration_ms=duration_ms,
        )
    except FileNotFoundError:
        return CmdResult(
            cmd=list(cmd),
            returncode=127,
            stdout="",
            stderr=f"command not found: {cmd[0]}",
            duration_ms=0,
        )


def git_root(cwd: str | None = None) -> str | None:
    r = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, timeout=5)
    if not r.ok:
        return None
    return r.stdout.strip()


def tail(text: str, max_lines: int = 30, max_chars: int = 4000) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    clipped = "\n".join(lines[-max_lines:])
    if len(clipped) > max_chars:
        return clipped[-max_chars:]
    return clipped
