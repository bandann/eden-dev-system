import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, PLUGIN / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


h = load("eden_host", "hooks/eden_host.py")
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def norm(raw, env=None, argv=()):
    host = h.detect(raw, env or {}, list(argv))
    return h.normalize(raw, host)


# --- detection
check("claude by default", h.detect({"hook_event_name": "PreToolUse", "tool_name": "Bash"}, {}, []) == "claude")
check("--host wins", h.detect({"hookEventName": "x"}, {"EDEN_HOST": "kimi"}, ["x", "--host", "gemini"]) == "gemini")
check("EDEN_HOST next", h.detect({}, {"EDEN_HOST": "Cursor"}, []) == "cursor")
check("grok by camelCase", h.detect({"hookEventName": "PreToolUse"}, {}, []) == "grok")
check("cursor by conversation_id", h.detect({"conversation_id": "c"}, {}, []) == "cursor")
check("gemini by event name", h.detect({"hook_event_name": "BeforeTool"}, {}, []) == "gemini")
check("codex by transcript", h.detect({"transcript_path": r"C:\Users\x\.codex\sessions\a.jsonl"}, {}, []) == "codex")
check("qwen by transcript", h.detect({"transcript_path": "/home/x/.qwen/projects/p/chats/a.jsonl"}, {}, []) == "qwen")
check("kimi by env", h.detect({}, {"KIMI_PLUGIN_ROOT": "/p"}, []) == "kimi")

# --- normalization
p = norm({"hook_event_name": "BeforeTool", "tool_name": "run_shell_command", "tool_input": {"command": "git commit -m x"},
          "session_id": "s", "cwd": "/r"})
check("gemini BeforeTool → PreToolUse + Bash", p["hook_event_name"] == "PreToolUse" and p["tool_name"] == "Bash"
      and p["tool_input"]["command"] == "git commit -m x")
p = norm({"hook_event_name": "beforeShellExecution", "command": "git push", "conversation_id": "c1",
          "workspace_roots": ["/w"]})
check("cursor shell → PreToolUse/Bash, cwd and session", p["hook_event_name"] == "PreToolUse" and p["tool_name"] == "Bash"
      and p["tool_input"]["command"] == "git push" and p["cwd"] == "/w" and p["session_id"] == "c1")
p = norm({"hookEventName": "PreToolUse", "toolName": "Bash", "toolInput": {"command": "ls"}, "sessionId": "g",
          "transcriptPath": "/t.jsonl"})
check("grok camelCase → snake", p["hook_event_name"] == "PreToolUse" and p["tool_input"]["command"] == "ls"
      and p["session_id"] == "g" and p["transcript_path"] == "/t.jsonl")
p = norm({"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": ["git", "commit"]}})
check("crush lowercase bash + argv list", p["tool_name"] == "Bash" and p["tool_input"]["command"] == "git commit")
p = norm({"hook_event_name": "PreToolUse", "tool_name": "PowerShell", "tool_input": {"command": "git push"}})
check("PowerShell kept", p["tool_name"] == "PowerShell")
p = norm({"hook_event_name": "PreCompress"})
check("PreCompress → PreCompact", p["hook_event_name"] == "PreCompact")
p = norm({"hook_event_name": "PreToolUse", "tool_name": "mcp__figma-console__figma_get_status", "tool_input": {"x": 1}})
check("non-shell tool untouched", p["tool_name"] == "mcp__figma-console__figma_get_status" and p["tool_input"] == {"x": 1})
check("empty stdin is safe", h.read_payload(io.StringIO(""))["hook_event_name"] == "")
check("non-JSON stdin is safe", h.read_payload(io.StringIO("nope"))["tool_input"] == {})

# --- outputs
obj, code = h.deny_output("r", "claude")
check("claude deny unchanged", code == 0 and obj["hookSpecificOutput"]["permissionDecision"] == "deny"
      and obj["hookSpecificOutput"]["permissionDecisionReason"] == "r")
check("qwen/codex/kimi use Claude's form", all(h.deny_output("r", x)[1] == 0 for x in ("qwen", "codex", "kimi")))
obj, code = h.deny_output("r", "gemini")
check("gemini deny + exit 2", code == 2 and obj == {"decision": "deny", "reason": "r"})
obj, code = h.deny_output("r", "cursor")
check("cursor deny + exit 2", code == 2 and obj["permission"] == "deny" and obj["agent_message"] == "r")
check("unknown host falls back to exit 2", h.deny_output("r", "somecli")[1] == 2)
out = h.emit_output("SessionStart", "ctx", "msg", "claude")
check("claude context + message", out["hookSpecificOutput"]["additionalContext"] == "ctx" and out["systemMessage"] == "msg")
check("cursor context alias", h.emit_output("SessionStart", "ctx", None, "cursor")["additional_context"] == "ctx")
check("nothing to emit → empty", h.emit_output("SessionStart", None, None, "claude") == {})


