"""CLI principal do agent-kit."""

from __future__ import annotations

import argparse
import sys

from agent_kit import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent", description="Macros CLI para agentes (JSON compacto).")
    p.add_argument("--version", action="version", version=f"agent-kit {__version__}")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--human", action="store_true", help="não use como agente")

    sub = p.add_subparsers(dest="domain", required=True)

    # prep
    prep = sub.add_parser("prep", help="contexto inicial em 1 turno")
    prep_sub = prep.add_subparsers(dest="action", required=True)
    t = prep_sub.add_parser("task", help="git + detect + pr opcional")
    t.add_argument("--pr", action="store_true")
    prep_sub.add_parser("pr", help="PR + CI em 1 turno")

    sub.add_parser("doctor", help="diagnóstico do ambiente")
    git = sub.add_parser("git")
    g = git.add_subparsers(dest="action", required=True)
    s = g.add_parser("snapshot"); s.add_argument("--diff", action="store_true")
    sh = g.add_parser("ship")
    sh.add_argument("-m", "--message", required=True, help="mensagem de commit (obrigatória)")
    sh.add_argument("--dry-run", action="store_true")
    sh.add_argument("--no-push", action="store_true"); sh.add_argument("--pr", action="store_true")
    sh.add_argument("--with-tests", action="store_true"); sh.add_argument("--all", action="store_true"); sh.add_argument("--base")
    cm = g.add_parser("commit")
    cm.add_argument("-m", "--message", required=True); cm.add_argument("--all", action="store_true")
    g.add_parser("suggest")
    sy = g.add_parser("sync"); sy.add_argument("--rebase", action="store_true"); sy.add_argument("--dry-run", action="store_true")
    d = g.add_parser("diff"); d.add_argument("--base", default="HEAD"); d.add_argument("--stat", action="store_true"); d.add_argument("--max-lines", type=int, default=60)
    lg = g.add_parser("log"); lg.add_argument("-n", type=int, default=10)
    br = g.add_parser("branch"); br.add_argument("--create"); br.add_argument("--switch")
    st = g.add_parser("stash"); st.add_argument("stash_action", choices=["push", "pop", "list"], nargs="?", default="list"); st.add_argument("-m", "--message")
    ad = g.add_parser("add"); ad.add_argument("paths", nargs="*"); ad.add_argument("--all", action="store_true")
    dc = g.add_parser("discard"); dc.add_argument("paths", nargs="*"); dc.add_argument("--all", action="store_true")
    g.add_parser("conflicts")

    pr = sub.add_parser("pr")
    prs = pr.add_subparsers(dest="action", required=True)
    pl = prs.add_parser("list")
    pl.add_argument("--mine", action="store_true")
    pl.add_argument("--limit", type=int, default=10)
    o = prs.add_parser("open"); o.add_argument("-t", "--title", required=True); o.add_argument("-b", "--body"); o.add_argument("--base"); o.add_argument("--draft", action="store_true")
    rv = prs.add_parser("review")
    rv.add_argument("-n", "--number", type=int)
    ck = prs.add_parser("checks")
    ck.add_argument("-n", "--number", type=int)
    mg = prs.add_parser("merge"); mg.add_argument("-n", "--number", type=int); mg.add_argument("--method", choices=["merge", "squash", "rebase"], default="squash")
    cm = prs.add_parser("comment"); cm.add_argument("-n", "--number", type=int); cm.add_argument("-b", "--body", required=True)
    cl = prs.add_parser("close")
    cl.add_argument("-n", "--number", type=int)
    pd = prs.add_parser("diff")
    pd.add_argument("-n", "--number", type=int)
    pd.add_argument("--max-files", type=int, default=50)

    ci = sub.add_parser("ci")
    ci_sub = ci.add_subparsers(dest="action", required=True)
    ci_sub.add_parser("status")
    cil = ci_sub.add_parser("logs")
    cil.add_argument("-n", "--run-id", type=int, dest="run_id")

    cfg = sub.add_parser("config")
    cfg_sub = cfg.add_subparsers(dest="action", required=True)
    cfg_sub.add_parser("show")
    cfg_sub.add_parser("learn")
    cfs = cfg_sub.add_parser("set")
    cfs.add_argument("key", help="ex: commands.test")
    cfs.add_argument("value")

    land_p = sub.add_parser("land", help="test + ship + ci status")
    land_p.add_argument("-m", "--message", required=True)
    land_p.add_argument("--pr", action="store_true")
    land_p.add_argument("--no-test", action="store_true")
    land_p.add_argument("--all", action="store_true")
    land_p.add_argument("--base")

    sub.add_parser("fix-ci", help="ci status + logs de falha")

    boot = sub.add_parser("bootstrap", help="config learn + deps + compose + prep")
    boot.add_argument("--no-docker", action="store_true")
    boot.add_argument("--no-learn", action="store_true")

    # test / build / deps
    test = sub.add_parser("test"); ts = test.add_subparsers(dest="action", required=True)
    ts.add_parser("detect"); tr = ts.add_parser("run"); tr.add_argument("-k", "--filter")
    build = sub.add_parser("build"); bs = build.add_subparsers(dest="action", required=True)
    brn = bs.add_parser("run"); brn.add_argument("--target", default="lint", choices=["test", "lint", "typecheck", "build"])
    deps = sub.add_parser("deps"); ds = deps.add_subparsers(dest="action", required=True)
    ds.add_parser("install")

    # fs
    fs = sub.add_parser("fs"); fs_sub = fs.add_subparsers(dest="action", required=True)
    fs_sub.add_parser("pwd")
    fc = fs_sub.add_parser("cd"); fc.add_argument("path")
    fl = fs_sub.add_parser("ls"); fl.add_argument("path", nargs="?"); fl.add_argument("--depth", type=int, default=1); fl.add_argument("--limit", type=int, default=120)
    fg = fs_sub.add_parser("grep"); fg.add_argument("pattern"); fg.add_argument("path", nargs="?", default=".")
    fg.add_argument("--max", type=int, default=50); fg.add_argument("-i", action="store_true"); fg.add_argument("--glob"); fg.add_argument("--type")
    ff = fs_sub.add_parser("find"); ff.add_argument("query"); ff.add_argument("path", nargs="?", default=".")
    ff.add_argument("--max", type=int, default=50); ff.add_argument("--type")
    fr = fs_sub.add_parser("read"); fr.add_argument("path"); fr.add_argument("--offset", type=int, default=1); fr.add_argument("--limit", type=int, default=200)

    # repo
    repo = sub.add_parser("repo"); rs = repo.add_subparsers(dest="action", required=True)
    rs.add_parser("info"); rs.add_parser("find").add_argument("name")
    cl = rs.add_parser("clone"); cl.add_argument("url"); cl.add_argument("--dest"); cl.add_argument("--depth", type=int)

    # env
    env = sub.add_parser("env"); env_sub = env.add_subparsers(dest="action", required=True)
    env_sub.add_parser("list")
    env_sub.add_parser("check")
    es = env_sub.add_parser("set"); es.add_argument("pairs", nargs="+"); es.add_argument("--file")
    ei = env_sub.add_parser("ingest"); ei.add_argument("blob")

    # docker
    dk = sub.add_parser("docker"); dk_sub = dk.add_subparsers(dest="action", required=True)
    dps = dk_sub.add_parser("ps"); dps.add_argument("-a", "--all", action="store_true")
    dk_sub.add_parser("kill").add_argument("container")
    dk_sub.add_parser("stop").add_argument("container")
    dr = dk_sub.add_parser("run"); dr.add_argument("image_args", nargs=argparse.REMAINDER); dr.add_argument("-d", "--detach", action="store_true")
    dc = dk_sub.add_parser("compose"); dc_sub = dc.add_subparsers(dest="compose_action", required=True)
    dc_sub.add_parser("ps")
    du = dc_sub.add_parser("up"); du.add_argument("-d", "--detach", action="store_true"); du.add_argument("--build", action="store_true"); du.add_argument("services", nargs="*")
    dcd = dc_sub.add_parser("down"); dcd.add_argument("-v", "--volumes", action="store_true")
    dl = dc_sub.add_parser("logs"); dl.add_argument("service", nargs="?"); dl.add_argument("--tail", type=int, default=50)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    v, h = args.verbose, args.human

    if args.domain == "doctor":
        from agent_kit import doctor_ops
        return doctor_ops.doctor(verbose=v, human=h)

    if args.domain == "prep":
        from agent_kit import prep_ops
        if args.action == "pr":
            return prep_ops.pr_prep(None, verbose=v, human=h)
        return prep_ops.task(None, with_pr=args.pr, verbose=v, human=h)

    if args.domain == "git":
        from agent_kit import git_ops
        a = args.action
        if a == "snapshot": return git_ops.snapshot(None, verbose=v, human=h, include_diff=args.diff)
        if a == "ship": return git_ops.ship(None, message=args.message, dry_run=args.dry_run, no_push=args.no_push,
            open_pr=args.pr, with_tests=args.with_tests, all_files=args.all, base=args.base, verbose=v, human=h)
        if a == "commit": return git_ops.commit(None, message=args.message, all_files=args.all, verbose=v, human=h)
        if a == "suggest": return git_ops.suggest_msg(None, verbose=v, human=h)
        if a == "sync": return git_ops.sync(None, rebase=args.rebase, dry_run=args.dry_run, verbose=v, human=h)
        if a == "diff": return git_ops.diff(None, base=args.base, stat_only=args.stat, max_lines=args.max_lines, verbose=v, human=h)
        if a == "log": return git_ops.log(None, count=args.n, verbose=v, human=h)
        if a == "branch": return git_ops.branch(None, create=args.create, switch=args.switch, verbose=v, human=h)
        if a == "stash": return git_ops.stash(None, action=args.stash_action, message=args.message, verbose=v, human=h)
        if a == "add": return git_ops.stage(None, paths=args.paths, all_files=args.all, verbose=v, human=h)
        if a == "discard": return git_ops.discard(None, all_files=args.all, paths=args.paths, verbose=v, human=h)
        if a == "conflicts": return git_ops.conflicts(None, verbose=v, human=h)

    if args.domain == "pr":
        from agent_kit import pr_ops
        a = args.action
        if a == "list": return pr_ops.list_prs(None, mine=args.mine, limit=args.limit, verbose=v, human=h)
        if a == "open": return pr_ops.open_pr(None, title=args.title, body=args.body, base=args.base, draft=args.draft, verbose=v, human=h)
        if a == "review": return pr_ops.review(None, number=args.number, verbose=v, human=h)
        if a == "checks": return pr_ops.checks(None, number=args.number, verbose=v, human=h)
        if a == "merge": return pr_ops.merge(None, number=args.number, method=args.method, verbose=v, human=h)
        if a == "comment": return pr_ops.comment(None, number=args.number, body=args.body, verbose=v, human=h)
        if a == "close": return pr_ops.close(None, number=args.number, verbose=v, human=h)
        if a == "diff": return pr_ops.pr_diff(None, number=args.number, max_files=args.max_files, verbose=v, human=h)

    if args.domain == "test":
        from agent_kit import test_ops
        if args.action == "detect": return test_ops.detect(None, verbose=v, human=h)
        return test_ops.run_tests(None, filter_arg=args.filter, verbose=v, human=h)

    if args.domain == "build":
        from agent_kit import build_ops
        return build_ops.run_target(None, target=args.target, verbose=v, human=h)

    if args.domain == "deps":
        from agent_kit import build_ops
        return build_ops.install(None, verbose=v, human=h)

    if args.domain == "fs":
        from agent_kit import fs_ops
        if args.action == "pwd": return fs_ops.pwd(verbose=v, human=h)
        if args.action == "cd": return fs_ops.cd(args.path, verbose=v, human=h)
        if args.action == "ls": return fs_ops.ls(args.path, depth=args.depth, limit=args.limit, verbose=v, human=h)
        if args.action == "grep": return fs_ops.grep(args.pattern, args.path, max_hits=args.max, ignore_case=args.i, glob=args.glob, file_type=args.type, verbose=v, human=h)
        if args.action == "find": return fs_ops.find(args.query, args.path, max_results=args.max, file_type=args.type, verbose=v, human=h)
        return fs_ops.read(args.path, offset=args.offset, limit=args.limit, verbose=v, human=h)

    if args.domain == "repo":
        from agent_kit import repo_ops
        if args.action == "info": return repo_ops.info(None, verbose=v, human=h)
        if args.action == "find": return repo_ops.find(args.name, verbose=v, human=h)
        return repo_ops.clone(args.url, dest=args.dest, depth=args.depth, verbose=v, human=h)

    if args.domain == "ci":
        from agent_kit import ci_ops
        if args.action == "status":
            return ci_ops.status(None, verbose=v, human=h)
        return ci_ops.logs(None, run_id=args.run_id, verbose=v, human=h)

    if args.domain == "config":
        from agent_kit import config_ops
        if args.action == "show":
            return config_ops.show(verbose=v, human=h)
        if args.action == "learn":
            return config_ops.learn(verbose=v, human=h)
        sec, _, key = args.key.partition(".")
        if not key:
            return config_ops.set_key("commands", args.key, args.value, verbose=v, human=h)
        return config_ops.set_key(sec, key, args.value, verbose=v, human=h)

    if args.domain == "land":
        from agent_kit import composite_ops
        return composite_ops.land(
            None, message=args.message, open_pr=args.pr, with_tests=not args.no_test,
            all_files=args.all, base=args.base, verbose=v, human=h,
        )

    if args.domain == "fix-ci":
        from agent_kit import composite_ops
        return composite_ops.fix_ci(None, verbose=v, human=h)

    if args.domain == "bootstrap":
        from agent_kit import composite_ops
        return composite_ops.bootstrap(
            None, docker=not args.no_docker, learn_config=not args.no_learn, verbose=v, human=h,
        )

    if args.domain == "env":
        from agent_kit import env_ops
        if args.action == "list": return env_ops.list_env(None, verbose=v, human=h)
        if args.action == "check": return env_ops.check(None, verbose=v, human=h)
        if args.action == "set": return env_ops.set_var(None, args.pairs, file=args.file, verbose=v, human=h)
        return env_ops.ingest(None, args.blob, verbose=v, human=h)

    if args.domain == "docker":
        from agent_kit import docker_ops
        a = args.action
        if a == "ps": return docker_ops.ps(all_containers=args.all, verbose=v, human=h)
        if a == "kill": return docker_ops.kill(args.container, verbose=v, human=h)
        if a == "stop": return docker_ops.stop(args.container, verbose=v, human=h)
        if a == "run": return docker_ops.run_cmd(args.image_args, detach=args.detach, verbose=v, human=h)
        ca = args.compose_action
        if ca == "ps": return docker_ops.compose_ps(verbose=v, human=h)
        if ca == "up": return docker_ops.compose_up(detach=args.detach, build=args.build, services=args.services or [], verbose=v, human=h)
        if ca == "down": return docker_ops.compose_down(volumes=args.volumes, verbose=v, human=h)
        return docker_ops.compose_logs(service=args.service, tail_lines=args.tail, verbose=v, human=h)

    return 1


if __name__ == "__main__":
    sys.exit(main())
