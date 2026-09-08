"""Filesystem — navegação, busca e leitura otimizados para agentes."""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Any

from agent_kit.exec_util import run
from agent_kit.fs_util import (
    SKIP_DIRS,
    get_agent_cwd,
    has_fd,
    has_rg,
    list_entries,
    parse_rg_line,
    resolve_path,
    set_agent_cwd,
)
from agent_kit.output import emit, fail

RG_GLOBS = ["!node_modules/**", "!.git/**", "!dist/**", "!build/**", "!.next/**", "!target/**"]


def pwd(*, verbose: bool, human: bool) -> int:
    cwd = get_agent_cwd()
    return emit(
        ok=True,
        command="fs.pwd",
        summary=cwd,
        data={"cwd": cwd, "entries": list_entries(Path(cwd), limit=40)},
        verbose=verbose,
        human=human,
    )


def cd(path: str, *, verbose: bool, human: bool) -> int:
    prev = get_agent_cwd()
    try:
        target = set_agent_cwd(path)
    except NotADirectoryError:
        return fail("fs.cd", "NOT_DIR", f"Não é diretório: {path}", data={"cwd": prev})
    except OSError as e:
        return fail("fs.cd", "CD_FAILED", str(e), data={"cwd": prev})

    entries = list_entries(Path(target))
    dirs = sum(1 for e in entries if e["type"] == "dir")
    files = len(entries) - dirs
    return emit(
        ok=True,
        command="fs.cd",
        summary=f"cwd {target} — {dirs} dir(s), {files} file(s)",
        data={
            "cwd": target,
            "previous": prev,
            "shell": f"cd {target}",
            "entries": entries,
        },
        next_steps=[f"agent fs read {entries[0]['path']}" if entries else None],
        verbose=verbose,
        human=human,
    )


def ls(path: str | None, *, depth: int, limit: int, verbose: bool, human: bool) -> int:
    base = resolve_path(path or ".")
    if not base.is_dir():
        return fail("fs.ls", "NOT_FOUND", f"Não é diretório: {base}")

    if depth <= 1:
        entries = list_entries(base, limit=limit)
        return emit(
            ok=True,
            command="fs.ls",
            summary=f"{len(entries)} entrada(s) em {base}",
            data={"path": str(base), "cwd": get_agent_cwd(), "entries": entries},
            verbose=verbose,
            human=human,
        )

    # depth > 1: fd/rg são muito mais rápidos que os.walk
    if has_fd():
        cmd = ["fd", ".", str(base), "--max-depth", str(depth), "--type", "f", "--max-results", str(limit)]
        r = run(cmd, timeout=15)
        entries = [{"name": Path(ln.strip()).name, "path": ln.strip(), "type": "file"} for ln in r.stdout.splitlines() if ln.strip()]
        return emit(
            ok=True, command="fs.ls",
            summary=f"{len(entries)} arquivo(s) sob {base} (depth≤{depth})",
            data={"path": str(base), "entries": entries}, verbose=verbose, human=human,
        )
    if has_rg():
        cmd = ["rg", "--files", "--max-depth", str(depth)]
        for g in RG_GLOBS:
            cmd.extend(["--glob", g])
        r = run(cmd, cwd=str(base), timeout=15)
        files = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()][:limit]
        entries = [{"name": Path(f).name, "path": str(base / f), "type": "file"} for f in files]
        return emit(
            ok=True, command="fs.ls",
            summary=f"{len(entries)} arquivo(s) sob {base} (depth≤{depth})",
            data={"path": str(base), "entries": entries}, verbose=verbose, human=human,
        )

    entries: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        rel = Path(dirpath).relative_to(base)
        if len(rel.parts) >= depth:
            dirnames.clear()
            continue
        for fn in filenames:
            if fn.startswith("."):
                continue
            entries.append({"name": str(rel / fn), "path": str(Path(dirpath) / fn), "type": "file"})
            if len(entries) >= limit:
                break
        if len(entries) >= limit:
            break

    return emit(
        ok=True,
        command="fs.ls",
        summary=f"{len(entries)} arquivo(s) em {base}",
        data={"path": str(base), "entries": entries},
        verbose=verbose,
        human=human,
    )


