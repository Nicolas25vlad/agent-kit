"""Gestão de variáveis de ambiente — nunca expõe valores completos."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agent_kit.exec_util import git_root
from agent_kit.fs_util import resolve_path
from agent_kit.output import emit, fail

ENV_FILES = (".env.local", ".env", ".env.development", ".env.dev")
EXAMPLE_FILES = (".env.example", ".env.sample", ".env.template")


def _env_base() -> Path:
    return Path(git_root() or resolve_path("."))


def mask_value(value: str) -> str:
    v = value.strip().strip('"').strip("'")
    if not v:
        return "(vazio)"
    if len(v) <= 6:
        return "***"
    return f"{v[:3]}***{v[-3:]}"


def _find_env_file(base: Path, prefer_local: bool = True) -> Path | None:
    order = (".env.local", ".env") if prefer_local else (".env", ".env.local")
    for name in order + [n for n in ENV_FILES if n not in order]:
        p = base / name
        if p.is_file():
            return p
    return None


def _parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        if k:
            out[k] = v.strip().strip('"').strip("'")
    return out


def _format_env_line(key: str, value: str) -> str:
    if re.search(r"\s|#|\"|'", value):
        return f'{key}="{value}"'
    return f"{key}={value}"


def list_env(cwd: str | None, *, verbose: bool, human: bool) -> int:
    base = _env_base()
    found: dict[str, Any] = {}
    for name in ENV_FILES + EXAMPLE_FILES:
        p = base / name
        if p.is_file():
            vars_ = _parse_env(p.read_text(encoding="utf-8", errors="replace"))
            found[name] = {
                "path": str(p),
                "keys": list(vars_.keys()),
                "masked": {k: mask_value(v) for k, v in vars_.items()},
            }
    if not found:
        return emit(
            ok=True,
            command="env.list",
            summary="nenhum .env encontrado",
            data={"cwd": str(base), "files": {}},
            next_steps=["agent env set KEY=valor", "criar .env.example"],
            verbose=verbose,
            human=human,
        )
    total = sum(len(f["keys"]) for f in found.values())
    return emit(
        ok=True,
        command="env.list",
        summary=f"{len(found)} arquivo(s), {total} variável(is) (valores mascarados)",
        data={"cwd": str(base), "files": found},
        verbose=verbose,
        human=human,
    )


def check(cwd: str | None, *, verbose: bool, human: bool) -> int:
    base = _env_base()
    example = next((base / n for n in EXAMPLE_FILES if (base / n).is_file()), None)
    envf = _find_env_file(base)
    if not example:
        return emit(ok=True, command="env.check", summary="sem .env.example", data={"skipped": True}, verbose=verbose, human=human)
    ex_keys = set(_parse_env(example.read_text(encoding="utf-8", errors="replace")).keys())
    cur_keys = set(_parse_env(envf.read_text(encoding="utf-8", errors="replace")).keys()) if envf else set()
    missing = sorted(ex_keys - cur_keys)
    extra = sorted(cur_keys - ex_keys)
    return emit(
        ok=not missing,
        command="env.check",
        summary=f"faltando {len(missing)} chave(s)" if missing else "env ok vs example",
        data={"example": str(example), "env_file": str(envf) if envf else None, "missing": missing, "extra": extra},
        next_steps=[f"agent env set {missing[0]}=..." for missing in missing[:1]] if missing else None,
        verbose=verbose,
        human=human,
    )


def set_var(cwd: str | None, pairs: list[str], *, file: str | None, verbose: bool, human: bool) -> int:
    base = _env_base()
    target = base / (file or ".env.local")
    if target.name == ".env" and (base / ".env.local").exists():
        target = base / ".env.local"

    parsed: dict[str, str] = {}
    for p in pairs:
        if "=" not in p:
            return fail("env.set", "BAD_FORMAT", f"Use KEY=valor, recebido: {p}")
        k, _, v = p.partition("=")
        parsed[k.strip()] = v.strip()

    existing: dict[str, str] = {}
    if target.is_file():
        existing = _parse_env(target.read_text(encoding="utf-8", errors="replace"))
    existing.update(parsed)

    lines = [f"# atualizado por agent-kit\n"] if not target.exists() else []
    lines.extend(_format_env_line(k, v) for k, v in sorted(existing.items()))
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return emit(
        ok=True,
        command="env.set",
        summary=f"{len(parsed)} variável(is) em {target.name}",
        data={
            "file": str(target),
            "set": list(parsed.keys()),
            "masked": {k: mask_value(v) for k, v in parsed.items()},
        },
        warnings=["nunca commite .env com secrets — use .env.local"],
        next_steps=["agent env check", "confirmar .env.local no .gitignore"],
        verbose=verbose,
        human=human,
    )


def ingest(cwd: str | None, blob: str, *, verbose: bool, human: bool) -> int:
    """Parseia blob colado no chat (TOKEN=xxx, linhas múltiplas, export KEY=val)."""
    if not blob.strip():
        return fail("env.ingest", "EMPTY", "Blob vazio")
    vars_ = _parse_env(blob)
    if not vars_:
        # tenta "só o token" — user mandou valor sem key
        token = blob.strip()
        if len(token) > 8 and " " not in token:
            return fail(
                "env.ingest",
                "NO_KEY",
                "Valor sem chave — informe o nome da variável",
                data={"hint": "agent env set GITHUB_TOKEN=<valor>"},
                next_steps=["pergunte ao user qual KEY usar"],
            )
        return fail("env.ingest", "PARSE_FAILED", "Não foi possível parsear KEY=valor")
    pairs = [f"{k}={v}" for k, v in vars_.items()]
    return set_var(cwd, pairs, file=None, verbose=verbose, human=human)
