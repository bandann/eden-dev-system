#!/usr/bin/env python3
"""Eden team brain: a separate git repo the team shares, next to each dev's personal brain.

    ~/.claude/eden-teams/{team}/          a clone of the team's private repo
        README.md
        projects/{project-slug}/          what the team knows about one project
            000-INDEX.md  decisions/  semantic/  procedural/  episodic/

A project is in a team when the clone has `projects/{slug}/`; the slug is the same one the personal
brain uses (the git remote, e.g. `acme-store`), so everybody working on that repo lands in the same
folder. Nothing is written into the client's repo.

Commands (print JSON):
    join <git-url> [--name N]       clone the team repo and register it in ~/.claude/eden-config.json
    init <git-url> [--name N]       same, for an EMPTY repo: scaffold README + projects/ and push it
    link [--team N] [--cwd DIR]     add this project to the team (projects/{slug}/ + index), commit, push
    status                          teams, their clones, last pull and which projects they hold
    pull [--quiet]                  `git pull --ff-only` every team clone (the session start runs this)
    doctor                          check each clone: remote reachable, clean tree, branch tracking
    leave <team>                    unregister the team (the clone stays on disk; delete it by hand)

Git runs with GIT_TERMINAL_PROMPT=0: it never asks for a password. Access is whatever the dev's own git
credentials allow. A URL that carries credentials is refused. Stdlib only.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hooks"))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("eden_brain", HERE.parent / "hooks" / "eden_brain.py")
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)

CONFIG = b.CLAUDE_DIR / "eden-config.json"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
README = """# {team} — Eden team brain

Shared knowledge for the projects this team works on, written by Eden's brain distiller and by hand.
One folder per project under `projects/`, named like the project's git remote (`owner-repo`).

- Notes are markdown with frontmatter (`title`, `topic`, `type`, `date`, `confidence`, `author`).
- Never secrets, credentials or customers' personal data. Eden redacts and quarantines them, but
  review what you add by hand.