def grep(
    pattern: str,
    path: str | None,
    *,
    max_hits: int,
    ignore_case: bool,
    glob: str | None,
    file_type: str | None,
    verbose: bool,
    human: bool,
) -> int:
    base = str(resolve_path(path or "."))
    hits: list[dict[str, str]] = []

    if has_rg():
        cmd = [
            "rg", "-n", "--no-heading", "--max-count", str(max_hits),
            "--max-columns", "200", "--color", "never",
        ]
        if ignore_case:
            cmd.append("-i")
        if file_type:
            cmd.extend(["--type", file_type])
        for g in RG_GLOBS:
            cmd.extend(["--glob", g])
        if glob:
            cmd.extend(["--glob", glob])
        cmd.extend([pattern, base])
        r = run(cmd, timeout=20)
        for line in (r.stdout or "").splitlines():
            parsed = parse_rg_line(line)
            if parsed:
                hits.append(parsed)
    else:
        # fallback python — só arquivos pequenos, 1 nível se path é dir
        rx = re.compile(pattern, re.I if ignore_case else 0)
        root = Path(base)
        files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()][:500]
        for fp in files:
            if any(s in fp.parts for s in SKIP_DIRS):
                continue
            if glob and not fnmatch.fnmatch(fp.name, glob):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append({"file": str(fp), "line": str(i), "text": line[:300]})
                    if len(hits) >= max_hits:
                        break
            if len(hits) >= max_hits:
                break

    return emit(
        ok=True,
        command="fs.grep",
        summary=f"{len(hits)} hit(s) /{pattern}/ em {base}",
        data={
            "pattern": pattern,
            "path": base,
            "engine": "rg" if has_rg() else "python",
            "hits": hits,
            "truncated": len(hits) >= max_hits,
        },
        verbose=verbose,
        human=human,
    )


def find(
    query: str,
    path: str | None,
    *,
    max_results: int,
    file_type: str | None,
    verbose: bool,
    human: bool,
) -> int:
    base = str(resolve_path(path or "."))
    results: list[dict[str, str]] = []

    if has_fd():
        cmd = ["fd", "--max-results", str(max_results), "--type", file_type or "f"]
        if not query.startswith("^") and "*" not in query:
            cmd.extend(["--glob", f"*{query}*"])
        else:
            cmd.append(query)
        cmd.append(base)
        r = run(cmd, timeout=15)
        for ln in r.stdout.splitlines():
            if ln.strip():
                results.append({"path": ln.strip(), "name": Path(ln.strip()).name})
    elif has_rg():
        cmd = ["rg", "--files", "--max-count", str(max_results), "--iglob", f"*{query}*"]
        for g in RG_GLOBS:
            cmd.extend(["--glob", g])
        cmd.append(base)
        r = run(cmd, timeout=15)
        for ln in r.stdout.splitlines():
            if ln.strip():
                p = ln.strip()
                results.append({"path": p if os.path.isabs(p) else str(Path(base) / p), "name": Path(p).name})
    else:
        root = Path(base)
        for p in root.rglob(f"*{query}*"):
            if p.is_file() and not any(s in p.parts for s in SKIP_DIRS):
                results.append({"path": str(p), "name": p.name})
                if len(results) >= max_results:
                    break

    return emit(
        ok=bool(results),
        command="fs.find",
        summary=f"{len(results)} arquivo(s) para '{query}'",
        data={"query": query, "path": base, "engine": "fd" if has_fd() else ("rg" if has_rg() else "python"), "files": results[:max_results]},
        next_steps=[f"agent fs read {results[0]['path']}" if results else None],
        verbose=verbose,
        human=human,
    )


def read(path: str, *, offset: int, limit: int, verbose: bool, human: bool) -> int:
    fp = resolve_path(path)
    if not fp.is_file():
        return fail("fs.read", "NOT_FILE", f"Arquivo não encontrado: {fp}")

    try:
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return fail("fs.read", "READ_FAILED", str(e))

    start = max(0, offset - 1)
    chunk = lines[start : start + limit]
    numbered = {str(start + i + 1): line for i, line in enumerate(chunk)}

    return emit(
        ok=True,
        command="fs.read",
        summary=f"{fp.name} L{start + 1}-{start + len(chunk)} de {len(lines)}",
        data={"path": str(fp), "cwd": get_agent_cwd(), "total_lines": len(lines), "offset": start + 1, "lines": numbered},
        verbose=verbose,
        human=human,
    )
