"""Operações git compostas."""

from __future__ import annotations

import json
from typing import Any

from agent_kit.commit_msg import suggest as build_suggest
from agent_kit.exec_util import run, tail
from agent_kit.output import emit, fail
from agent_kit.util import is_ignored, looks_secret, parse_status, require_git


def snapshot(cwd: str | None, *, verbose: bool, human: bool, include_diff: bool) -> int:
    root = require_git(cwd, "git.snapshot")
    if not isinstance(root, str):
        return root

    status_r = run(["git", "status", "--porcelain=v2", "-b"], cwd=root, timeout=10)
    if not status_r.ok:
        return fail("git.snapshot", "GIT_STATUS_FAILED", tail(status_r.stderr))

    parsed = parse_status(status_r.stdout)
    stat_r = run(["git", "diff", "--stat", "HEAD"], cwd=root, timeout=15)
    log_r = run(["git", "log", "-1", "--format=%h %s (%an, %ar)"], cwd=root, timeout=5)
    remote_r = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=root, timeout=5)

    data: dict[str, Any] = {
        "root": root,
        "branch": parsed["branch"],
        "tracking": remote_r.stdout.strip() if remote_r.ok else None,
        "ahead": parsed["ahead"],
        "behind": parsed["behind"],
        "counts": {k: len(parsed[k]) for k in ("staged", "unstaged", "untracked", "conflicted")},
        "files": {k: parsed[k][:50] for k in ("staged", "unstaged", "untracked", "conflicted")},
        "last_commit": log_r.stdout.strip() if log_r.ok else None,
        "diff_stat": tail(stat_r.stdout, max_lines=20).strip() or None,
    }
    if include_diff and parsed["dirty"]:
        data["diff"] = tail(run(["git", "diff", "HEAD"], cwd=root, timeout=20).stdout, max_lines=80, max_chars=8000)

    parts = [f"branch {parsed['branch'] or '?'}"]
    if parsed["conflicted"]:
        parts.append(f"{len(parsed['conflicted'])} conflito(s)")
    elif parsed["dirty"]:
        parts.append(f"{data['counts']['staged']} staged, {data['counts']['unstaged']} unstaged, {data['counts']['untracked']} untracked")
    else:
        parts.append("working tree limpo")

    risky = [f for f in parsed["staged"] + parsed["unstaged"] + parsed["untracked"] if looks_secret(f)]
    return emit(
        ok=not parsed["conflicted"],
        command="git.snapshot",
        summary="; ".join(parts),
        data=data,
        warnings=[f"sensíveis: {', '.join(risky[:5])}"] if risky else None,
        next_steps=(["agent git suggest → agent git ship -m \"...\""] if parsed["dirty"] and not parsed["conflicted"] else None),
        verbose=verbose,
        human=human,
    )