def run_hook(rel, payload, env=None, args=()):
    e = dict(os.environ, **(env or {}))
    e.pop("EDEN_HOST", None)
    e.update(env or {})
    return subprocess.run([sys.executable, "-I", str(PLUGIN / rel), *args], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", env=e)


# --- real hooks through other hosts' payloads
write = {"hook_event_name": "BeforeTool", "tool_name": "mcp_figma-console_figma_create_frame", "tool_input": {}}
res = run_hook("hooks/eden_figma_guard.py", write)
check("gemini: Figma write denied with exit 2", res.returncode == 2 and json.loads(res.stdout)["decision"] == "deny")
read = {"hook_event_name": "BeforeTool", "tool_name": "mcp_figma-console_figma_get_status", "tool_input": {}}
res = run_hook("hooks/eden_figma_guard.py", read)
check("gemini: Figma read allowed", res.returncode == 0 and not res.stdout.strip())
res = run_hook("hooks/eden_figma_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "mcp__figma-console__figma_delete_node"})
check("claude: Figma write denied the old way", res.returncode == 0 and "permissionDecision" in res.stdout)
fg = load("eden_figma_guard", "hooks/eden_figma_guard.py")
check("figma short names across hosts", [fg.short_name(n) for n in (
    "mcp__claude_ai_Figma__get_screenshot", "figma:get_screenshot", "figma-console/figma_execute",
    "mcp_figma-console_figma_get_status", "mcp_figma_get_design_context")]
      == ["get_screenshot", "get_screenshot", "figma_execute", "figma_get_status", "figma_get_design_context"])
res = run_hook("hooks/eden_rules.py", {"hook_event_name": "sessionStart", "conversation_id": "c"})
check("cursor: rules context emitted", res.returncode == 0 and json.loads(res.stdout).get("additional_context"))

# --- transcripts: Codex rollout and generic {role, content} lines condense like Claude's
b = load("eden_brain", "hooks/eden_brain.py")
tmp = Path(tempfile.mkdtemp())
codex = tmp / "rollout.jsonl"
codex.write_text("\n".join(json.dumps(x) for x in [
    {"type": "session_meta", "payload": {"cwd": "/repo"}},
    {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
        {"type": "input_text", "text": "<environment_context>noise</environment_context>"}]}},
    {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
        {"type": "input_text", "text": "no uses yarn, siempre pnpm"}]}},
    {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [
        {"type": "output_text", "text": "Entendido."}]}},
    {"type": "response_item", "payload": {"type": "function_call", "name": "shell",
                                          "arguments": json.dumps({"command": ["pnpm", "install"]})}},
    {"type": "event_msg", "payload": {"type": "token_count"}},
]), encoding="utf-8")
parts, stats, n = b.condense(codex, 0, 80000)
text = "\n".join(parts) if isinstance(parts, list) else str(parts)
check("codex: user words kept, noise dropped", "siempre pnpm" in text and "noise" not in text and stats["users"] == 1)
check("codex: tool call and cwd", stats["tools"] == 1 and "pnpm install" in text and stats["cwd"] == "/repo")
generic = tmp / "generic.jsonl"
generic.write_text(json.dumps({"role": "user", "content": "recuerda: tabs, no espacios"}) + "\n"
                   + json.dumps({"role": "assistant", "content": [{"type": "text", "text": "ok"}]}), encoding="utf-8")
parts, stats, n = b.condense(generic, 0, 80000)
check("generic {role, content} lines", stats["users"] == 1 and "tabs, no espacios" in "\n".join(map(str, parts)))

# --- AI signatures of other assistants
g = load("eden_guard", "hooks/eden_guard.py")
for sig in ("Co-Authored-By: Claude <noreply@anthropic.com>", "Co-authored-by: Codex <codex@openai.com>",
            "Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>", "Co-Authored-By: Gemini <gemini@google.com>",
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)", "Generated with Qwen Code"):
    check(f"AI signature caught: {sig[:40]}", bool(g.AI_SIGNATURE.search(sig)))
for ok in ("Co-authored-by: Haider Ali <haider@example.com>", "Co-authored-by: Jane Doe <jane@example.com>",
           "fix: cursor position in editor"):
    check(f"human / ordinary text passes: {ok[:40]}", not g.AI_SIGNATURE.search(ok))

# --- git hooks end to end: install, block a secret, block a signature, pass a clean commit, chain, remove
home = tmp / "home"
(home / ".claude").mkdir(parents=True)
repo = tmp / "repo"
repo.mkdir()
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e.x",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e.x")
env.pop("EDEN_GUARD_OFF", None)


def git(*a, check_rc=False):
    return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)


def setup(*a):
    return subprocess.run([sys.executable, "-I", str(PLUGIN / "scripts" / "eden_setup.py"), "githooks", *a],
                          cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)


