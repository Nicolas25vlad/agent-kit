"""Prep e composites de 2ª ordem."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_kit.config import CONFIG_NAME, load
from agent_kit.detect import detect_all
from agent_kit.exec_util import git_root, run
from agent_kit.output import emit, fail
from agent_kit.util import parse_status


def task(cwd: str | None, *, with_pr: bool, verbose: bool, human: bool) -> int:
    root = git_root(cwd) or cwd or "."
    data: dict[str, Any] = {"root": root, "config": load(root) if git_root(cwd) else None}

    status_r = run(["git", "status", "--porcelain=v2", "-b"], cwd=root, timeout=10) if git_root(cwd) else None
    if status_r and status_r.ok:
        parsed = parse_status(status_r.stdout)
        data["git"] = {
            "branch": parsed["branch"],
            "dirty": parsed["dirty"],
            "counts": {k: len(parsed[k]) for k in ("staged", "unstaged", "untracked", "conflicted")},
            "conflicted": parsed["conflicted"],
        }
    else:
        data["git"] = None

    data["detect"] = detect_all(root)

    if with_pr and git_root(cwd) and run(["gh", "--version"], timeout=3).ok:
        pr_r = run(["gh", "pr", "view", "--json", "number,title,state,url"], cwd=root, timeout=15)
        if pr_r.ok:
            try:
                data["pr"] = json.loads(pr_r.stdout)
            except json.JSONDecodeError:
                data["pr"] = None
        else:
            data["pr"] = None

    g = data.get("git") or {}
    tools = [t["kind"] for t in data["detect"].get("tools", [])]
    parts = []
    if g.get("branch"):
        parts.append(f"branch {g['branch']}")
    parts.append("dirty" if g.get("dirty") else "clean")
    if tools:
        parts.append(f"tools: {','.join(dict.fromkeys(tools))}")

    next_steps = []
    if g.get("conflicted"):
        next_steps.append("agent git conflicts")
    elif g.get("dirty"):
        next_steps.append("agent git suggest")
    if not Path(root, CONFIG_NAME).is_file() and git_root(cwd):
        next_steps.append("agent config learn")
    if "test" in tools:
        next_steps.append("agent test run")

    return emit(
        ok=not g.get("conflicted"),
        command="prep.task",
        summary="; ".join(parts) or "contexto carregado",
        data=data,
        next_steps=next_steps or None,
        verbose=verbose,
        human=human,
    )


def pr_prep(cwd, *, verbose: bool, human: bool) -> int:
    root = git_root(cwd)
    if not root:
        return fail("prep.pr", "NOT_A_REPO", "Fora de um repositório git")

    data: dict[str, Any] = {"root": root, "config": load(root)}
    status_r = run(["git", "status", "--porcelain=v2", "-b"], cwd=root, timeout=10)
    if status_r.ok:
        parsed = parse_status(status_r.stdout)
        data["git"] = {"branch": parsed["branch"], "dirty": parsed["dirty"], "conflicted": parsed["conflicted"]}

    pr_r = run(["gh", "pr", "view", "--json", "number,title,state,url,reviewDecision"], cwd=root, timeout=15)
    if pr_r.ok:
        try:
            data["pr"] = json.loads(pr_r.stdout)
        except json.JSONDecodeError:
            data["pr"] = None
    else:
        data["pr"] = None

    ci_r = run(["gh", "run", "list", "--limit", "3", "--json", "name,status,conclusion,url"], cwd=root, timeout=15)
    if ci_r.ok:
        try:
            data["ci"] = json.loads(ci_r.stdout)
        except json.JSONDecodeError:
            data["ci"] = []

    parts = []
    if data.get("pr"):
        parts.append(f"PR #{data['pr'].get('number')} {data['pr'].get('state')}")
    ci_failed = [c for c in (data.get("ci") or []) if c.get("conclusion") == "failure"]
    if ci_failed:
        parts.append(f"{len(ci_failed)} CI fail")
    elif data.get("ci"):
        parts.append("CI ok")

    next_steps = []
    if ci_failed:
        next_steps.append("agent fix-ci")
    if data.get("pr"):
        next_steps.append("agent pr review")
        next_steps.append("agent pr diff")

    return emit(
        ok=not ci_failed and not (data.get("git") or {}).get("conflicted"),
        command="prep.pr",
        summary=" — ".join(parts) or "sem PR/CI",
        data=data,
        next_steps=next_steps or None,
        verbose=verbose,
        human=human,
    )
