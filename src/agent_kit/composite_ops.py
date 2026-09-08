"""Composites — land, fix-ci, bootstrap."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_kit.config import CONFIG_NAME, load
from agent_kit.exec_util import git_root
from agent_kit.output import emit, fail


def land(
    cwd,
    *,
    message: str,
    open_pr: bool,
    with_tests: bool,
    all_files: bool,
    base: str | None,
    verbose: bool,
    human: bool,
) -> int:
    from agent_kit import ci_ops, git_ops, test_ops

    root = git_root(cwd)
    if not root:
        return fail("land", "NOT_A_REPO", "Fora de um repositório git")

    steps: list[dict[str, Any]] = []

    if with_tests:
        code = test_ops.run_tests(root, filter_arg=None, verbose=verbose, human=False)
        steps.append({"step": "test", "ok": code == 0})
        if code != 0:
            return fail("land", "TESTS_FAILED", "Testes falharam", data={"steps": steps}, next_steps=["agent fix-ci"])

    code = git_ops.ship(
        root, message=message, dry_run=False, no_push=False, open_pr=open_pr,
        with_tests=False, all_files=all_files, base=base, verbose=verbose, human=False,
    )
    steps.append({"step": "ship", "ok": code == 0})
    if code != 0:
        return fail("land", "SHIP_FAILED", "git ship falhou", data={"steps": steps})

    ci_code = ci_ops.status(root, verbose=verbose, human=False)
    steps.append({"step": "ci_status", "ok": ci_code == 0})

    return emit(
        ok=ci_code == 0,
        command="land",
        summary=f"land ok — {message!r}" + (" (CI falhou)" if ci_code != 0 else ""),
        data={"steps": steps, "message": message},
        next_steps=["agent fix-ci"] if ci_code != 0 else None,
        verbose=verbose,
        human=human,
    )


def fix_ci(cwd, *, verbose: bool, human: bool) -> int:
    import json
    from agent_kit import ci_ops
    from agent_kit.ci_ops import _gh_root
    from agent_kit.exec_util import run, tail

    root = git_root(cwd)
    if not root:
        return fail("fix-ci", "NOT_A_REPO", "Fora de um repositório git")

    if ci_ops.status(root, verbose=False, human=False) == 0:
        return emit(ok=True, command="fix-ci", summary="CI ok", verbose=verbose, human=human)

    root2 = _gh_root(root, "fix-ci")
    if not isinstance(root2, str):
        return root2
    lst = run(["gh", "run", "list", "--limit", "1", "--json", "databaseId,conclusion,name,url"], cwd=root2)
    run_id = None
    ci_info = None
    if lst.ok:
        try:
            runs = json.loads(lst.stdout)
            if runs:
                ci_info = runs[0]
                run_id = runs[0]["databaseId"]
        except json.JSONDecodeError:
            pass
    log_text = ""
    if run_id:
        lr = run(["gh", "run", "view", str(run_id), "--log-failed"], cwd=root2, timeout=60)
        log_text = tail(lr.stdout + lr.stderr, max_lines=50, max_chars=8000)

    return emit(
        ok=False,
        command="fix-ci",
        summary=f"CI falhou — {ci_info.get('name') if ci_info else 'run'}",
        data={"ci": ci_info, "logs": log_text},
        next_steps=['corrigir e agent land -m "fix(ci): descrição"'],
        verbose=verbose,
        human=human,
    )


def bootstrap(cwd, *, docker: bool, learn_config: bool, verbose: bool, human: bool) -> int:
    from agent_kit import build_ops, config_ops, docker_ops, prep_ops

    root = git_root(cwd) or cwd or "."
    steps: list[dict[str, Any]] = []

    if learn_config or not Path(root, CONFIG_NAME).is_file():
        c = config_ops.learn(verbose=False, human=False)
        steps.append({"step": "config_learn", "ok": c == 0})

    c = build_ops.install(root, verbose=False, human=False)
    steps.append({"step": "deps_install", "ok": c == 0})

    if docker and load(root).get("docker", {}).get("compose", True):
        c = docker_ops.compose_up(detach=True, build=False, services=[], verbose=False, human=False)
        steps.append({"step": "compose_up", "ok": c == 0})

    c = prep_ops.task(root, with_pr=False, verbose=verbose, human=human)
    steps.append({"step": "prep_task", "ok": c == 0})

    failed = [s for s in steps if not s["ok"]]
    return emit(
        ok=not failed,
        command="bootstrap",
        summary=f"bootstrap — {len(steps) - len(failed)}/{len(steps)} ok",
        data={"steps": steps},
        next_steps=["agent doctor"] if failed else None,
        verbose=verbose,
        human=human,
    )
