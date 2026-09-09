"""Operações GitHub que não cabem em PR/CI."""

from __future__ import annotations

from pathlib import Path

from agent_kit.exec_util import run, tail
from agent_kit.output import emit, fail
from agent_kit.util import require_gh, require_git


def _root(cmd: str):
    root = require_git(None, cmd)
    if not isinstance(root, str):
        return root
    gh = require_gh(cmd)
    return root if gh is True else gh


def auth_status(*, verbose: bool, human: bool) -> int:
    gh = require_gh("github.auth")
    if gh is not True:
        return gh
    r = run(["gh", "auth", "status"])
    return emit(ok=r.ok, command="github.auth", summary="autenticação consultada", data={"output": tail(r.stdout + r.stderr)}, verbose=verbose, human=human)


def api(endpoint: str, *, method: str, input_file: str | None, verbose: bool, human: bool) -> int:
    root = _root("github.api")
    if not isinstance(root, str):
        return root
    cmd = ["gh", "api", endpoint, "--method", method]
    if input_file:
        if not Path(input_file).is_file():
            return fail("github.api", "INPUT_NOT_FOUND", f"Arquivo não encontrado: {input_file}")
        cmd.extend(["--input", input_file])
    r = run(cmd, cwd=root, timeout=60)
    return emit(ok=r.ok, command="github.api", summary=f"gh api {endpoint}", data={"output": tail(r.stdout or r.stderr, max_chars=8000)}, verbose=verbose, human=human)


def release(action: str, *, tag: str | None, title: str | None, verbose: bool, human: bool) -> int:
    root = _root("github.release")
    if not isinstance(root, str):
        return root
    if action == "list":
        cmd = ["gh", "release", "list", "--limit", "20"]
    elif action == "view":
        cmd = ["gh", "release", "view", tag or "latest"]
    else:
        if not tag:
            return fail("github.release", "TAG_REQUIRED", "Informe --tag para criar uma release")
        cmd = ["gh", "release", "create", tag, "--title", title or tag, "--generate-notes"]
    r = run(cmd, cwd=root, timeout=120)
    return emit(ok=r.ok, command="github.release", summary=f"release {action}", data={"tag": tag, "output": tail(r.stdout or r.stderr, max_chars=8000)}, verbose=verbose, human=human)
