"""Eden hosts — the one table of what each AI tool is and can do.

Data only, no imports beyond the standard library: hooks (eden_host.py), the packager (scripts/eden_port.py)
and the provider layer (scripts/eden_ai.py) all read it, so a tool's facts live in exactly one place.

Per host:
  label           display name
  family          hook contract: "claude" (Claude's payload and hookSpecificOutput deny, exit 0),
                  "gemini" / "grok" / "crush" ({"decision": "deny"} + exit 2), "cursor" ({"permission":
                  "deny"} + exit 2), "opencode" (in-process plugin; exit 2 from the scripts it calls)
  native          loads the Claude plugin (.claude-plugin) by itself
  port            what `/eden:setup hosts install` adds: None (nothing), "agents", or "package"
  clis            executable names, PATH first
  app_globs       where a desktop app ships its CLI off the PATH: (env var or "HOME", glob)
  config_dir      the tool's home folder, relative to the user's home
  instructions    the project instructions file it reads
  skills          True when it reads the shared Agent Skills folder ~/.agents/skills
  shell_tools     its shell tool names (hook matchers; normalized to "Bash")
  read_tools      its file-read tool names (normalized to "Read")
  tiers           model per tier — plan: the orchestrating session (/eden:go), strong: complex units,
                  fast: bounded units (None = omit, the agent inherits the session's model)
  invoke          how the dev calls an Eden skill there (x = the skill)
  session_hint    how the dev puts the session on the strong model
  verified        what was run in the real tool (see docs/guide.md); "" = built from docs only
"""

