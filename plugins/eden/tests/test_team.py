"""Team brain end to end: two devs (two HOMEs), one shared bare repo, one client project."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
TEAM = PLUGIN / "scripts" / "eden_team.py"
BRAIN = PLUGIN / "hooks" / "eden_brain.py"
RECALL = PLUGIN / "hooks" / "eden_recall.py"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


tmp = Path(tempfile.mkdtemp())
GIT_ID = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
          "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com"}


def env_for(home):
    e = dict(os.environ, HOME=str(home), USERPROFILE=str(home), EDEN_TEAM_ALLOW_LOCAL="1", **GIT_ID)
    e.pop("EDEN_DISTILLER", None)
    return e


def run(script, args, home, stdin=None, cwd=None):
    r = subprocess.run([sys.executable, "-I", str(script), *args], capture_output=True, text=True,
                       env=env_for(home), input=stdin, cwd=cwd, encoding="utf-8")
    try:
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"raw": r.stdout, "err": r.stderr}
    except ValueError:
        return {"raw": r.stdout, "err": r.stderr}


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=dict(os.environ, **GIT_ID))


# shared remote and a client project whose origin is github.com/acme/store
remote = tmp / "team-remote.git"
git("init", "--bare", "-q", "-b", "main", str(remote))
project = tmp / "work" / "store"
project.mkdir(parents=True)
git("init", "-q", cwd=project)
git("remote", "add", "origin", "https://github.com/acme/store.git", cwd=project)
alice, bob = tmp / "alice", tmp / "bob"
for h in (alice, bob):
    (h / ".claude" / "eden-brain" / "semantic").mkdir(parents=True)

# --- URL safety
r = run(TEAM, ["join", "https://user:pw@github.com/acme/brain.git"], alice)
check("refuses a URL with credentials", r.get("ok") is False and "credentials" in r.get("error", ""))
r = run(TEAM, ["join", "not a url"], alice)
check("refuses a non-git URL", r.get("ok") is False)

# --- alice starts the team brain and links the project
r = run(TEAM, ["init", str(remote), "--name", "acme-team"], alice)
check("init clones, scaffolds and pushes", r.get("ok") and r["scaffold"].get("pushed") is True)
cfg = json.loads((alice / ".claude" / "eden-config.json").read_text(encoding="utf-8"))
check("team registered in eden-config", cfg["teams"]["acme-team"]["url"] == str(remote))
r = run(TEAM, ["link", "--cwd", str(project)], alice)
check("link creates projects/{remote slug}", r.get("ok") and r["project"] == "acme-store" and r.get("pushed") is True)
check("nothing written in the client repo", not (project / ".claude").exists()
      and git("status", "--porcelain", cwd=project).stdout == "")

# alice's team note (phase 2 will write these automatically)
aclone = alice / ".claude" / "eden-teams" / "acme-team"
note = aclone / "projects" / "acme-store" / "semantic" / "checkout-webhook-retries.md"
note.write_text("---\ntitle: The checkout webhook retries three times before failing\ntopic: checkout-webhook\n"
                "type: semantic\nauthor: alice\n---\n\nThe checkout webhook retries three times with backoff.\n",
                encoding="utf-8")
git("add", "-A", cwd=aclone)
git("commit", "-q", "-m", "note", cwd=aclone)
git("push", "-q", cwd=aclone)

# --- bob joins and sees it
r = run(TEAM, ["join", str(remote), "--name", "acme-team"], bob)
check("join clones the team brain and lists projects", r.get("ok") and r["projects"] == ["acme-store"])
start = subprocess.run([sys.executable, "-I", str(BRAIN), "start"], capture_output=True, text=True, encoding="utf-8",
                       env=env_for(bob), input=json.dumps({"cwd": str(project), "hook_event_name": "SessionStart"}))
ctx = start.stdout
check("session start lists the team's notes", "Equipo `acme-team`" in ctx and "checkout webhook retries" in ctx)
r = run(RECALL, ["search", "por que el checkout webhook retries falla", "--cwd", str(project)], bob)
check("recall finds the team note", any("checkout-webhook-retries" in h["path"] for h in r.get("hits", [])))
other = tmp / "work" / "other"
other.mkdir()
git("init", "-q", cwd=other)
git("remote", "add", "origin", "https://github.com/someone/other.git", cwd=other)
r = run(RECALL, ["search", "checkout webhook retries", "--cwd", str(other)], bob)
check("an unlinked project does not see the team's notes", r.get("hits") == [])

# --- status, pull, doctor
r = run(TEAM, ["status", "--cwd", str(project)], bob)
check("status says this project is linked", r["teams"][0]["this_project_linked"] and r["teams"][0]["notes"] >= 2)
note.write_text(note.read_text(encoding="utf-8") + "\n- Verified in: [[acme-store]]\n", encoding="utf-8")
git("commit", "-qam", "update", cwd=aclone)
git("push", "-q", cwd=aclone)
r = run(TEAM, ["pull"], bob)
bnote = bob / ".claude" / "eden-teams" / "acme-team" / "projects" / "acme-store" / "semantic" / "checkout-webhook-retries.md"
check("pull brings the teammate's change", r.get("ok") and "Verified in" in bnote.read_text(encoding="utf-8"))
r = run(TEAM, ["doctor"], bob)
check("doctor passes on a healthy clone", r.get("ok") is True)
r = run(TEAM, ["leave", "acme-team"], bob)
check("leave unregisters and keeps the clone", r.get("ok") and bnote.exists()
      and "acme-team" not in json.loads((bob / ".claude" / "eden-config.json").read_text(encoding="utf-8")).get("teams", {}))

# --- project brains never live in the client repo any more
(project / ".claude" / "brain").mkdir(parents=True)
start = subprocess.run([sys.executable, "-I", str(BRAIN), "start"], capture_output=True, text=True, encoding="utf-8",
                       env=env_for(alice), input=json.dumps({"cwd": str(project), "hook_event_name": "SessionStart"}))
check("a legacy in-repo vault is reported, not used", "cerebro antiguo" in start.stdout and "migrate-vault" in start.stdout)
legacy = project / ".claude" / "brain"
(legacy / "memory" / "semantic").mkdir(parents=True)
(legacy / "memory" / "semantic" / "old-gotcha.md").write_text("---\ntitle: old gotcha\n---\nx\n", encoding="utf-8")
(legacy / "code").mkdir()
(legacy / "code" / "node.md").write_text("generated", encoding="utf-8")
mv = subprocess.run([sys.executable, "-I", str(BRAIN), "migrate-vault", str(project)], capture_output=True, text=True,
                    encoding="utf-8", env=env_for(alice))
res = json.loads(mv.stdout)
target = alice / ".claude" / "eden-brain" / "projects" / "acme-store" / "semantic" / "old-gotcha.md"
check("migrate-vault copies notes out of the repo", target.exists() and legacy.joinpath("memory/semantic/old-gotcha.md").exists())
check("migrate-vault skips the generated graph", not any("node.md" in c for c in res["copied"]))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
