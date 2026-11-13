import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eden_review", PLUGIN / "hooks" / "eden_review.py")
rv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rv)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


repo = Path(tempfile.mkdtemp())
env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e.x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e.x")
for k in ("EDEN_REVIEW_OFF", "EDEN_GUARD_OFF", "EDEN_HOST"):
    env.pop(k, None)
os.environ.pop("EDEN_REVIEW_OFF", None)


def git(*a):
    return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)


def guard(payload=None, args=(), stdin=None):
    return subprocess.run([sys.executable, "-I", str(PLUGIN / "hooks" / "eden_guard.py"), *args], cwd=repo,
                          input=stdin if stdin is not None else json.dumps(payload), capture_output=True, text=True,
                          encoding="utf-8", env=env)


git("init", "-q", "-b", "feat")
(repo / "a.txt").write_text("one\n")
(repo / ".gitignore").write_text("ignored.log\n")
git("add", "-A")
git("commit", "-q", "-m", "base")
cwd = str(repo)

# --- stamp the reviewed working state, without touching the dev's staging area
(repo / "a.txt").write_text("two\n")
(repo / "b.txt").write_text("new file\n")
(repo / "scratch.md").write_text("notes, never committed\n")
(repo / "ignored.log").write_text("x\n")
git("add", "b.txt")
staged_before = git("diff", "--cached", "--name-only").stdout
st = rv.stamp(cwd)
check("stamp recorded", st and st["branch"] == "feat" and (Path(rv.stamp_path(cwd))).exists())
check("staging area untouched", git("diff", "--cached", "--name-only").stdout == staged_before)
check("untracked files listed, ignored ones not", "scratch.md" in st["untracked"] and "ignored.log" not in st["untracked"])

# --- two logical commits of the reviewed work, scratch left out: the push matches
git("add", "a.txt")
git("commit", "-q", "-m", "change a")
git("add", "b.txt")
git("commit", "-q", "-m", "add b")
check("drift empty when HEAD carries what was reviewed", rv.drift(cwd, rv.load(cwd), "HEAD") == [])
check("matching push allowed", rv.check_push(cwd, "feat", "HEAD") is None)
check("…and consumes the stamp", rv.load(cwd) is None)
check("no stamp: nothing enforced", rv.check_push(cwd, "feat", "HEAD") is None)

# --- a change after the review: the push is blocked and the file is named
rv.stamp(cwd)
(repo / "a.txt").write_text("three, after the review\n")
git("commit", "-q", "-am", "sneaky change")
msg = rv.check_push(cwd, "feat", "HEAD")
check("changed-after-review push blocked", msg is not None and "a.txt" in msg and "revisó" in msg)
check("blocked push keeps the stamp", rv.load(cwd) is not None)
check("another branch is not affected", rv.check_push(cwd, "other", "HEAD") is None)

# --- the guard enforces it: as the AI's tool hook and as the git pre-push hook
r = guard({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": cwd})
check("tool hook denies the push", "permissionDecision" in r.stdout and "a.txt" in r.stdout)
head = git("rev-parse", "HEAD").stdout.strip()
r = guard(args=("--git-hook", "pre-push"), stdin=f"refs/heads/feat {head} refs/heads/feat {'0' * 40}\n")
check("git pre-push hook blocks it", r.returncode == 1 and "a.txt" in r.stderr)
env["EDEN_REVIEW_OFF"] = "1"
r = guard(args=("--git-hook", "pre-push"), stdin=f"refs/heads/feat {head} refs/heads/feat {'0' * 40}\n")
check("EDEN_REVIEW_OFF lets the dev push anyway", r.returncode == 0)
env.pop("EDEN_REVIEW_OFF")
check("clear drops the stamp (the dev's call)", rv.clear(cwd) and rv.load(cwd) is None)
r = guard({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": cwd})
check("without a stamp the push passes", not r.stdout.strip())

# --- the CLI
r = subprocess.run([sys.executable, "-I", str(PLUGIN / "hooks" / "eden_review.py"), "status"], cwd=repo,
                   capture_output=True, text=True, encoding="utf-8")
check("status without stamp", "Sin sello" in r.stdout)

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
