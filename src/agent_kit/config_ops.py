"""agent config — ler/escrever .agent-kit.toml."""

from __future__ import annotations

from typing import Any

from agent_kit.config import CONFIG_NAME, DEFAULTS, _config_path, load, save
from agent_kit.detect import detect_all
from agent_kit.exec_util import git_root
from agent_kit.output import emit, fail


def show(*, verbose: bool, human: bool) -> int:
    root = git_root()
    cfg = load(root)
    path = str(_config_path(root)) if root else CONFIG_NAME
    return emit(
        ok=True,
        command="config.show",
        summary=f"config em {path}",
        data={"path": path, "config": cfg},
        next_steps=["agent config learn", "agent config set commands.test \"bun test\""],
        verbose=verbose,
        human=human,
    )


def learn(*, verbose: bool, human: bool) -> int:
    root = git_root()
    if not root:
        return fail("config.learn", "NOT_A_REPO", "Fora de um repositório git")
    cfg = load(root)
    det = detect_all(root)
    learned: list[str] = []
    for t in det.get("tools", []):
        kind = t.get("kind")
        cmd = t.get("cmd")
        if kind and cmd:
            cfg.setdefault("commands", {})[kind] = " ".join(cmd)
            learned.append(kind)
    if inst := det.get("install"):
        cfg.setdefault("commands", {})["install"] = " ".join(inst["cmd"])
        learned.append("install")
    if det.get("node"):
        cfg.setdefault("meta", {})["node_pm"] = det["node"].get("pm")
    path = save(cfg, root)
    return emit(
        ok=True,
        command="config.learn",
        summary=f"aprendeu {len(learned)} comando(s) → {path.name}",
        data={"path": str(path), "learned": learned, "config": cfg},
        next_steps=["agent config show"],
        verbose=verbose,
        human=human,
    )


def set_key(section: str, key: str, value: str, *, verbose: bool, human: bool) -> int:
    root = git_root()
    if not root:
        return fail("config.set", "NOT_A_REPO", "Fora de um repositório git")
    cfg = load(root)
    if section not in ("commands", "paths", "env", "docker", "meta"):
        return fail("config.set", "BAD_SECTION", f"Seção inválida: {section}")
    if section == "paths" and key == "skip":
        cfg.setdefault("paths", {})["skip"] = [v.strip() for v in value.split(",")]
    elif value.lower() in ("true", "false"):
        cfg.setdefault(section, {})[key] = value.lower() == "true"
    else:
        cfg.setdefault(section, {})[key] = value
    path = save(cfg, root)
    return emit(
        ok=True,
        command="config.set",
        summary=f"{section}.{key} salvo",
        data={"path": str(path), "config": cfg},
        verbose=verbose,
        human=human,
    )
