import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "hooks" / "eden_secret_guard.py"
spec = importlib.util.spec_from_file_location("eden_secret_guard", SCRIPT)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def run(payload, host=None, env=None, cwd=None):
    args = [sys.executable, "-I", str(SCRIPT)] + (["--host", host] if host else [])
    e = dict(os.environ, **(env or {}))
    e.pop("EDEN_HOST", None)
    e.pop("EDEN_GUARD_OFF", None)
    e.update(env or {})
    return subprocess.run(args, input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8", env=e, cwd=cwd)


def denied(r):
    return "deny" in r.stdout or r.returncode == 2


def pre(tool, **tin):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tin}


# --- what counts as a secret file (pure string check)
for p in (".env", "C:\\p\\.env", "/a/.env.local", "prod.env", "server.key", "cert.pem", "app.p12", "id_rsa",
          "/home/u/.ssh/id_ed25519", "/home/u/.ssh/deploy_key", "~/.aws/credentials", ".netrc", "_netrc", ".pgpass",
          ".git-credentials", "/x/application_default_credentials.json"):
    check(f"sensitive: {p}", bool(g.sensitive(p)))
for p in (".env.example", ".env.sample", ".env.template", "id_ed25519.pub", "/home/u/.ssh/known_hosts",
          "/home/u/.ssh/config", "src/env.ts", "environment.md", "keys.md", "README.md", ""):
    check(f"not sensitive: {p or '(empty)'}", not g.sensitive(p))

# --- tool calls
cases = [
    (pre("Read", file_path=".env"), True),
    (pre("Read", file_path=".env.example"), False),
    (pre("NotebookRead", notebook_path="secrets/id_rsa"), True),
    (pre("Grep", pattern="KEY", path=".env.production"), True),
    (pre("Grep", pattern="KEY", glob="*.pem"), True),
    (pre("Grep", pattern="KEY", path="src"), False),
    (pre("Bash", command="cat .env"), True),
    (pre("Bash", command="ls -la && cp .env.local /tmp/x"), True),
    (pre("Bash", command="grep TOKEN < prod.env"), True),
    (pre("PowerShell", command="Get-Content ~/.aws/credentials"), True),
    (pre("Bash", command="docker run --env-file .env app"), False),
    (pre("Bash", command="echo 'API_KEY=' > .env"), False),
    (pre("Bash", command="rm .env && ls"), False),
    (pre("Bash", command="git status"), False),
    (pre("Edit", file_path=".env"), False),  # writing a .env the dev asked for is not reading it
]
for payload, want in cases:
    check(f"{'deny' if want else 'allow'}: {payload['tool_name']} {json.dumps(payload['tool_input'])[:60]}",
          denied(run(payload)) == want)

# --- other hosts' payloads
r = run({"hook_event_name": "BeforeTool", "tool_name": "read_file", "tool_input": {"absolute_path": "/w/server.key"}})
check("gemini read_file denied with exit 2", r.returncode == 2 and json.loads(r.stdout)["decision"] == "deny")
r = run({"hook_event_name": "beforeReadFile", "file_path": "/w/.env", "conversation_id": "c"})
check("cursor beforeReadFile denied", r.returncode == 2 and json.loads(r.stdout)["permission"] == "deny")
r = run({"hook_event_name": "PreToolUse", "tool_name": "read", "tool_input": {"filePath": "/w/.env"}}, host="opencode")
check("opencode read denied (exit 2)", r.returncode == 2)
r = run(pre("Read", file_path=".env"))
check("claude: hookSpecificOutput deny, reason in Spanish, no value",
      json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny" and "secretos" in r.stdout)

# --- fast path, kill switch, the dev's exceptions
r = run(pre("Bash", command="npm test"))
check("no hint in the payload: silent", r.returncode == 0 and not r.stdout.strip())
check("EDEN_GUARD_OFF disables it", not denied(run(pre("Read", file_path=".env"), env={"EDEN_GUARD_OFF": "1"})))
proj = Path(tempfile.mkdtemp())
(proj / ".claude").mkdir()
(proj / ".claude" / "project-config.json").write_text(json.dumps({"security": {"allow_read": [".env.test"]}}))
payload = {**pre("Read", file_path=".env.test"), "cwd": str(proj)}
check("security.allow_read lets the dev's exception through", not denied(run(payload, cwd=str(proj))))
check("…and only that one", denied(run({**pre("Read", file_path=".env"), "cwd": str(proj)}, cwd=str(proj))))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
