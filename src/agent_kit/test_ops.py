"""Detecção e execução de testes."""

from __future__ import annotations

from agent_kit.detect import detect_all, pick_tool
from agent_kit.exec_util import git_root, run, tail
from agent_kit.output import emit, fail


def detect(cwd: str | None, *, verbose: bool, human: bool) -> int:
    root = git_root(cwd) or cwd or "."
    det = detect_all(root)
    test_cmds = [t for t in det.get("tools", []) if t.get("kind") == "test"]
    return emit(
        ok=bool(test_cmds),
        command="test.detect",
        summary=f"{len(test_cmds)} runner(s) detectado(s)" if test_cmds else "nenhum runner",
        data={"runners": test_cmds, "detect": det},
        next_steps=["agent test run"] if test_cmds else None,
        verbose=verbose,
        human=human,
    )


def run_tests(cwd: str | None, *, filter_arg: str | None, verbose: bool, human: bool) -> int:
    root = git_root(cwd) or cwd or "."
    runner = pick_tool(root, "test")
    if not runner:
        return fail("test.run", "NO_RUNNER", "Nenhum runner detectado", next_steps=["agent test detect"])

    cmd = list(runner)
    if filter_arg and "pytest" in cmd[0]:
        cmd.append(filter_arg)
    elif filter_arg:
        cmd.extend(["--", filter_arg])

    r = run(cmd, cwd=root, timeout=600)
    return emit(
        ok=r.ok,
        command="test.run",
        summary=f"testes: {'ok' if r.ok else 'falhou'} ({r.duration_ms}ms)",
        data={"cmd": cmd, "exit_code": r.returncode, "output": tail(r.stdout + r.stderr)},
        next_steps=None if r.ok else ["corrigir e agent test run"],
        verbose=verbose,
        human=human,
    )
