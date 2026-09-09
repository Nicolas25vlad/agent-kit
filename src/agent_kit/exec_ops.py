"""Execução de um binário externo sem shell intermediário."""

from __future__ import annotations

from agent_kit.exec_util import run, tail
from agent_kit.output import emit


def command(program: str, args: list[str], *, verbose: bool, human: bool) -> int:
    r = run([program, *args], timeout=900)
    return emit(
        ok=r.ok,
        command="exec",
        summary=f"{program} {' '.join(args)}".strip(),
        data={"program": program, "args": args, "returncode": r.returncode, "stdout": tail(r.stdout, max_chars=8000), "stderr": tail(r.stderr, max_chars=8000), "duration_ms": r.duration_ms},
        verbose=verbose,
        human=human,
    )
