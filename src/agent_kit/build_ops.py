"""Build, lint e instalação de deps."""

from __future__ import annotations

from pathlib import Path

from agent_kit.detect import detect_all, node_run, pick_tool
from agent_kit.exec_util import git_root, run, tail
from agent_kit.output import emit, fail


def _root(cwd: str | None) -> str:
    return git_root(cwd) or cwd or "."


def run_target(cwd: str | None, *, target: str, verbose: bool, human: bool) -> int:
    root = _root(cwd)
    cmd = pick_tool(root, target)
    if not cmd:
        cmd = node_run(Path(root), target)
    if not cmd:
        return fail("build.run", "NO_TARGET", f"Nenhum comando '{target}' detectado", data=detect_all(root))

    r = run(cmd, cwd=root, timeout=600)
    return emit(
        ok=r.ok,
        command="build.run",
        summary=f"{target}: {'ok' if r.ok else 'falhou'} ({r.duration_ms}ms)",
        data={"target": target, "cmd": cmd, "exit_code": r.returncode, "output": tail(r.stdout + r.stderr)},
        next_steps=None if r.ok else [f"corrigir e rodar agent build run --target {target}"],
        verbose=verbose,
        human=human,
    )


def install(cwd: str | None, *, verbose: bool, human: bool) -> int:
    root = _root(cwd)
    p = Path(root)
    det = detect_all(root)

    if inst := det.get("install"):
        cmd = inst["cmd"]
    elif (p / "requirements.txt").exists():
        cmd = ["python3", "-m", "pip", "install", "-r", "requirements.txt"]
    elif (p / "go.mod").exists():
        cmd = ["go", "mod", "download"]
    elif (p / "Cargo.toml").exists():
        cmd = ["cargo", "fetch"]
    else:
        return fail("deps.install", "NO_DEPS", "Nenhum gerenciador de deps detectado", data=det)

    r = run(cmd, cwd=root, timeout=600)
    return emit(
        ok=r.ok,
        command="deps.install",
        summary=f"deps: {'ok' if r.ok else 'falhou'}",
        data={"cmd": cmd, "output": tail(r.stdout + r.stderr, max_lines=20)},
        verbose=verbose,
        human=human,
    )
