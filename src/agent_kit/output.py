"""Formato de saída JSON compacto para agentes."""

from __future__ import annotations

import json
import sys
from typing import Any


def emit(
    *,
    ok: bool,
    command: str,
    summary: str,
    data: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    error: dict[str, Any] | None = None,
    next_steps: list[str] | None = None,
    verbose: bool = False,
    human: bool = False,
    extra: dict[str, Any] | None = None,
) -> int:
    payload: dict[str, Any] = {
        "ok": ok,
        "command": command,
        "summary": summary,
    }
    if data:
        payload["data"] = data
    if warnings:
        payload["warnings"] = warnings
    if error:
        payload["error"] = error
    if next_steps:
        payload["next"] = [s for s in next_steps if s]
    if extra:
        payload.update(extra)

    if human:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {summary}")
        if warnings:
            for w in warnings:
                print(f"  warn: {w}")
        if error:
            print(f"  error: {error.get('code')}: {error.get('message')}")
        if next_steps:
            print("  next:")
            for step in next_steps:
                print(f"    - {step}")
        if verbose and data:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    return 0 if ok else 1


def fail(command: str, code: str, message: str, **kwargs: Any) -> int:
    return emit(
        ok=False,
        command=command,
        summary=message,
        error={"code": code, "message": message},
        **kwargs,
    )
