"""Operações de PR via gh."""

from __future__ import annotations

import json
from typing import Any

from agent_kit.exec_util import run, tail
from agent_kit.output import emit, fail
from agent_kit.util import require_gh, require_git


def open_pr(cwd, *, title, body, base, draft, verbose, human) -> int:
    root = require_git(cwd, "pr.open")
    if not isinstance(root, str) or require_gh("pr.open") is not True:
        return root if not isinstance(root, str) else require_gh("pr.open")

    cmd = ["gh", "pr", "create", "--title", title] + (["--body", body] if body else []) + (["--base", base] if base else []) + (["--draft"] if draft else [])
    r = run(cmd, cwd=root, timeout=60)
    if not r.ok:
        return fail("pr.open", "PR_CREATE_FAILED", tail(r.stderr or r.stdout))
    url = r.stdout.strip()
    view = run(["gh", "pr", "view", url, "--json", "number,url,title,state"], cwd=root)
    data: dict[str, Any] = {"url": url}
    if view.ok:
        try:
            data["pr"] = json.loads(view.stdout)
        except json.JSONDecodeError:
            pass
    return emit(ok=True, command="pr.open", summary=f"PR: {url}", data=data, verbose=verbose, human=human)


def list_prs(cwd, *, mine: bool, limit: int, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "pr.list")
    if not isinstance(root, str) or require_gh("pr.list") is not True:
        return root if not isinstance(root, str) else require_gh("pr.list")

    cmd = ["gh", "pr", "list", "--json", "number,title,state,url,headRefName", "--limit", str(limit)]
    if mine:
        cmd.append("--author=@me")
    r = run(cmd, cwd=root)
    if not r.ok:
        return fail("pr.list", "PR_LIST_FAILED", tail(r.stderr))
    try:
        prs = json.loads(r.stdout)
    except json.JSONDecodeError:
        return fail("pr.list", "PR_PARSE_FAILED", "JSON inválido")
    return emit(ok=True, command="pr.list", summary=f"{len(prs)} PR(s)", data={"prs": prs}, verbose=verbose, human=human)


def review(cwd, *, number, verbose, human) -> int:
    root = require_git(cwd, "pr.review")
    if not isinstance(root, str) or require_gh("pr.review") is not True:
        return root if not isinstance(root, str) else require_gh("pr.review")

    sel = str(number) if number else ""
    cmd = ["gh", "pr", "view", sel, "--json", "number,title,state,url,reviewDecision,comments,statusCheckRollup"] if sel else ["gh", "pr", "view", "--json", "number,title,state,url,reviewDecision,comments,statusCheckRollup"]
    r = run(cmd, cwd=root)
    if not r.ok:
        return fail("pr.review", "PR_VIEW_FAILED", tail(r.stderr))
    try:
        pr = json.loads(r.stdout)
    except json.JSONDecodeError:
        return fail("pr.review", "PR_PARSE_FAILED", "JSON inválido")

    comments = [{"author": c.get("author", {}).get("login"), "body": (c.get("body") or "")[:400]} for c in (pr.get("comments") or []) if c.get("body")]
    checks = [{"name": c.get("name"), "state": c.get("state") or c.get("conclusion")} for c in (pr.get("statusCheckRollup") or [])]
    failed = [c for c in checks if str(c.get("state", "")).lower() in ("failure", "failed", "error")]

    return emit(
        ok=not failed,
        command="pr.review",
        summary=f"PR #{pr.get('number')} {pr.get('state')} — {len(comments)} comment(s), {len(failed)} fail(s)",
        data={"pr": pr, "comments": comments[:20], "checks": checks[:30], "failed_checks": failed},
        next_steps=(["agent pr checks"] if failed else None),
        verbose=verbose,
        human=human,
    )


def checks(cwd, *, number, verbose, human) -> int:
    root = require_git(cwd, "pr.checks")
    if not isinstance(root, str) or require_gh("pr.checks") is not True:
        return root if not isinstance(root, str) else require_gh("pr.checks")
    cmd = ["gh", "pr", "checks"] + ([str(number)] if number else [])
    r = run(cmd, cwd=root)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    failed = [ln for ln in lines if "fail" in ln.lower()]
    return emit(ok=r.ok and not failed, command="pr.checks", summary=f"{len(lines)} checks, {len(failed)} fail",
                data={"checks": lines[:50], "failed": failed}, verbose=verbose, human=human)


def merge(cwd, *, number, method: str, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "pr.merge")
    if not isinstance(root, str) or require_gh("pr.merge") is not True:
        return root if not isinstance(root, str) else require_gh("pr.merge")
    cmd = ["gh", "pr", "merge"] + ([str(number)] if number else []) + [f"--{method}"]
    r = run(cmd, cwd=root, timeout=60)
    return emit(ok=r.ok, command="pr.merge", summary="merge ok" if r.ok else "merge falhou",
                data={"output": tail(r.stdout + r.stderr)}, verbose=verbose, human=human)


def comment(cwd, *, number, body: str, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "pr.comment")
    if not isinstance(root, str) or require_gh("pr.comment") is not True:
        return root if not isinstance(root, str) else require_gh("pr.comment")
    cmd = ["gh", "pr", "comment"] + ([str(number)] if number else []) + ["--body", body]
    r = run(cmd, cwd=root)
    return emit(ok=r.ok, command="pr.comment", summary="comentário enviado" if r.ok else "falhou",
                data={"output": tail(r.stdout + r.stderr)}, verbose=verbose, human=human)


def close(cwd, *, number, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "pr.close")
    if not isinstance(root, str) or require_gh("pr.close") is not True:
        return root if not isinstance(root, str) else require_gh("pr.close")
    cmd = ["gh", "pr", "close"] + ([str(number)] if number else [])
    r = run(cmd, cwd=root)
    return emit(ok=r.ok, command="pr.close", summary="PR fechada" if r.ok else "falhou", verbose=verbose, human=human)


def pr_diff(cwd, *, number: int | None, max_files: int, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "pr.diff")
    if not isinstance(root, str) or require_gh("pr.diff") is not True:
        return root if not isinstance(root, str) else require_gh("pr.diff")
    sel = str(number) if number else ""
    stat = run(["gh", "pr", "diff", sel, "--stat"], cwd=root, timeout=30)
    names = run(["gh", "pr", "diff", sel, "--name-only"], cwd=root, timeout=30)
    files = [f for f in names.stdout.splitlines() if f.strip()][:max_files]
    return emit(
        ok=stat.ok,
        command="pr.diff",
        summary=f"{len(files)} arquivo(s) na PR",
        data={"files": files, "stat": tail(stat.stdout, max_lines=30), "truncated": len(files) >= max_files},
        verbose=verbose,
        human=human,
    )
