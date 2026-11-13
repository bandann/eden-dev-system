import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN / "hooks"))
spec = importlib.util.spec_from_file_location("eden_ai_review", PLUGIN / "hooks" / "eden_ai_review.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


repo = Path(tempfile.mkdtemp())
env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e.x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e.x")
for k in ("EDEN_AI_REVIEW_OFF", "EDEN_GUARD_OFF", "EDEN_HOST", "EDEN_DISTILLER"):
    env.pop(k, None)
    os.environ.pop(k, None)


def git(*a):
    return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)


def set_cfg(**pre):
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "project-config.json").write_text(json.dumps({"review": {"precommit": pre}}))


git("init", "-q")
(repo / "AGENTS.md").write_text("Never use var in JavaScript.\n")
(repo / "app.js").write_text("const a = 1;\n")
git("add", "-A")
git("commit", "-q", "-m", "base")
cwd = str(repo)
(repo / "app.js").write_text("var a = 1;\nconsole.log(a)\n")
git("add", "app.js")

# --- parsing
check("parse plain JSON", ar.parse_findings('{"findings": [{"severity": "high"}]}') == [{"severity": "high"}])
check("parse JSON wrapped in prose", ar.parse_findings('Sure:\n```json\n{"findings": []}\n```') == [])
check("unreadable answer -> None", ar.parse_findings("looks good to me") is None)

# --- off by default
check("disabled by default: no call", ar.review(cwd, run=lambda p, t: 1 / 0) == (None, []))

set_cfg(enabled=True, block_on="high")
seen = {}


def fake(answer):
    def run(prompt, timeout):
        seen["prompt"] = prompt
        return answer
    return run


msg, notes = ar.review(cwd, run=fake('{"findings": [{"severity": "high", "file": "app.js", "line": 1, '
                                     '"issue": "var used", "fix": "use const"}]}'))
check("high finding blocks", msg is not None and "app.js:1" in msg and "var used" in msg)
check("the prompt carries the diff and the project's instructions",
      "var a = 1" in seen["prompt"] and "Never use var" in seen["prompt"])
msg, notes = ar.review(cwd, run=fake('{"findings": [{"severity": "medium", "file": "app.js", "line": 2, "issue": "log left"}]}'))
check("medium finding does not block, is shown", msg is None and any("log left" in n for n in notes))
msg, notes = ar.review(cwd, run=lambda p, t: 1 / 0)
check("same staged tree already passed: not sent again", msg is None and any("ya pasó" in n for n in notes))
(repo / "app.js").write_text("const a = 2;\n")
git("add", "app.js")
msg, notes = ar.review(cwd, run=fake("I cannot help"))
check("unreadable answer fails open", msg is None and any("no se pudo leer" in n for n in notes))


def boom(p, t):
    raise TimeoutError("provider took too long")


msg, notes = ar.review(cwd, run=boom)
check("provider error fails open, says why", msg is None and any("no corrió" in n and "TimeoutError" in n for n in notes))
set_cfg(enabled=True, max_diff_chars=10)
msg, notes = ar.review(cwd, run=lambda p, t: 1 / 0)
check("diff over the limit: skipped, not blocked", msg is None and any("max_diff_chars" in n for n in notes))
set_cfg(enabled=True, block_on="critical")
msg, _ = ar.review(cwd, run=fake('{"findings": [{"severity": "high", "issue": "x"}]}'))
check("block_on raises the floor", msg is None)
os.environ["EDEN_AI_REVIEW_OFF"] = "1"
check("EDEN_AI_REVIEW_OFF skips it", ar.review(cwd, run=lambda p, t: 1 / 0) == (None, []))
os.environ.pop("EDEN_AI_REVIEW_OFF")

# --- end to end: git pre-commit hook -> eden_ai -> a CLI provider (a fake that answers JSON)
home = Path(tempfile.mkdtemp())
(home / ".claude").mkdir()
answer = json.dumps({"findings": [{"severity": "critical", "file": "app.js", "line": 1, "issue": "drops the table"}]})
fake_cli = [sys.executable, "-c", f"import sys; sys.stdin.read(); print({answer!r})"]
(home / ".claude" / "eden-config.json").write_text(json.dumps({"ai": {"provider": "fakecli", "providers": {"fakecli": {"cmd": fake_cli}}}}))
set_cfg(enabled=True, block_on="high")
(repo / "app.js").write_text("const a = 3;\n")
git("add", "app.js")
henv = dict(env, HOME=str(home), USERPROFILE=str(home))
r = subprocess.run([sys.executable, "-I", str(PLUGIN / "hooks" / "eden_guard.py"), "--git-hook", "pre-commit"],
                   cwd=repo, capture_output=True, text=True, encoding="utf-8", env=henv)
check("pre-commit hook blocks through the configured provider", r.returncode == 1 and "drops the table" in r.stderr)

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
