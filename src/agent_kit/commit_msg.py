"""Geração heurística de mensagens de commit (Conventional Commits PT-BR)."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from agent_kit.exec_util import run, tail


def _files_and_diff(root: str, staged_only: bool) -> tuple[list[str], str, str]:
    if staged_only:
        files_r = run(["git", "diff", "--cached", "--name-only"], cwd=root)
        diff_r = run(["git", "diff", "--cached"], cwd=root, timeout=15)
        stat_r = run(["git", "diff", "--cached", "--stat"], cwd=root)
    else:
        files_r = run(["git", "diff", "--name-only", "HEAD"], cwd=root)
        diff_r = run(["git", "diff", "HEAD"], cwd=root, timeout=15)
        stat_r = run(["git", "diff", "--stat", "HEAD"], cwd=root)
    files = [f for f in files_r.stdout.splitlines() if f.strip()]
    return files, tail(diff_r.stdout, max_lines=60, max_chars=4000), stat_r.stdout.strip()


def _scope(files: list[str]) -> str | None:
    parts: list[str] = []
    for f in files:
        p = Path(f).parts
        if len(p) >= 2 and p[0] in ("src", "lib", "app", "pkg", "internal", "cmd"):
            parts.append(p[1])
        elif len(p) >= 2:
            parts.append(p[0])
    if not parts:
        return None
    return Counter(parts).most_common(1)[0][0]


def _commit_type(files: list[str], diff: str) -> str:
    low = diff.lower()
    names = " ".join(files).lower()
    if any(x in names for x in ("readme", "doc", "docs/", ".md")) and not any(
        x.endswith((".py", ".ts", ".tsx", ".js", ".go", ".rs")) for x in files
    ):
        return "docs"
    if "test" in names or "/test" in names or "spec." in names:
        return "test"
    if re.search(r"\b(fix|bug|erro|error|corrige|hotfix)\b", low):
        return "fix"
    if re.search(r"\b(refactor|rename|move|extract)\b", low):
        return "refactor"
    if re.search(r"\b(chore|deps|bump|config|ci)\b", low) or any(
        x.endswith((".lock", ".json", ".yaml", ".yml", ".toml")) and "package" not in x for x in files
    ):
        return "chore"
    added = diff.count("+++ b/")
    return "feat" if added >= len(files) // 2 else "chore"


def _description(files: list[str], diff: str) -> str:
    if len(files) == 1:
        name = Path(files[0]).stem.replace("_", " ").replace("-", " ")
        return f"atualiza {name}"[:72]
    verbs = re.findall(r"^\+.*(?:def |class |function |export )(\w+)", diff, re.M)
    if verbs:
        return f"adiciona {verbs[0]}"[:72]
    dirs = Counter(Path(f).parent.name for f in files)
    if dirs:
        top = dirs.most_common(1)[0][0]
        if top and top != ".":
            return f"atualiza {top} ({len(files)} arquivos)"[:72]
    return f"atualiza {len(files)} arquivos"[:72]


def suggest(root: str, *, staged_only: bool = False) -> dict[str, Any]:
    files, diff, stat = _files_and_diff(root, staged_only)
    if not files:
        status = run(["git", "status", "--porcelain"], cwd=root).stdout
        for ln in status.splitlines():
            if ln.startswith("??"):
                files.append(ln[3:].strip())
            elif ln.startswith("? "):
                files.append(ln[2:].strip())
        stat = f"{len(files)} untracked"
    if not files:
        return {"message": "", "type": "chore", "scope": None, "files": [], "files_count": 0, "diff_stat": None, "diff_excerpt": None}
    tipo = _commit_type(files, diff)
    scope = _scope(files)
    desc = _description(files, diff)
    if scope:
        message = f"{tipo}({scope}): {desc}"
    else:
        message = f"{tipo}: {desc}"
    return {
        "message": message,
        "type": tipo,
        "scope": scope,
        "files": files[:30],
        "files_count": len(files),
        "diff_stat": stat or None,
        "diff_excerpt": diff[:1500] if diff else None,
    }