git("init", "-q")
(repo / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\necho previous-hook-ran >&2\n", encoding="utf-8", newline="\n")
os.chmod(repo / ".git" / "hooks" / "pre-commit", 0o755)
dry = setup()
check("githooks dry run writes nothing", "haría" in dry.stdout and not (repo / ".git" / "hooks" / "commit-msg").exists())
res = setup("--apply")
hooks = repo / ".git" / "hooks"
check("githooks installed, previous hook kept", (hooks / "pre-push").exists() and (hooks / "pre-commit.eden-prev").exists()
      and (home / ".claude" / "eden-cache" / "plugin_root").exists())
fake_key = "AKIA" + "ABCDEFGHIJKLMNOP"  # assembled so this file itself carries no key
(repo / "config.js").write_text(f'const k = "{fake_key}";\n', encoding="utf-8")
git("add", "config.js")
res = git("commit", "-m", "add config")
check("secret commit blocked by the git hook", res.returncode != 0 and "Eden guard" in res.stderr
      and fake_key not in res.stderr)
check("previous pre-commit still ran", "previous-hook-ran" in res.stderr)
(repo / "config.js").write_text("const k = process.env.KEY;\n", encoding="utf-8")
git("add", "config.js")
res = git("commit", "-m", "feat: config\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
check("AI-signed commit blocked by commit-msg", res.returncode != 0 and "firma" in res.stderr)
res = git("commit", "-m", "feat: config")
check("clean commit passes", res.returncode == 0)
env["EDEN_GUARD_OFF"] = "1"
(repo / "b.txt").write_text("x", encoding="utf-8")
git("add", "b.txt")
check("EDEN_GUARD_OFF skips", git("commit", "-m", "x\n\nCo-Authored-By: Claude <noreply@anthropic.com>").returncode == 0)
env.pop("EDEN_GUARD_OFF")
subprocess.run(["git", "init", "-q", "--bare", str(tmp / "remote.git")], capture_output=True, env=env)
res = git("push", str(tmp / "remote.git"), "HEAD:refs/heads/main")
check("pre-push blocks the AI-signed outgoing commit", res.returncode != 0 and "Eden guard" in res.stderr)
setup("--remove", "--apply")
check("githooks removed, previous hook restored", not (hooks / "pre-push").exists() and not (hooks / "commit-msg").exists()
      and "previous-hook-ran" in (hooks / "pre-commit").read_text(encoding="utf-8"))
git("config", "core.hooksPath", ".husky")
check("core.hooksPath respected", "core.hooksPath" in setup("--apply").stdout and not (repo / ".husky").exists())

# --- the host table is the single source and complete
hs = load("eden_hosts", "hooks/eden_hosts.py")
KEYS = {"label", "family", "native", "port", "clis", "app_globs", "config_dir", "instructions", "skills",
        "shell_tools", "read_tools", "tiers", "invoke", "session_hint", "verified"}
check("every host has every field", all(set(v) == KEYS for v in hs.HOSTS.values()))
check("families are known contracts", {v["family"] for v in hs.HOSTS.values()} <= {"claude", "gemini", "grok", "crush", "cursor", "opencode"})
check("port values", {v["port"] for v in hs.HOSTS.values()} <= {None, "agents", "package"})
check("tiers have plan, strong and fast", all(set(v["tiers"]) == {"plan", "strong", "fast"} for v in hs.HOSTS.values()))
check("Claude: Fable plans, Opus and Sonnet work", hs.HOSTS["claude"]["tiers"] == {"plan": "fable", "strong": "opus", "fast": "sonnet"})
check("eden_host derives from the table", h.CLAUDE_FAMILY == set(hs.by("family", "claude")) and h.SHELL_TOOLS == hs.shell_tools())
check("every claude-family host denies the Claude way", all(h.deny_output("r", x)[1] == 0 for x in h.CLAUDE_FAMILY))
check("read tools normalize to Read", norm({"hook_event_name": "BeforeTool", "tool_name": "read_many_files",
                                           "tool_input": {"paths": ["a.md", ".env"]}})["tool_input"]["paths"] == ["a.md", ".env"])

# --- performance contracts: hooks that run on every shell call / prompt stay light
res = run_hook("hooks/eden_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "ls -la"}})
check("guard: non-git payload exits silently (fast path)", res.returncode == 0 and not res.stdout.strip())
res = run_hook("hooks/eden_brain.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"}},
               args=("learn",))
check("learn: non-git tool event exits silently (fast path)", res.returncode == 0 and not res.stdout.strip())
probe = subprocess.run([sys.executable, "-I", "-c",
                        "import importlib.util,sys;"
                        f"s=importlib.util.spec_from_file_location('b',r'{PLUGIN / 'hooks' / 'eden_brain.py'}');"
                        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                        "print('eden_ai' in sys.modules, 'urllib.request' in sys.modules)"],
                       capture_output=True, text=True)
check("brain does not load eden_ai / urllib until it distils", probe.stdout.strip() == "False False")
res = run_hook("hooks/eden_rules.py", {"hook_event_name": "SessionStart"})
ctx = json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"]
check("rules digest fits whole under the cap", "truncado" not in ctx and len(ctx) < 9500 and "## Git" in ctx)
check("rules index is compact (base path once)", ctx.count("/rules/") <= 2 and "sabores en `wordpress/flavors/`" in ctx)

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
