"""CI via GitHub Actions (gh)."""

from __future__ import annotations

import json
from typing import Any

from agent_kit.exec_util import run, tail
from agent_kit.output import emit, fail
from agent_kit.util import require_gh, require_git


def _gh_root(cwd, cmd: str) -> str | int:
    root = require_git(cwd, cmd)
    if not isinstance(root, str):
        return root
    g = require_gh(cmd)
    if g is not True:
        return g
    return root


def status(cwd, *, verbose: bool, human: bool) -> int:
    root = _gh_root(cwd, "ci.status")
    if not isinstance(root, str):
        return root
    r = run(["gh", "run", "list", "--limit", "5", "--json", "databaseId,status,conclusion,name,headBranch,url,createdAt"], cwd=root)
    if not r.ok:
        return fail("ci.status", "CI_LIST_FAILED", tail(r.stderr))
    try:
        runs = json.loads(r.stdout)
    except json.JSONDecodeError:
        return fail("ci.status", "CI_PARSE_FAILED", "JSON inválido")
    latest = runs[0] if runs else None
    failed = [x for x in runs if x.get("conclusion") == "failure"]
    summary = "sem runs"
    if latest:
        summary = f"{latest.get('name')} — {latest.get('status')}/{latest.get('conclusion') or '?'}"
    return emit(
        ok=not failed or latest.get("conclusion") == "success",
        command="ci.status",
        summary=summary,
        data={"latest": latest, "recent": runs, "failed_count": len(failed)},
        next_steps=["agent ci logs"] if failed else None,
        verbose=verbose,
        human=human,
    )


def logs(cwd, *, run_id: int | None, verbose: bool, human: bool) -> int:
    root = _gh_root(cwd, "ci.logs")
    if not isinstance(root, str):
        return root
    selector = str(run_id) if run_id else ""
    if not selector:
        lst = run(["gh", "run", "list", "--limit", "1", "--json", "databaseId,conclusion"], cwd=root)
        if not lst.ok:
            return fail("ci.logs", "CI_LIST_FAILED", tail(lst.stderr))
        try:
            runs = json.loads(lst.stdout)
            if not runs:
                return fail("ci.logs", "NO_RUNS", "Nenhum workflow encontrado")
            selector = str(runs[0]["databaseId"])
            if runs[0].get("conclusion") == "success":
                return emit(ok=True, command="ci.logs", summary="último run passou", data={"run_id": selector}, verbose=verbose, human=human)
        except (json.JSONDecodeError, KeyError):
            return fail("ci.logs", "CI_PARSE_FAILED", "JSON inválido")

    r = run(["gh", "run", "view", selector, "--log-failed"], cwd=root, timeout=60)
    text = tail(r.stdout + r.stderr, max_lines=50, max_chars=8000)
    return emit(
        ok=r.ok,
        command="ci.logs",
        summary=f"logs run {selector}" + (" (falhou)" if not r.ok else ""),
        data={"run_id": selector, "output": text},
        verbose=verbose,
        human=human,
    )
