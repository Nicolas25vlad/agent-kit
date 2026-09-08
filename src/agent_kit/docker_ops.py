"""Docker — wrappers simples (ps, run, compose). Sem Dockerfile."""

from __future__ import annotations

import json
import shutil
from typing import Any

from agent_kit.exec_util import run, tail
from agent_kit.output import emit, fail


def _has_docker() -> bool:
    return shutil.which("docker") is not None


def _compose_cmd(args: list[str], *, cwd: str | None = None, timeout: int = 120) -> Any:
    if run(["docker", "compose", "version"], timeout=5).ok:
        return run(["docker", "compose"] + args, cwd=cwd, timeout=timeout)
    if shutil.which("docker-compose"):
        return run(["docker-compose"] + args, cwd=cwd, timeout=timeout)
    return None


def _parse_json_lines(stdout: str) -> list[dict[str, Any]]:
    out = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def ps(*, all_containers: bool, verbose: bool, human: bool) -> int:
    if not _has_docker():
        return fail("docker.ps", "DOCKER_MISSING", "docker não encontrado no PATH")
    cmd = ["docker", "ps", "--format", "{{json .}}"]
    if all_containers:
        cmd.insert(2, "-a")
    r = run(cmd, timeout=15)
    containers = _parse_json_lines(r.stdout)
    return emit(
        ok=True,
        command="docker.ps",
        summary=f"{len(containers)} container(s)",
        data={"containers": containers},
        verbose=verbose,
        human=human,
    )


def kill(container: str, *, verbose: bool, human: bool) -> int:
    if not _has_docker():
        return fail("docker.kill", "DOCKER_MISSING", "docker não encontrado")
    r = run(["docker", "kill", container], timeout=30)
    return emit(ok=r.ok, command="docker.kill", summary=f"kill {container}" if r.ok else "kill falhou",
                data={"output": tail(r.stderr or r.stdout)}, verbose=verbose, human=human)


def stop(container: str, *, verbose: bool, human: bool) -> int:
    if not _has_docker():
        return fail("docker.stop", "DOCKER_MISSING", "docker não encontrado")
    r = run(["docker", "stop", container], timeout=60)
    return emit(ok=r.ok, command="docker.stop", summary=f"stop {container}" if r.ok else "stop falhou",
                data={"output": tail(r.stderr or r.stdout)}, verbose=verbose, human=human)


def run_cmd(image_args: list[str], *, detach: bool, verbose: bool, human: bool) -> int:
    if not _has_docker():
        return fail("docker.run", "DOCKER_MISSING", "docker não encontrado")
    if not image_args:
        return fail("docker.run", "NO_ARGS", "Uso: agent docker run [--detach] IMAGE [args...]")
    cmd = ["docker", "run"]
    if detach:
        cmd.append("-d")
    cmd.extend(image_args)
    r = run(cmd, timeout=300)
    return emit(
        ok=r.ok,
        command="docker.run",
        summary="container iniciado" if r.ok else "run falhou",
        data={"cmd": cmd, "container_id": r.stdout.strip() if r.ok else None, "output": tail(r.stdout + r.stderr)},
        verbose=verbose,
        human=human,
    )


def compose_up(*, detach: bool, build: bool, services: list[str], verbose: bool, human: bool) -> int:
    c = _compose_cmd(["up"] + (["-d"] if detach else []) + (["--build"] if build else []) + services)
    if c is None:
        return fail("docker.compose", "COMPOSE_MISSING", "docker compose não disponível")
    return emit(ok=c.ok, command="docker.compose.up",
                summary="compose up ok" if c.ok else "compose up falhou",
                data={"output": tail(c.stdout + c.stderr)}, verbose=verbose, human=human)


def compose_down(*, volumes: bool, verbose: bool, human: bool) -> int:
    cmd = ["down"] + (["-v"] if volumes else [])
    c = _compose_cmd(cmd)
    if c is None:
        return fail("docker.compose", "COMPOSE_MISSING", "docker compose não disponível")
    return emit(ok=c.ok, command="docker.compose.down", summary="compose down ok" if c.ok else "falhou",
                data={"output": tail(c.stdout + c.stderr)}, verbose=verbose, human=human)


def compose_ps(verbose: bool, human: bool) -> int:
    c = _compose_cmd(["ps", "--format", "json"])
    if c is None:
        return fail("docker.compose", "COMPOSE_MISSING", "docker compose não disponível")
    services = _parse_json_lines(c.stdout) if c.stdout.strip().startswith("{") else []
    if not services and c.stdout.strip():
        services = [{"raw": ln} for ln in c.stdout.splitlines() if ln.strip()]
    return emit(ok=c.ok, command="docker.compose.ps", summary=f"{len(services)} serviço(s)",
                data={"services": services}, verbose=verbose, human=human)


def compose_logs(*, service: str | None, tail_lines: int, verbose: bool, human: bool) -> int:
    cmd = ["logs", "--tail", str(tail_lines)]
    if service:
        cmd.append(service)
    c = _compose_cmd(cmd)
    if c is None:
        return fail("docker.compose", "COMPOSE_MISSING", "docker compose não disponível")
    return emit(
        ok=c.ok,
        command="docker.compose.logs",
        summary=f"logs ({tail_lines} linhas)" + (f" — {service}" if service else ""),
        data={"output": tail(c.stdout + c.stderr, max_lines=tail_lines, max_chars=8000)},
        verbose=verbose,
        human=human,
    )
