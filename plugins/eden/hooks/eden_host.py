"""Eden host — one hook contract for every agentic CLI that runs Eden's hooks.

Eden's hooks were written against Claude Code's contract. Other hosts call the same scripts with
their own payload and expect their own answer. This module is the only place that knows the
differences, so every hook reads `read_payload()` and answers with `deny()` / `emit()`:

  Input   read_payload() → a Claude-shaped dict whatever the host sent:
            hook_event_name (Claude names: PreToolUse, SessionStart, SessionEnd, PreCompact,
            UserPromptSubmit), tool_name ("Bash" for any shell tool), tool_input (with .command for
            a shell call), cwd, session_id, transcript_path, prompt — plus `host` and `_raw`.
  Output  deny(reason)            block the tool call, in the host's format.
          emit(event, context, message)   add context to the conversation / show a line to the dev.

Host = `--host <name>` in argv (the generated packages pass it, see scripts/eden_port.py), else
$EDEN_HOST, else inferred from the payload and the environment, else "claude". Known hosts:

  claude, qwen, codex, kimi   Claude's own contract (payload, hookSpecificOutput deny/context).
  gemini (and antigravity)    BeforeTool / BeforeAgent / PreCompress, run_shell_command,
                              {"decision": "deny", "reason"} — plus exit code 2.
  cursor                      camelCase events (preToolUse, beforeShellExecution…), Shell tool,
                              conversation_id / workspace_roots, {"permission": "deny", …} + exit 2.
  grok                        Claude's event names, camelCase keys (hookEventName, toolName…),
                              {"decision": "deny", "reason"} + exit 2.
  crush                       Claude's names, lowercase bash tool, {"decision": "deny"} + exit 2.

Exit code 2 with the reason on stderr is the one blocking signal every host documents, so it is the
fallback for any host this module does not know. Claude-family hosts keep the exact JSON they always
got (exit 0), so Claude Code behaves exactly as before.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eden_hosts  # the one table of what each AI tool is (hooks/eden_hosts.py)

CLAUDE_FAMILY = set(eden_hosts.by("family", "claude"))
KNOWN = set(eden_hosts.HOSTS)
EVENTS = eden_hosts.EVENT_ALIASES  # host event name → Claude's
SHELL_TOOLS = eden_hosts.shell_tools()
READ_TOOLS = eden_hosts.read_tools()
PATH_KEYS = ("file_path", "path", "absolute_path", "filePath", "target_file", "notebook_path")

_host = None


def _snake(key):
    return "".join("_" + c.lower() if c.isupper() else c for c in key).lstrip("_")


def detect(raw, env=None, argv=None):
    """Which host called us. Explicit beats inferred; unknown shapes are Claude's."""
    env = os.environ if env is None else env
    argv = sys.argv if argv is None else argv
    if "--host" in argv[:-1]:
        return argv[argv.index("--host") + 1].lower()
    if env.get("EDEN_HOST"):
        return env["EDEN_HOST"].lower()
    if "hookEventName" in raw or "toolName" in raw:
        return "grok"
    if "conversation_id" in raw or "workspace_roots" in raw or env.get("CURSOR_PLUGIN_ROOT"):
        return "cursor"
    event = raw.get("hook_event_name") or ""
    if event in ("BeforeTool", "BeforeAgent", "PreCompress", "AfterTool", "AfterAgent") or env.get("GEMINI_PROJECT_DIR"):
        return "gemini"
    if env.get("KIMI_PLUGIN_ROOT"):
        return "kimi"
    transcript = str(raw.get("transcript_path") or "").replace("\\", "/")
    if "/.codex/" in transcript or (env.get("PLUGIN_ROOT") and env.get("CODEX_HOME")):
        return "codex"
    if "/.qwen/" in transcript:
        return "qwen"
    if event == "TurnStart":
        return "crush"
    return "claude"


def normalize(raw, host):
    """Claude-shaped payload from any host's payload."""
    p = {(_snake(k) if host == "grok" else k): v for k, v in raw.items()}
    event = p.get("hook_event_name") or ""
    p["hook_event_name"] = EVENTS.get(event, event)
    tool = str(p.get("tool_name") or "")
    tin = p.get("tool_input") if isinstance(p.get("tool_input"), dict) else {}
    if event == "beforeShellExecution":  # Cursor: the command comes at the top level
        tool, tin = "Bash", {"command": raw.get("command") or ""}
    elif event == "beforeReadFile":  # Cursor: the file comes at the top level
        tool, tin = "Read", {"file_path": raw.get("file_path") or raw.get("path") or ""}
    if tool.lower() in READ_TOOLS:
        tool = "Read"
        paths = tin.get("paths") if isinstance(tin.get("paths"), list) else []
        first = next((tin[k] for k in PATH_KEYS if isinstance(tin.get(k), str) and tin[k]), "")
        tin = dict(tin, file_path=first or (paths[0] if paths else ""), paths=[str(x) for x in paths] or [first])
    if tool.lower() in SHELL_TOOLS:
        tool = "PowerShell" if tool.lower() == "powershell" else "Bash"
        if not tin.get("command"):
            tin = dict(tin, command=tin.get("cmd") or tin.get("script") or "")
    if isinstance(tin.get("command"), list):  # some hosts pass argv, not a string
        tin = dict(tin, command=" ".join(map(str, tin["command"])))
    p["tool_name"], p["tool_input"] = tool, tin
    if not p.get("cwd"):
        roots = p.get("workspace_roots") or []
        p["cwd"] = (roots[0] if roots else "") or os.environ.get("GEMINI_PROJECT_DIR") or \
            os.environ.get("CLAUDE_PROJECT_DIR") or ""
    if not p.get("session_id"):
        p["session_id"] = p.get("conversation_id") or p.get("thread_id") or ""
    if not p.get("prompt") and isinstance(p.get("user_prompt"), str):
        p["prompt"] = p["user_prompt"]
    p["host"], p["_raw"] = host, raw
    return p


def read_payload(stream=None):
    """The hook payload, normalized. {} (host still detected) when stdin is empty or not JSON."""
    global _host
    try:
        raw = json.loads((stream or sys.stdin).read() or "{}")
        if not isinstance(raw, dict):
            raw = {}
    except ValueError:
        raw = {}
    _host = detect(raw)
    return normalize(raw, _host)


def host():
    return _host or detect({})


def _print(obj):
    print(json.dumps(obj))  # ensure_ascii: safe on a cp1252 console


def _stderr(text):
    try:
        sys.stderr.write(text + "\n")
    except UnicodeEncodeError:
        sys.stderr.write(text.encode("ascii", "replace").decode("ascii") + "\n")
    sys.stderr.flush()


def deny_output(reason, h=None):
    """(stdout object, exit code) that blocks the current tool call on host h."""
    h = h or host()
    if h in CLAUDE_FAMILY:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": reason}}, 0
    if h == "cursor":
        return {"permission": "deny", "user_message": reason, "agent_message": reason}, 2
    return {"decision": "deny", "reason": reason}, 2


def deny(reason):
    """Block the tool call. Exits the process for hosts that need exit code 2."""
    obj, code = deny_output(reason)
    _print(obj)
    if code:
        _stderr(reason)
        sys.exit(code)


def emit_output(event, context=None, message=None, h=None):
    """stdout object that adds `context` for the model and shows `message` to the dev."""
    h = h or host()
    out = {}
    if message:
        out["systemMessage"] = message
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
        if h == "cursor":
            out["additional_context"] = context
    return out


def emit(event, context=None, message=None):
    out = emit_output(event, context, message)
    if out:
        _print(out)
