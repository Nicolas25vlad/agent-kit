"""Operações de repositório: clone, find, info."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent_kit.exec_util import git_root, run
from agent_kit.output import emit, fail

SEARCH_ROOTS = [
    "~/Projects",
    "~/Developer",
    "~/code",
    "~/repos",
    "~/Documents",
]


def _expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def info(cwd: str | None, *, verbose: bool, human: bool) -> int:
    root = git_root(cwd)
    if not root:
        return emit(
            ok=True,
            command="repo.info",
            summary="fora de um repositório git",
            data={"cwd": os.path.abspath(cwd or os.getcwd()), "git_root": None},
            verbose=verbose,
            human=human,
        )

    remote_r = run(["git", "remote", "get-url", "origin"], cwd=root, timeout=5)
    branch_r = run(["git", "branch", "--show-current"], cwd=root, timeout=5)

    return emit(
        ok=True,
        command="repo.info",
        summary=f"{Path(root).name} ({branch_r.stdout.strip()})",
        data={
            "root": root,
            "name": Path(root).name,
            "branch": branch_r.stdout.strip() if branch_r.ok else None,
            "origin": remote_r.stdout.strip() if remote_r.ok else None,
            "cwd": os.path.abspath(cwd or os.getcwd()),
        },
        verbose=verbose,
        human=human,
    )


def find(name: str, *, verbose: bool, human: bool) -> int:
    query = name.lower().strip()
    matches: list[dict[str, Any]] = []

    for root_glob in SEARCH_ROOTS:
        base = Path(_expand(root_glob))
        if not base.exists():
            continue
        try:
            for child in base.iterdir():
                if not child.is_dir():
                    continue
                if query in child.name.lower():
                    is_git = (child / ".git").exists()
                    matches.append({"path": str(child), "name": child.name, "git": is_git})
        except OSError:
            continue

    if not matches:
        return fail(
            "repo.find",
            "NOT_FOUND",
            f"Nenhum diretório correspondendo a '{name}'",
            data={"searched": [_expand(r) for r in SEARCH_ROOTS]},
            next_steps=[f"agent repo clone <url> --dest ~/Projects/{name}"],
        )

    best = sorted(matches, key=lambda m: (not m["git"], len(m["name"])))[0]
    return emit(
        ok=True,
        command="repo.find",
        summary=f"{len(matches)} match(es); melhor: {best['path']}",
        data={"query": name, "matches": matches[:20], "recommended": best},
        next_steps=[f"cd {best['path']}"],
        verbose=verbose,
        human=human,
    )


def clone(
    url: str,
    *,
    dest: str | None,
    depth: int | None,
    verbose: bool,
    human: bool,
) -> int:
    if dest:
        target = _expand(dest)
    else:
        name = url.rstrip("/").split("/")[-1].removesuffix(".git")
        target = _expand(f"~/Projects/{name}")

    if Path(target).exists():
        return fail(
            "repo.clone",
            "DEST_EXISTS",
            f"Destino já existe: {target}",
            next_steps=["agent repo info", f"cd {target}"],
        )

    cmd = ["git", "clone"]
    if depth:
        cmd.extend(["--depth", str(depth)])
    cmd.extend([url, target])

    result = run(cmd, timeout=300)
    if not result.ok:
        return fail("repo.clone", "CLONE_FAILED", result.stderr.strip() or result.stdout.strip())

    return emit(
        ok=True,
        command="repo.clone",
        summary=f"clonado em {target}",
        data={"url": url, "path": target},
        next_steps=[f"cd {target}", "agent git snapshot"],
        verbose=verbose,
        human=human,
    )