HOSTS = {
    "claude": dict(label="Claude Code", family="claude", native=True, port=None, clis=["claude"],
                   # the Claude desktop app bundles the Claude Code CLI off the PATH (verified on Windows)
                   app_globs=[("LOCALAPPDATA", "Claude-Data/*/claude-code/*/*/claude.exe")],
                   config_dir=".claude", instructions="CLAUDE.md", skills=False,
                   shell_tools=["Bash", "PowerShell"], read_tools=["Read", "NotebookRead"],
                   tiers={"plan": "fable", "strong": "opus", "fast": "sonnet"}, invoke="`/eden:x`",
                   session_hint="`/model opus` (o `\"model\": \"opus\"` en settings.json)", verified="native"),
    "qwen": dict(label="Qwen Code", family="claude", native=True, port=None, clis=["qwen"],
                 app_globs=[("LOCALAPPDATA", "qwen-code/bin/qwen.cmd")], config_dir=".qwen", instructions="QWEN.md",
                 skills=False, shell_tools=["run_shell_command"], read_tools=["read_file", "read_many_files"],
                 tiers={"plan": "inherit", "strong": "inherit", "fast": "fast"}, invoke="`/eden:x`",
                 session_hint="`/model` y elige el modelo más capaz", verified="0.26.5"),
    "codex": dict(label="Codex", family="claude", native=True, port="agents", clis=["codex"],
                  app_globs=[("LOCALAPPDATA", "OpenAI/Codex/bin/*/codex.exe"),
                             ("HOME", "Applications/Codex.app/Contents/Resources/codex")],
                  config_dir=".codex", instructions="AGENTS.md", skills=False,
                  shell_tools=["Bash", "shell", "exec_command", "shell_command"], read_tools=[],
                  tiers={"plan": None, "strong": None, "fast": None}, invoke="`$eden-x`",
                  session_hint="`/model` (o `model` en ~/.codex/config.toml)", verified="0.167"),
    "kimi": dict(label="Kimi Code", family="claude", native=False, port="package", clis=["kimi"], app_globs=[],
                 config_dir=".kimi-code", instructions="AGENTS.md", skills=True,
                 shell_tools=["Bash"], read_tools=["Read"], tiers={"plan": None, "strong": None, "fast": None},
                 invoke="`/eden-x`", session_hint="`/model`", verified=""),
    "gemini": dict(label="Gemini CLI", family="gemini", native=False, port="package", clis=["gemini", "agy"],
                   app_globs=[], config_dir=".gemini", instructions="GEMINI.md", skills=True,
                   shell_tools=["run_shell_command"], read_tools=["read_file", "read_many_files"],
                   tiers={"plan": None, "strong": None, "fast": None}, invoke="`/eden:x`",
                   session_hint="`/model` y elige Pro", verified=""),
    "antigravity": dict(label="Antigravity", family="gemini", native=False, port=None, clis=["agy"], app_globs=[],
                        config_dir=".gemini", instructions="GEMINI.md", skills=True,
                        shell_tools=["run_shell_command"], read_tools=["read_file", "read_many_files"],
                        tiers={"plan": None, "strong": None, "fast": None}, invoke="`/eden:x`",
                        session_hint="el selector de modelo", verified=""),
    "cursor": dict(label="Cursor", family="cursor", native=False, port="package", clis=["cursor-agent", "agent"],
                   app_globs=[], config_dir=".cursor", instructions="AGENTS.md", skills=True,
                   shell_tools=["Shell"], read_tools=["Read"], tiers={"plan": "inherit", "strong": "inherit", "fast": "inherit"},
                   invoke="`/eden-x`", session_hint="el selector de modelo del chat", verified=""),
    "opencode": dict(label="OpenCode", family="opencode", native=False, port="package", clis=["opencode"],
                     app_globs=[], config_dir=".config/opencode", instructions="AGENTS.md", skills=True,
                     shell_tools=["bash"], read_tools=["read"], tiers={"plan": None, "strong": None, "fast": None},
                     invoke="`/eden-x`", session_hint="`/models`", verified="2.2.6"),
    "grok": dict(label="Grok Build", family="grok", native=True, port=None, clis=["grok"], app_globs=[],
                 config_dir=".grok", instructions="AGENTS.md", skills=True, shell_tools=["Bash"],
                 read_tools=["Read"], tiers={"plan": None, "strong": None, "fast": None}, invoke="`/eden:x`",
                 session_hint="`/model`", verified=""),
    "crush": dict(label="Crush", family="crush", native=False, port=None, clis=["crush"], app_globs=[],
                  config_dir=".config/crush", instructions="AGENTS.md", skills=False, shell_tools=["bash"],
                  read_tools=["view"], tiers={"plan": None, "strong": None, "fast": None}, invoke="el nombre del skill (`eden-x`)",
                  session_hint="el selector de modelo", verified=""),
}

# Host event names → Claude's.
EVENT_ALIASES = {
    "BeforeTool": "PreToolUse", "BeforeAgent": "UserPromptSubmit", "PreCompress": "PreCompact",
    "preToolUse": "PreToolUse", "beforeShellExecution": "PreToolUse", "beforeMCPExecution": "PreToolUse",
    "beforeReadFile": "PreToolUse", "beforeSubmitPrompt": "UserPromptSubmit", "sessionStart": "SessionStart",
    "sessionEnd": "SessionEnd", "preCompact": "PreCompact", "TurnStart": "UserPromptSubmit",
}
# Shell tools that no table entry names but some hosts or versions use.
EXTRA_SHELL = {"execute_command", "terminal", "run_terminal_cmd"}
EXTRA_READ = {"view_file", "readfile", "read_text_file"}


def shell_tools():
    """Every host's shell tool name, lowercased."""
    return {t.lower() for h in HOSTS.values() for t in h["shell_tools"]} | EXTRA_SHELL


def read_tools():
    """Every host's file-read tool name, lowercased."""
    return {t.lower() for h in HOSTS.values() for t in h["read_tools"]} | EXTRA_READ


def family(host):
    return HOSTS.get(host, {}).get("family", "unknown")


def by(key, value=True):
    return [name for name, h in HOSTS.items() if h.get(key) == value]