def suggest_msg(cwd, *, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.suggest")
    if not isinstance(root, str):
        return root
    data = build_suggest(root, staged_only=False)
    if not data["files"]:
        return fail("git.suggest", "NOTHING_TO_COMMIT", "Sem mudanças para sugerir mensagem")
    draft = data["message"]
    return emit(
        ok=True,
        command="git.suggest",
        summary=f"rascunho: {draft}",
        data={**data, "draft": draft, "note": "rascunho heurístico — revise e escreva -m explicitamente"},
        next_steps=['agent git ship -m "sua mensagem revisada"'],
        verbose=verbose,
        human=human,
    )


def commit(cwd, *, message: str, all_files: bool, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.commit")
    if not isinstance(root, str):
        return root
    parsed = parse_status(run(["git", "status", "--porcelain=v2", "-b"], cwd=root).stdout)
    if parsed["conflicted"]:
        return fail("git.commit", "MERGE_CONFLICT", "Conflitos não resolvidos")
    if not parsed["dirty"] and not all_files:
        return fail("git.commit", "NOTHING_TO_COMMIT", "Working tree limpo")

    add_cmd = ["git", "add", "-A"] if all_files else ["git", "add", "-u"]
    if not run(add_cmd, cwd=root).ok:
        return fail("git.commit", "GIT_ADD_FAILED", "git add falhou")

    commit_r = run(["git", "commit", "-m", message], cwd=root)
    if not commit_r.ok:
        return fail("git.commit", "GIT_COMMIT_FAILED", tail(commit_r.stderr or commit_r.stdout))
    sha = run(["git", "rev-parse", "--short", "HEAD"], cwd=root).stdout.strip()
    return emit(ok=True, command="git.commit", summary=f"commit {sha}: {message}",
                data={"commit": sha, "message": message}, next_steps=["agent git sync"], verbose=verbose, human=human)


def ship(cwd, *, message: str, dry_run, no_push, open_pr, with_tests, all_files, base, verbose, human) -> int:
    root = require_git(cwd, "git.ship")
    if not isinstance(root, str):
        return root

    parsed = parse_status(run(["git", "status", "--porcelain=v2", "-b"], cwd=root).stdout)
    if parsed["conflicted"]:
        return fail("git.ship", "MERGE_CONFLICT", "Conflitos não resolvidos", data={"conflicted": parsed["conflicted"]})
    if not parsed["dirty"] and not all_files:
        return fail("git.ship", "NOTHING_TO_COMMIT", "Working tree limpo")

    candidates = parsed["staged"] + parsed["unstaged"] + parsed["untracked"]
    blocked = [f for f in candidates if looks_secret(f) and not is_ignored(f, root)]
    if blocked:
        return fail("git.ship", "SECRETS_BLOCKED", f"Arquivos sensíveis: {', '.join(blocked[:5])}", data={"blocked_files": blocked})

    if with_tests:
        from agent_kit.test_ops import run_tests
        if run_tests(root, filter_arg=None, verbose=False, human=False) != 0:
            return fail("git.ship", "TESTS_FAILED", "Testes falharam", next_steps=["agent test run"])

    add_cmd = ["git", "add", "-A"] if all_files else ["git", "add", "-u"]

    if dry_run:
        return emit(ok=True, command="git.ship", summary=f"[dry-run] {message!r}",
                    data={"would_add": add_cmd, "would_push": not no_push, "would_pr": open_pr, "message": message, "files": candidates[:30]},
                    verbose=verbose, human=human)

    if not run(add_cmd, cwd=root).ok:
        return fail("git.ship", "GIT_ADD_FAILED", "git add falhou")
    after = parse_status(run(["git", "status", "--porcelain=v2", "-b"], cwd=root).stdout)
    staged_blocked = [f for f in after["staged"] if looks_secret(f) and not is_ignored(f, root)]
    if staged_blocked:
        run(["git", "reset", "HEAD"], cwd=root)
        return fail("git.ship", "SECRETS_BLOCKED", f"Pós-stage bloqueado: {staged_blocked}")

    commit_r = run(["git", "commit", "-m", message], cwd=root)
    if not commit_r.ok:
        return fail("git.ship", "GIT_COMMIT_FAILED", tail(commit_r.stderr or commit_r.stdout))

    sha = run(["git", "rev-parse", "--short", "HEAD"], cwd=root).stdout.strip()
    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    data: dict[str, Any] = {"commit": sha, "branch": branch, "message": message}
    warnings: list[str] = []

    if not no_push:
        push_r = run(["git", "push", "-u", "origin", "HEAD"], cwd=root, timeout=120)
        if not push_r.ok:
            return fail("git.ship", "GIT_PUSH_FAILED", tail(push_r.stderr or push_r.stdout), data=data)
        data["pushed"] = True

    pr_url = None
    if open_pr and not no_push:
        pr_cmd = ["gh", "pr", "create", "--title", message] + (["--base", base] if base else [])
        pr_create = run(pr_cmd, cwd=root, timeout=60)
        if pr_create.ok:
            pr_url = pr_create.stdout.strip()
            view = run(["gh", "pr", "view", pr_url, "--json", "url,number,title"], cwd=root)
            if view.ok:
                try:
                    data["pr"] = json.loads(view.stdout)
                    pr_url = data["pr"].get("url") or pr_url
                except json.JSONDecodeError:
                    data["pr"] = {"url": pr_url}
        else:
            warnings.append("push ok, PR falhou — agent pr open")

    summary = f"commit {sha} em {branch}" + (" (push ok)" if data.get("pushed") else "")
    if pr_url:
        summary += f" — {pr_url}"
    return emit(ok=True, command="git.ship", summary=summary, data=data, warnings=warnings or None, verbose=verbose, human=human)


def sync(cwd, *, rebase, dry_run, verbose, human) -> int:
    root = require_git(cwd, "git.sync")
    if not isinstance(root, str):
        return root
    if not run(["git", "fetch", "--prune"], cwd=root, timeout=60).ok:
        return fail("git.sync", "GIT_FETCH_FAILED", "fetch falhou")
    if not run(["git", "rev-parse", "@{u}"], cwd=root).ok:
        return fail("git.sync", "NO_UPSTREAM", "Sem upstream — git push -u origin HEAD")
    if dry_run:
        ahead = run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd=root).stdout.strip()
        behind = run(["git", "rev-list", "--count", "HEAD..@{u}"], cwd=root).stdout.strip()
        return emit(ok=True, command="git.sync", summary=f"[dry-run] ↑{ahead} ↓{behind}", data={"ahead": ahead, "behind": behind}, verbose=verbose, human=human)
    pull = ["git", "pull", "--rebase", "--autostash"] if rebase else ["git", "pull", "--ff-only"]
    if not run(pull, cwd=root, timeout=120).ok:
        return fail("git.sync", "GIT_PULL_FAILED", "pull falhou")
    if not run(["git", "push"], cwd=root, timeout=120).ok:
        return fail("git.sync", "GIT_PUSH_FAILED", "push falhou")
    return emit(ok=True, command="git.sync", summary="sync ok", verbose=verbose, human=human)


def diff(cwd, *, base, stat_only, cached, check, max_lines, verbose, human) -> int:
    root = require_git(cwd, "git.diff")
    if not isinstance(root, str):
        return root
    target = base or (None if cached else "HEAD")
    cmd = ["git", "diff"]
    if cached:
        cmd.append("--cached")
    if check:
        cmd.append("--check")
    if stat_only:
        cmd.append("--stat")
    if target:
        cmd.append(target)
    diff_r = run(cmd, cwd=root, timeout=30)
    names_cmd = ["git", "diff"] + (["--cached"] if cached else []) + ["--name-only"] + ([target] if target else [])
    files = run(names_cmd, cwd=root).stdout.splitlines()
    return emit(ok=diff_r.ok, command="git.diff", summary=f"{len(files)} arquivo(s)" + (f" vs {target}" if target else " staged"),
                data={"base": target, "cached": cached, "check": check, "files": files[:100], "diff": tail(diff_r.stdout or diff_r.stderr, max_lines=max_lines)}, verbose=verbose, human=human)


def remote(cwd, *, verbose, human) -> int:
    root = require_git(cwd, "git.remote")
    if not isinstance(root, str):
        return root
    r = run(["git", "remote", "-v"], cwd=root)
    return emit(ok=r.ok, command="git.remote", summary="remotes listados", data={"output": r.stdout.strip()}, verbose=verbose, human=human)


def config(cwd, *, key, value, global_scope, verbose, human) -> int:
    root = require_git(cwd, "git.config")
    if not isinstance(root, str):
        return root
    cmd = ["git", "config"] + (["--global"] if global_scope else []) + [key] + ([value] if value is not None else [])
    r = run(cmd, cwd=root)
    return emit(ok=r.ok, command="git.config", summary=f"config {key}", data={"key": key, "value": r.stdout.strip() if value is None else value, "global": global_scope}, verbose=verbose, human=human)


def tag(cwd, *, name, message, delete, verbose, human) -> int:
    root = require_git(cwd, "git.tag")
    if not isinstance(root, str):
        return root
    if delete and name:
        r = run(["git", "tag", "-d", name], cwd=root)
    elif name:
        r = run(["git", "tag"] + (["-a", name, "-m", message] if message else [name]), cwd=root)
    else:
        r = run(["git", "tag", "--sort=-creatordate"], cwd=root)
    return emit(ok=r.ok, command="git.tag", summary="tags listadas" if not name else f"tag {name}", data={"output": (r.stdout or r.stderr).strip()}, verbose=verbose, human=human)


def check_ignore(cwd, *, paths, verbose, human) -> int:
    root = require_git(cwd, "git.check-ignore")
    if not isinstance(root, str):
        return root
    r = run(["git", "check-ignore", "-v", "--"] + paths, cwd=root)
    return emit(ok=r.ok, command="git.check-ignore", summary=f"{len(paths)} caminho(s) consultado(s)", data={"ignored": r.stdout.splitlines()}, verbose=verbose, human=human)


def log(cwd, *, count: int, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.log")
    if not isinstance(root, str):
        return root
    r = run(["git", "log", f"-{count}", "--format=%h|%s|%an|%ar"], cwd=root)
    commits = []
    for line in r.stdout.splitlines():
        p = line.split("|", 3)
        if len(p) == 4:
            commits.append({"sha": p[0], "subject": p[1], "author": p[2], "when": p[3]})
    return emit(ok=True, command="git.log", summary=f"{len(commits)} commit(s)", data={"commits": commits}, verbose=verbose, human=human)


def branch(cwd, *, create: str | None, switch: str | None, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.branch")
    if not isinstance(root, str):
        return root
    if create:
        r = run(["git", "checkout", "-b", create], cwd=root)
        if not r.ok:
            return fail("git.branch", "BRANCH_CREATE_FAILED", tail(r.stderr))
        return emit(ok=True, command="git.branch", summary=f"branch criada: {create}", data={"branch": create, "created": True}, verbose=verbose, human=human)
    if switch:
        r = run(["git", "checkout", switch], cwd=root)
        if not r.ok:
            return fail("git.branch", "BRANCH_SWITCH_FAILED", tail(r.stderr))
        return emit(ok=True, command="git.branch", summary=f"em branch {switch}", data={"branch": switch}, verbose=verbose, human=human)
    current = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    branches = [b.strip().lstrip("* ") for b in run(["git", "branch", "--format=%(refname:short)"], cwd=root).stdout.splitlines() if b.strip()]
    return emit(ok=True, command="git.branch", summary=f"branch atual: {current}", data={"current": current, "branches": branches[:50]}, verbose=verbose, human=human)


def stash(cwd, *, action: str, message: str | None, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.stash")
    if not isinstance(root, str):
        return root
    if action == "list":
        r = run(["git", "stash", "list"], cwd=root)
        items = r.stdout.strip().splitlines() if r.stdout.strip() else []
        return emit(ok=True, command="git.stash", summary=f"{len(items)} stash(es)", data={"stashes": items[:20]}, verbose=verbose, human=human)
    if action == "pop":
        r = run(["git", "stash", "pop"], cwd=root)
        return emit(ok=r.ok, command="git.stash", summary="stash pop" if r.ok else "pop falhou",
                    data={"output": tail(r.stdout + r.stderr)}, verbose=verbose, human=human)
    cmd = ["git", "stash", "push", "-m", message or "agent-kit stash"]
    r = run(cmd, cwd=root)
    return emit(ok=r.ok, command="git.stash", summary="stash push ok" if r.ok else "stash falhou",
                data={"output": tail(r.stdout + r.stderr)}, verbose=verbose, human=human)


def stage(cwd, *, paths: list[str], all_files: bool, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.add")
    if not isinstance(root, str):
        return root
    cmd = ["git", "add", "-A"] if all_files else (["git", "add", "-u"] if not paths else ["git", "add"] + paths)
    r = run(cmd, cwd=root)
    if not r.ok:
        return fail("git.add", "GIT_ADD_FAILED", tail(r.stderr))
    parsed = parse_status(run(["git", "status", "--porcelain=v2", "-b"], cwd=root).stdout)
    return emit(ok=True, command="git.add", summary=f"{len(parsed['staged'])} staged",
                data={"staged": parsed["staged"][:50]}, next_steps=["agent git suggest", 'agent git ship -m "..."'], verbose=verbose, human=human)


def discard(cwd, *, all_files: bool, paths: list[str], verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.discard")
    if not isinstance(root, str):
        return root
    if all_files:
        cmds = [["git", "reset", "--hard", "HEAD"], ["git", "clean", "-fd"]]
    else:
        cmds = [["git", "restore", "--staged", "--worktree"] + paths] if paths else [["git", "restore", "."]]
    for cmd in cmds:
        r = run(cmd, cwd=root)
        if not r.ok:
            return fail("git.discard", "DISCARD_FAILED", tail(r.stderr))
    return emit(ok=True, command="git.discard", summary="mudanças descartadas", verbose=verbose, human=human)


def conflicts(cwd, *, verbose: bool, human: bool) -> int:
    root = require_git(cwd, "git.conflicts")
    if not isinstance(root, str):
        return root
    parsed = parse_status(run(["git", "status", "--porcelain=v2", "-b"], cwd=root).stdout)
    files = parsed["conflicted"]
    if not files:
        return emit(ok=True, command="git.conflicts", summary="sem conflitos", data={"files": []}, verbose=verbose, human=human)
    snippets: dict[str, str] = {}
    for f in files[:10]:
        fp = __import__("pathlib").Path(root) / f
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
            markers = [ln for ln in text.splitlines() if ln.startswith(("<<<<<<<", "=======", ">>>>>>>"))]
            snippets[f] = "\n".join(markers[:12]) or "(sem marcadores visíveis)"
        except OSError:
            snippets[f] = "(não legível)"
    return emit(
        ok=False,
        command="git.conflicts",
        summary=f"{len(files)} arquivo(s) em conflito",
        data={"files": files, "markers": snippets},
        next_steps=["resolver conflitos manualmente", "agent git snapshot"],
        verbose=verbose,
        human=human,
    )
