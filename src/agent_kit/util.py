"""Helpers compartilhados — mantém os módulos enxutos."""

from __future__ import annotations

import re
from typing import Any

from agent_kit.exec_util import git_root, run
from agent_kit.output import fail

SECRET_PATTERNS = (
    r"\.env$",
    r"\.env\.",
    r"credentials\.json$",
    r"secrets\.(ya?ml|json)$",
    r"id_rsa$",
    r"\.pem$",
    r"\.p12$",
    r"\.key$",
)


def parse_status(porcelain: str) -> dict[str, Any]:
    branch = None
    ahead = behind = 0
    staged, unstaged, untracked, conflicted = [], [], [], []

    for line in porcelain.splitlines():
        if line.startswith("#"):
            if line.startswith("# branch.head "):
                branch = line.removeprefix("# branch.head ").strip()
            elif line.startswith("# branch.ab "):
                p = line.split()
                if len(p) >= 4:
                    ahead, behind = int(p[2].lstrip("+") or 0), int(p[3].lstrip("-") or 0)
            continue
        if line.startswith("u ") or "DD" in line[:2] or "AA" in line[:2]:
            conflicted.append(line[3:].strip())
        elif line.startswith("? "):
            untracked.append(line[2:].strip())
        elif line.startswith(("1 ", "2 ")):
            p = line.split(" ", 8)
            if len(p) >= 9:
                xy, path = p[1], p[8].strip()
                if xy[0] != ".":
                    staged.append(path)
                if xy[1] != ".":
                    unstaged.append(path)
        elif len(line) >= 4 and line[2] == " ":
            xy, path = line[:2], line[3:].strip()
            if xy[0] not in " ?":
                staged.append(path)
            if xy[1] != " ":
                unstaged.append(path)

    return {
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "conflicted": conflicted,
        "dirty": bool(staged or unstaged or untracked or conflicted),
    }


def looks_secret(path: str) -> bool:
    return any(re.search(p, path, re.I) for p in SECRET_PATTERNS)


def is_ignored(path: str, root: str) -> bool:
    return run(["git", "check-ignore", "-q", path], cwd=root, timeout=5).ok


def require_git(cwd: str | None, cmd: str) -> str | int:
    root = git_root(cwd)
    if not root:
        return fail(cmd, "NOT_A_REPO", "Diretório atual não é um repositório git")
    return root


def require_gh(cmd: str) -> bool | int:
    if run(["gh", "--version"], timeout=5).ok:
        return True
    return fail(cmd, "GH_MISSING", "GitHub CLI (gh) não encontrado no PATH")
