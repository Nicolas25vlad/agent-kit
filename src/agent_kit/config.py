"""Config do projeto — .agent-kit.toml na raiz do git (IA escreve, todos leem)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_kit.exec_util import git_root

CONFIG_NAME = ".agent-kit.toml"

DEFAULTS: dict[str, Any] = {
    "commands": {},
    "paths": {"skip": ["node_modules", ".git", "dist", "build", ".next", "vendor"]},
    "env": {"file": ".env.local"},
    "docker": {"compose": True},
}


def _config_path(root: str | None = None) -> Path:
    base = Path(root or git_root() or Path.cwd())
    return base / CONFIG_NAME


def _parse_toml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    section = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"\[(\w+)\]", line)
        if m:
            section = m.group(1)
            data.setdefault(section, {})
            continue
        if "=" in line and section:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if v.startswith("[") and v.endswith("]"):
                items = [i.strip().strip('"').strip("'") for i in v[1:-1].split(",") if i.strip()]
                data[section][k] = items
            elif v.lower() in ("true", "false"):
                data[section][k] = v.lower() == "true"
            else:
                data[section][k] = v
    return data


def _dump_toml(data: dict[str, Any]) -> str:
    lines = ["# agent-kit — config do projeto (IA pode editar via agent config)\n"]
    for section, values in data.items():
        if not isinstance(values, dict) or not values:
            continue
        lines.append(f"[{section}]")
        for k, v in values.items():
            if isinstance(v, bool):
                lines.append(f'{k} = {"true" if v else "false"}')
            elif isinstance(v, list):
                inner = ", ".join(f'"{x}"' for x in v)
                lines.append(f"{k} = [{inner}]")
            else:
                lines.append(f'{k} = "{v}"')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load(root: str | None = None) -> dict[str, Any]:
    path = _config_path(root)
    merged: dict[str, Any] = {
        "commands": dict(DEFAULTS["commands"]),
        "paths": {"skip": list(DEFAULTS["paths"]["skip"])},
        "env": dict(DEFAULTS["env"]),
        "docker": dict(DEFAULTS["docker"]),
    }
    if not path.is_file():
        return merged
    try:
        parsed = _parse_toml(path.read_text(encoding="utf-8"))
    except OSError:
        return merged
    for section in ("commands", "paths", "env", "docker", "meta"):
        if section in parsed and isinstance(parsed[section], dict):
            merged.setdefault(section, {}).update(parsed[section])
    return merged


def save(data: dict[str, Any], root: str | None = None) -> Path:
    path = _config_path(root)
    data.setdefault("meta", {})["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(_dump_toml(data), encoding="utf-8")
    return path


def get_command(kind: str, root: str | None = None) -> list[str] | None:
    cfg = load(root)
    cmd = cfg.get("commands", {}).get(kind)
    if not cmd:
        return None
    return cmd.split() if isinstance(cmd, str) else list(cmd)


def skip_paths(root: str | None = None) -> list[str]:
    return list(load(root).get("paths", {}).get("skip", DEFAULTS["paths"]["skip"]))


def env_file(root: str | None = None) -> str:
    return str(load(root).get("env", {}).get("file", ".env.local"))