- Each dev's working style and personal notes stay in their own brain (`~/.claude/eden-brain`).
"""
INDEX = "# {project}\n\nWhat the team knows about this project. One line per note.\n"


def out(data, code=0):
    print(json.dumps(data, indent=1, ensure_ascii=False))
    sys.exit(code)


def git(args, cwd=None, timeout=60):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="echo", GCM_INTERACTIVE="never")
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env,
                           creationflags=NO_WINDOW)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", repr(exc)


def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(CONFIG)


def check_url(url):
    """https://host/owner/repo(.git) or git@host:owner/repo(.git). No credentials inside the URL.
    EDEN_TEAM_ALLOW_LOCAL=1 also accepts a local path (tests, or a repo on a shared drive)."""
    if os.environ.get("EDEN_TEAM_ALLOW_LOCAL") == "1" and (Path(url).is_absolute() or url.startswith("file://")):
        return None
    if re.match(r"^https?://[^/@\s]+:[^/@\s]*@", url) or re.match(r"^https?://[^/\s]+@", url):
        return "the URL carries credentials; use your git credential helper or SSH instead"
    if not (re.match(r"^https://[\w.-]+/[\w.-]+/[\w.-]+?(\.git)?/?$", url)
            or re.match(r"^(ssh://)?git@[\w.-]+[:/][\w.-]+/[\w.-]+?(\.git)?$", url)):
        return "not a git URL (https://host/owner/repo or git@host:owner/repo)"
    return None


def team_name(url, name=None):
    raw = name or re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1].split(":")[-1])
    slug = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    return slug or None


def opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def register(name, url, path):
    cfg = load_config()
    teams = cfg.setdefault("teams", {})
    teams[name] = {"url": url, "path": path.as_posix(), "push": teams.get(name, {}).get("push", "auto"),
                   "share_general": teams.get(name, {}).get("share_general", False)}
    save_config(cfg)


def clone(url, name):
    err = check_url(url)
    if err:
        out({"ok": False, "error": err}, 1)
    if not name:
        out({"ok": False, "error": "could not derive a team name; pass --name"}, 1)
    path = b.TEAMS / name
    if path.exists() and any(path.iterdir()):
        code, origin, _ = git(["remote", "get-url", "origin"], cwd=path)
        if code or origin.rstrip("/") != url.rstrip("/"):
            out({"ok": False, "error": f"{path.as_posix()} already exists with another remote ({origin or 'none'})"}, 1)
        return path, False
    b.TEAMS.mkdir(parents=True, exist_ok=True)
    code, _, err = git(["clone", "--quiet", url, str(path)], timeout=180)
    if code:
        out({"ok": False, "error": "git clone failed: " + err[-400:],
             "hint": "check you were given access and that your git can read private repos (gh auth login, gh auth setup-git)"}, 1)
    return path, True


def commit_and_push(path, message, push=True):
    git(["add", "-A"], cwd=path)
    code, status, _ = git(["status", "--porcelain"], cwd=path)
    if not status:
        return {"committed": False, "pushed": False}
    code, _, err = git(["commit", "--quiet", "-m", message], cwd=path)
    if code:
        return {"committed": False, "pushed": False, "error": err[-300:]}
    if not push:
        return {"committed": True, "pushed": False}
    code, _, err = git(["push", "--quiet", "-u", "origin", "HEAD"], cwd=path, timeout=120)
    if code:  # someone pushed first: replay ours on top and try once more
        git(["pull", "--rebase", "--quiet"], cwd=path, timeout=120)
        code, _, err = git(["push", "--quiet", "-u", "origin", "HEAD"], cwd=path, timeout=120)
    return {"committed": True, "pushed": code == 0, **({"error": err[-300:]} if code else {})}


# --- commands -----------------------------------------------------------------------------------

def cmd_join(argv, scaffold=False):
    if not argv or argv[0].startswith("--"):
        out({"ok": False, "error": "usage: join|init <git-url> [--name N]"}, 1)
    url = argv[0].strip()
    name = team_name(url, opt(argv, "--name"))
    path, fresh = clone(url, name)
    res = {"ok": True, "team": name, "path": path.as_posix(), "cloned": fresh}
    if scaffold:
        has_commits = git(["rev-parse", "--verify", "HEAD"], cwd=path)[0] == 0
        if has_commits and (path / "projects").is_dir():
            res["scaffold"] = "already a team brain"
        else:
            (path / "projects").mkdir(exist_ok=True)
            (path / "projects" / ".gitkeep").touch()
            if not (path / "README.md").exists():
                (path / "README.md").write_text(README.format(team=name), encoding="utf-8")
            res["scaffold"] = commit_and_push(path, "chore: start the team brain")
    elif not (path / "projects").is_dir():
        res["warning"] = "this repo has no projects/ folder yet: it is empty or not a team brain (use init for a new one)"
    register(name, url, path)
    res["projects"] = sorted(p.name for p in (path / "projects").iterdir() if p.is_dir()) if (path / "projects").is_dir() else []
    out(res)


def cmd_link(argv):
    teams = b.teams_config()
    name = opt(argv, "--team") or (next(iter(teams)) if len(teams) == 1 else None)
    if not name or name not in teams:
        out({"ok": False, "error": "say which team: --team " + "|".join(sorted(teams)) if teams
             else "no team yet: /eden:brain team join <url>"}, 1)
    root = b.project_root(opt(argv, "--cwd") or os.getcwd())
    if root.resolve() == Path.home().resolve() or not (root / ".git").exists():
        out({"ok": False, "error": f"{root.as_posix()} is not a git project"}, 1)
    slug = b.project_slug(root)
    tpath = b.team_path(name, teams[name])
    folder = tpath / "projects" / slug
    git(["pull", "--ff-only", "--quiet"], cwd=tpath, timeout=60)
    created = not folder.is_dir()
    for sub in ("decisions", "semantic", "procedural", "episodic"):
        (folder / sub).mkdir(parents=True, exist_ok=True)
        keep = folder / sub / ".gitkeep"
        if not any(folder.joinpath(sub).iterdir()):
            keep.touch()
    if not (folder / "000-INDEX.md").exists():
        (folder / "000-INDEX.md").write_text(INDEX.format(project=slug), encoding="utf-8")
    push = teams[name].get("push", "auto") != "manual"
    res = commit_and_push(tpath, f"chore: add project {slug} to the team brain", push=push)
    out({"ok": True, "team": name, "project": slug, "folder": folder.as_posix(), "created": created, **res})


def last_pull(path):
    f = path / ".git" / "FETCH_HEAD"
    return datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="minutes") if f.exists() else None


def cmd_status(argv):
    teams, rows = b.teams_config(), []
    root = b.project_root(opt(argv, "--cwd") or os.getcwd())
    here = b.project_slug(root) if (root / ".git").exists() else None
    for name, t in sorted(teams.items()):
        path = b.team_path(name, t)
        projects = sorted(p.name for p in (path / "projects").iterdir() if p.is_dir()) if (path / "projects").is_dir() else []
        notes = sum(1 for _ in (path / "projects").rglob("*.md")) if projects else 0
        rows.append({"team": name, "url": t.get("url"), "path": path.as_posix(), "cloned": (path / ".git").exists(),
                     "last_pull": last_pull(path) if path.exists() else None, "projects": projects, "notes": notes,
                     "this_project_linked": bool(here and here in projects), "push": t.get("push", "auto")})
    out({"ok": True, "project": here, "teams": rows})


def cmd_pull(argv):
    quiet, res = "--quiet" in argv, []
    for name, t in sorted(b.teams_config().items()):
        path = b.team_path(name, t)
        if t.get("enabled") is False or not (path / ".git").exists():
            continue
        code, _, err = git(["pull", "--ff-only", "--quiet"], cwd=path, timeout=60)
        res.append({"team": name, "ok": code == 0, **({"error": err[-300:]} if code else {})})
        if code:
            try:
                b.log(f"team {name}: pull failed: {err[-200:]}")
            except Exception:
                pass
    if not quiet:
        out({"ok": all(r["ok"] for r in res), "pulled": res})


def cmd_doctor(argv):
    checks = []
    code, ver, _ = git(["--version"])
    checks.append({"check": "git installed", "ok": code == 0, "detail": ver})
    for name, t in sorted(b.teams_config().items()):
        path = b.team_path(name, t)
        ok_clone = (path / ".git").exists()
        checks.append({"check": f"{name}: clone at {path.as_posix()}", "ok": ok_clone})
        if not ok_clone:
            continue
        code, _, err = git(["ls-remote", "--heads", "origin"], cwd=path, timeout=30)
        checks.append({"check": f"{name}: remote reachable with your credentials", "ok": code == 0,
                       **({"detail": err[-200:]} if code else {})})
        code, st, _ = git(["status", "--porcelain"], cwd=path)
        checks.append({"check": f"{name}: no uncommitted changes", "ok": not st, **({"detail": st[:300]} if st else {})})
        code, up, _ = git(["rev-parse", "--abbrev-ref", "@{u}"], cwd=path)
        checks.append({"check": f"{name}: branch tracks a remote branch", "ok": code == 0, "detail": up})
        checks.append({"check": f"{name}: has projects/", "ok": (path / "projects").is_dir()})
    out({"ok": all(c["ok"] for c in checks), "checks": checks})


def cmd_leave(argv):
    if not argv:
        out({"ok": False, "error": "usage: leave <team>"}, 1)
    cfg = load_config()
    t = (cfg.get("teams") or {}).pop(argv[0], None)
    if t is None:
        out({"ok": False, "error": f"no team {argv[0]}"}, 1)
    save_config(cfg)
    out({"ok": True, "left": argv[0], "clone_kept": t.get("path")})


def main(argv):
    cmd, rest = (argv[0] if argv else ""), argv[1:]
    handlers = {"join": cmd_join, "init": lambda a: cmd_join(a, scaffold=True), "link": cmd_link,
                "status": cmd_status, "pull": cmd_pull, "doctor": cmd_doctor, "leave": cmd_leave}
    if cmd not in handlers:
        print(__doc__)
        return
    handlers[cmd](rest)


if __name__ == "__main__":
    main(sys.argv[1:])
