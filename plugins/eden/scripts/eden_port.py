"""Eden port — package the plugin for AI tools other than Claude Code.

Usage: python -I eden_port.py <detect | plan | install | uninstall | doctor | sync | build> [host …] [--apply] [--out DIR]
  detect              which AI tools are installed on this machine
  plan / install      what installing Eden for those tools writes (dry run); with --apply, does it
  uninstall           removes what install wrote for those tools (from the install record)
  doctor              checks that what was installed is there, untouched and current (changes nothing)
  sync                after a plugin update, reinstalls every recorded tool (dry run; --apply to do it)
  build --out DIR     writes one tool's package into DIR to inspect it (nothing else touched)

Claude Code, Qwen Code and Grok Build load the plugin as it is (.claude-plugin); they need none of this.

Layout (one source, three layers):
  ~/.eden/kit/                The plugin, adapted once: ${CLAUDE_PLUGIN_ROOT} → this folder,
                              `/eden:x` → `/eden-x`, `eden:agent` → `eden-agent`, $ARGUMENTS → prose.
                              Hooks and scripts run from here, so every tool shares one kit.
  ~/.agents/skills/eden-*/    The skills, in the Agent Skills standard folder that Codex, Gemini /
                              Antigravity, Cursor, Kimi Code and OpenCode all read — written once, so
                              no tool sees them twice.
  per tool                    Only what is tool-specific: its agents (in its format and model field,
                              see eden_ai.agent_model), its hooks (calling the kit with --host), and its
                              manifest / context file.

  codex     agents → ~/.codex/agents/eden-*.toml only: Codex loads the Claude plugin itself (skills and
            hooks, from the eden-kit marketplace); trust its hooks with /hooks
  cursor    plugin ~/.cursor/plugins/local/eden: .cursor-plugin/plugin.json, agents/, hooks/hooks.json
  gemini    extension ~/.gemini/extensions/eden: gemini-extension.json (context EDEN.md), agents/,
            commands/eden/*.toml (so `/eden:x` works), hooks/hooks.json. Antigravity imports it with
            `agy plugin import gemini`.
  opencode  ~/.config/opencode/agents/eden-*.md · plugins/eden.js (v2 plugin: the rules digest via the
            session `context` hook, and the two guards via `tool.hook("execute.before")`)
  kimi      ~/.eden/hosts/kimi: kimi.plugin.json + agents/ + hooks.toml — built, installed by you
  universal ~/.eden/EDEN.md (rules digest + how to call the skills) for any tool that reads AGENTS.md
            (Crush and others): reference it from your AGENTS.md

Every install is recorded in ~/.eden/installed.json with each file's sha256: Eden only overwrites or
removes files that are its own and untouched; a file that was already there, or one the dev edited,
is backed up to ~/.eden/backups first (and a pre-existing one is restored on uninstall).
Formats marked "unverified" in docs/guide.md were taken from each tool's docs, not tested in the tool.
"""
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_ai  # model tiers → each tool's agent model field

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
EDEN = HOME / ".eden"
KIT = EDEN / "kit"
SKILLS = HOME / ".agents" / "skills"
RECORD = EDEN / "installed.json"
APPLY = "--apply" in sys.argv
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
KIT_DIRS = ("agents", "brain", "config", "hooks", "memory", "profiles", "rules", "scripts", "skills", "team",
            "teams", ".claude-plugin")
KIT_FILES = ("CLAUDE.base.md", "VERSION", "THIRD_PARTY_NOTICES.md")
TEXT = {".md", ".json", ".toml", ".txt", ".yml", ".yaml"}

sys.path.insert(0, str(ROOT / "hooks"))
import eden_hosts  # the one table of what each AI tool is (hooks/eden_hosts.py)

TOOLS = eden_hosts.HOSTS
HOSTS = tuple(n for n, h in TOOLS.items() if h["port"]) + ("universal",)   # what `install` can target
NATIVE = tuple(n for n, h in TOOLS.items() if h["native"] and not h["port"])  # load .claude-plugin, nothing to add
SHARED_SKILLS = tuple(n for n, h in TOOLS.items() if h["port"] and h["skills"]) + ("universal",)
CLIS = {n: list(h["clis"]) for n, h in TOOLS.items()}
HOST_DIRS = {n: HOME / h["config_dir"] for n, h in TOOLS.items() if n != "claude"}
INVOKE = {**{n: h["invoke"] for n, h in TOOLS.items()}, "universal": "el nombre del skill (`eden-x`)"}

# Hook table: (claude event, matcher kind, script + subcommand, timeout s, name)
HOOKS = [
    ("SessionStart", None, "eden_rules.py", 15, "eden-load-rules"),
    ("SessionStart", None, "eden_brain.py start", 15, "eden-brain-recall"),
    ("UserPromptSubmit", None, "eden_context.py watch", 20, "eden-context-watch"),
    ("SessionEnd", None, "eden_brain.py learn", 30, "eden-brain-learn-on-exit"),
    ("PreCompact", None, "eden_brain.py learn", 30, "eden-brain-learn-before-compact"),
    ("PreToolUse", "shell", "eden_guard.py", 60, "eden-commit-guard"),
    ("PreToolUse", "shell", "eden_brain.py learn", 15, "eden-brain-learn-on-commit"),
    ("PreToolUse", "read", "eden_secret_guard.py", 10, "eden-secrets-readonly"),
    ("PreToolUse", "figma", "eden_figma_guard.py", 10, "eden-figma-readonly"),
]


def say(msg):
    print(msg)


# ---------------------------------------------------------------- text and frontmatter transforms

def adapt_text(text, kit=None, skill_dir=None):
    """Plugin text → tool-neutral text that points at the installed kit."""
    kit = kit or KIT
    text = text.replace("${CLAUDE_PLUGIN_ROOT}", kit.as_posix())
    if skill_dir is not None:
        text = text.replace("${CLAUDE_SKILL_DIR}", skill_dir.as_posix())
    text = re.sub(r"/eden:([\w-]+)", r"/eden-\1", text)
    text = re.sub(r"(?<![\w/.-])eden:([\w*][\w*-]*)", r"eden-\1", text)
    return text.replace("$ARGUMENTS", "(lo que el dev escribió después del comando)")


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text.replace("\r\n", "\n"), re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def parse_frontmatter(fm):
    """The flat YAML Eden uses: `key: value` and folded `key: >` blocks."""
    out, key, buf = {}, None, []
    for line in fm.splitlines():
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key is not None and buf:
                out[key] = " ".join(buf).strip()
            key, val = m.group(1), m.group(2).strip()
            buf = [] if val in (">", "|", ">-", "|-") else [val]
            if val not in (">", "|", ">-", "|-"):
                out[key] = val
        elif key is not None:
            buf.append(line.strip())
    if key is not None and buf:
        out[key] = " ".join(buf).strip()
    return out


def yq(value):
    return json.dumps(value, ensure_ascii=False)  # a JSON string is a valid YAML double-quoted scalar


def toml_str(value):
    if "'''" not in value:
        return "'''\n" + value + "'''"
    return json.dumps(value, ensure_ascii=False)


def read_only(meta):
    tools = {t.strip() for t in (meta.get("tools") or "").split(",") if t.strip()}
    banned = {t.strip() for t in (meta.get("disallowedTools") or "").split(",")}
    return bool(tools) and not ({"Write", "Edit", "NotebookEdit"} & (tools - banned))


def agents():
    """[(name, meta, body)] of the plugin's agents, body adapted to the kit."""
    out = []
    for f in sorted((ROOT / "agents").glob("*.md")):
        fm, body = split_frontmatter(f.read_text(encoding="utf-8"))
        meta = parse_frontmatter(fm)
        out.append((f.stem, meta, adapt_text(body)))
    return out


def agent_file(host, name, meta, body, ai=None):
    """(file name, content) of one agent in `host`'s format."""
    desc = adapt_text(meta.get("description", ""))
    model = eden_ai.agent_model(host, meta.get("model"), ai)
    full = f"eden-{name}"
    if host == "codex":
        lines = [f"name = {json.dumps(full)}", f"description = {json.dumps(desc, ensure_ascii=False)}"]
        if model:
            lines.append(f"model = {json.dumps(model)}")
        lines.append(f"developer_instructions = {toml_str(body.strip() + chr(10))}")
        return f"{full}.toml", "\n".join(lines) + "\n"
    fm = []
    if host != "opencode":
        fm.append(f"name: {full}")
    fm.append(f"description: {yq(desc)}")
    if host == "opencode":
        fm.append("mode: subagent")
        if read_only(meta):
            fm += ["permission:", "  edit: deny"]
    if host == "cursor" and read_only(meta):
        fm.append("readonly: true")
    if model:
        fm.append(f"model: {model}")
    return f"{full}.md", "---\n" + "\n".join(fm) + "\n---\n\n" + body.lstrip()


def skills():
    return sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())


def hook_cmd(script, host, kit=None):
    kit = kit or KIT
    parts = script.split()
    return f'python -I "{(kit / "hooks" / parts[0]).as_posix()}"' + "".join(f" {a}" for a in parts[1:]) + f" --host {host}"


# ---------------------------------------------------------------- per-tool hook configs

def hooks_claude_format(host, kit=None):
    """Codex: Claude's own hooks.json format (same events, `Bash` matcher)."""
    kit = kit or KIT
    out = {}
    for event, kind, script, timeout, name in HOOKS:
        group = {"hooks": [{"type": "command", "command": hook_cmd(script, host, kit), "timeout": timeout,
                            "statusMessage": name}]}
        if kind == "shell":
            group = {"matcher": "Bash", **group}
        elif kind == "figma":
            group = {"matcher": "mcp__.*[Ff]igma.*", **group}
        elif kind == "read":
            group = {"matcher": "Read|Grep|Bash", **group}
        out.setdefault(event, []).append(group)
    return {"hooks": out}


def hooks_gemini(kit=None):
    kit = kit or KIT
    ev = {"SessionStart": "SessionStart", "UserPromptSubmit": "BeforeAgent", "SessionEnd": "SessionEnd",
          "PreCompact": "PreCompress", "PreToolUse": "BeforeTool"}
    out = {}
    for event, kind, script, timeout, name in HOOKS:
        group = {"hooks": [{"type": "command", "name": name, "command": hook_cmd(script, "gemini", kit)}]}
        if kind == "shell":
            group = {"matcher": "run_shell_command", **group}
        elif kind == "figma":
            group = {"matcher": ".*[Ff]igma.*", **group}
        elif kind == "read":
            group = {"matcher": "read_file|read_many_files|run_shell_command", **group}
        out.setdefault(ev[event], []).append(group)
    return {"hooks": out}


def hooks_cursor(kit=None):
    kit = kit or KIT
    ev = {"SessionStart": "sessionStart", "UserPromptSubmit": "beforeSubmitPrompt", "SessionEnd": "sessionEnd",
          "PreCompact": "preCompact"}
    out = {}
    for event, kind, script, timeout, name in HOOKS:
        keys = {"shell": ["beforeShellExecution"], "figma": ["beforeMCPExecution"],
                "read": ["beforeReadFile", "beforeShellExecution"]}.get(kind) or [ev[event]]
        for key in keys:
            out.setdefault(key, []).append({"command": hook_cmd(script, "cursor", kit)})
    return {"version": 1, "hooks": out}


def hooks_kimi_toml(kit=None):
    kit = kit or KIT
    lines = ["# Eden hooks for Kimi Code — append to ~/.kimi-code/config.toml"]
    for event, kind, script, timeout, name in HOOKS:
        lines += ["", "[[hooks]]", f"# {name}", f"event = {json.dumps(event)}"]
        if kind:
            lines.append(f"matcher = {json.dumps({'shell': 'Bash', 'figma': '.*[Ff]igma.*', 'read': 'Read|Bash'}[kind])}")
        lines += [f"command = {json.dumps(hook_cmd(script, 'kimi', kit))}", f"timeout = {timeout}"]
    return "\n".join(lines) + "\n"


def opencode_plugin(kit=None):
    """OpenCode v2 plugin (verified against OpenCode 2.2.6: a `.js` file in ~/.config/opencode/plugins with a
    default export `{ id, setup(ctx) }` is loaded; the v1 named-export form is rejected)."""
    kit = kit or KIT
    guard, figma = (kit / "hooks" / "eden_guard.py").as_posix(), (kit / "hooks" / "eden_figma_guard.py").as_posix()
    secrets = (kit / "hooks" / "eden_secret_guard.py").as_posix()
    brain = (kit / "hooks" / "eden_brain.py").as_posix()
    rules = (kit.parent / "EDEN.md").as_posix()
    sessions = (kit.parent / "opencode-sessions").as_posix()
    return f"""// Eden for OpenCode v2 — generated by eden_port.py; do not edit (re-run `hosts install opencode`).
// eden-load-rules: adds the kit's rules digest (EDEN.md) to every model call of the agent loop.
// eden-commit-guard: blocks commits / pushes carrying a secret or an AI signature.
// eden-secrets-readonly: blocks reading .env, private keys and credential files.
// eden-figma-readonly: blocks Figma writes. A blocked call throws, which OpenCode reports to the model.
// eden-brain-recall / eden-brain-learn-on-exit: the same brain as every other tool — what it knows is added
// at start; when a session goes idle its dialogue is saved as JSONL ({{role, content}}) and queued with
// eden_brain.py learn, which distils it with the provider set in ~/.claude/eden-config.json.
import {{ spawn, spawnSync }} from "node:child_process";
import {{ mkdirSync, readFileSync, writeFileSync }} from "node:fs";

const PY = process.platform === "win32" ? "python" : "python3";
const GUARD = {json.dumps(guard)};
const FIGMA = {json.dumps(figma)};
const SECRETS = {json.dumps(secrets)};
const RULES = {json.dumps(rules)};
const BRAIN = {json.dumps(brain)};
const SESSIONS = {json.dumps(sessions)};

function brainRecall(cwd) {{
  const r = spawnSync(PY, ["-I", BRAIN, "start", "--host", "opencode"],
    {{ input: JSON.stringify({{ hook_event_name: "SessionStart", cwd }}), encoding: "utf8", timeout: 15000 }});
  try {{
    const out = JSON.parse(r.stdout || "{{}}");
    return (out.hookSpecificOutput && out.hookSpecificOutput.additionalContext) || out.additional_context || "";
  }} catch {{ return ""; }}
}}

// One message, whatever the SDK shape: {{role, content}}, {{info: {{role}}, parts: [{{type: "text", text}}]}}, …
export function toLine(m) {{
  const role = (m && (m.role || (m.info && m.info.role))) || "";
  if (role !== "user" && role !== "assistant") return null;
  if (typeof m.content === "string") return m.content.trim() ? JSON.stringify({{ role, content: m.content.trim() }}) : null;
  const parts = m.parts || (Array.isArray(m.content) ? m.content : []);
  const blocks = [];
  for (const p of parts) {{
    if (!p || p.synthetic) continue;
    if (p.type === "tool" || p.type === "tool_use" || p.type === "tool-invocation") {{
      // tool calls count for the brain's "real work happened" threshold; their input is a short hint
      const input = (p.state && p.state.input) || p.input || p.args || {{}};
      blocks.push({{ type: "tool_use", name: p.tool || p.name || "tool", input }});
    }} else if (typeof p.text === "string" && p.text.trim()) {{
      blocks.push({{ type: "text", text: p.text.trim() }});
    }}
  }}
  if (!blocks.length) return null;
  const onlyText = blocks.every((b) => b.type === "text");
  return JSON.stringify({{ role, content: onlyText ? blocks.map((b) => b.text).join("\\n") : blocks }});
}}

export function saveSession(sessionID, messages, dir = SESSIONS) {{
  mkdirSync(dir, {{ recursive: true }});
  const file = `${{dir}}/${{String(sessionID).replace(/[^A-Za-z0-9_.-]/g, "_")}}.jsonl`;
  writeFileSync(file, (messages || []).map(toLine).filter(Boolean).join("\\n") + "\\n", "utf8");
  return file;
}}

export function queueLearning(sessionID, transcript, cwd) {{
  const child = spawn(PY, ["-I", BRAIN, "learn", "--host", "opencode"], {{ detached: true, stdio: ["pipe", "ignore", "ignore"], windowsHide: true }});
  child.stdin.end(JSON.stringify({{ hook_event_name: "SessionEnd", session_id: String(sessionID), transcript_path: transcript, cwd }}));
  child.unref();
}}

export function check(script, payload) {{
  const r = spawnSync(PY, ["-I", script, "--host", "opencode"], {{ input: JSON.stringify(payload), encoding: "utf8" }});
  if (r.status === 2) return (r.stderr || "").trim() || "Blocked by Eden";
  try {{
    const out = JSON.parse(r.stdout || "{{}}");
    if (out.decision === "deny") return out.reason || "Blocked by Eden";
  }} catch {{}}
  return null;
}}

export default {{
  id: "eden",
  async setup(ctx) {{
    const cwd = (ctx.location && ctx.location.directory) || process.cwd();
    let rules = "";
    try {{ rules = readFileSync(RULES, "utf8"); }} catch {{}}
    const recall = brainRecall(cwd);
    const context = [rules, recall].filter(Boolean).join("\\n\\n");
    if (context) {{
      await ctx.session.hook("context", (event) => {{ event.system.push({{ type: "text", text: context }}); }});
    }}
    // Learning: when a session goes idle, save its dialogue and queue it for the shared brain.
    const controller = new AbortController();
    (async () => {{
      try {{
        for await (const event of ctx.event.subscribe({{ signal: controller.signal }})) {{
          if (!event || event.type !== "session.idle") continue;
          const sessionID = event.sessionID || (event.properties && event.properties.sessionID);
          if (!sessionID || !ctx.session.context) continue;
          const res = await ctx.session.context({{ sessionID }});
          const messages = Array.isArray(res) ? res : (res && (res.messages || res.data)) || [];
          if (messages.length) queueLearning(sessionID, saveSession(sessionID, messages), cwd);
        }}
      }} catch {{}}  // the brain must never break a session
    }})();
    await ctx.tool.hook("execute.before", (event) => {{
      const tool = String(event.tool || "");
      const scripts = [];
      if (/^(bash|shell)$/i.test(tool)) scripts.push(GUARD);
      if (/^(read|bash|shell|grep)$/i.test(tool)) scripts.push(SECRETS);
      if (/figma/i.test(tool)) scripts.push(FIGMA);
      for (const s of scripts) {{
        const reason = check(s, {{ hook_event_name: "PreToolUse", tool_name: tool, tool_input: event.input || {{}}, cwd }});
        if (reason) throw new Error(reason);
      }}
    }});
    return () => controller.abort();
  }},
}};
"""


def eden_md(host, kit=None):
    kit = kit or KIT
    digest = (kit / "rules" / "DIGEST.md") if (kit / "rules" / "DIGEST.md").exists() else ROOT / "rules" / "DIGEST.md"
    text = adapt_text(digest.read_text(encoding="utf-8"), kit)
    invoke = INVOKE.get(host, INVOKE["universal"]).replace("x", "{skill}")
    return (f"# Eden {(ROOT / 'VERSION').read_text().strip()} — reglas del kit\n\n"
            f"Los skills de Eden se llaman `eden-{{skill}}` (en esta herramienta: {invoke}). Sus agentes, "
            f"`eden-{{rol}}`. Reglas completas: `{(kit / 'rules').as_posix()}/` — léelas con la herramienta de "
            "lectura antes de actuar en su terreno.\n\n" + text)


# ---------------------------------------------------------------- plan: every file an install writes

def plan_kit(with_skills=True):
    """(dest, content | Path to copy) for the shared kit and, when a host needs them, the shared skills."""
    out = []
    for d in KIT_DIRS:
        for f in sorted((ROOT / d).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                rel = f.relative_to(ROOT)
                out.append((KIT / rel, adapt_text(f.read_text(encoding="utf-8")) if f.suffix in TEXT else f))
    for name in KIT_FILES:
        if (ROOT / name).is_file():
            out.append((KIT / name, adapt_text((ROOT / name).read_text(encoding="utf-8"))))
    for sk in skills() if with_skills else []:
        dest = SKILLS / f"eden-{sk.name}"
        for f in sorted(sk.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(sk)
            if f.suffix in TEXT:
                text = adapt_text(f.read_text(encoding="utf-8"), KIT, dest)
                if rel.as_posix() == "SKILL.md":
                    text = re.sub(r"^name:\s*.+$", f"name: eden-{sk.name}", text, count=1, flags=re.M)
                out.append((dest / rel, text))
            else:
                out.append((dest / rel, f))
    out.append((EDEN / "EDEN.md", eden_md("universal")))
    return out


def plan_host(host, ai=None):
    """(dest, content) for one tool, plus merges [(file, fn(data) → data)] and notes."""
    files, merges, notes = [], [], []
    version = (ROOT / "VERSION").read_text().strip()
    manifest = {"name": "eden", "version": version,
                "description": "Eden development kit: plan-first workflow, reuse-first building, stack teams, "
                               "security guard and self-learning brain."}
    ags = agents()
    if host == "codex":
        base = HOME / ".codex"
        files += [(base / "agents" / fn, c) for fn, c in (agent_file("codex", *a, ai=ai) for a in ags)]
        notes.append("Codex carga el plugin de Claude de forma nativa (skills y hooks): si no lo tienes, "
                     "`codex plugin marketplace add https://github.com/bandann/eden-dev-system.git` y "
                     "`codex plugin add eden@eden-kit`. Después confía en sus hooks con `/hooks` dentro de Codex: "
                     "sin eso, el guard de secretos no corre (o usa `/eden:setup githooks`).")
    elif host == "cursor":
        base = HOME / ".cursor" / "plugins" / "local" / "eden"
        files.append((base / ".cursor-plugin" / "plugin.json", json.dumps({**manifest, "displayName": "Eden"}, indent=2)))
        files += [(base / "agents" / fn, c) for fn, c in (agent_file("cursor", *a, ai=ai) for a in ags)]
        files.append((base / "hooks" / "hooks.json", json.dumps(hooks_cursor(), indent=2)))
    elif host == "gemini":
        base = HOME / ".gemini" / "extensions" / "eden"
        files.append((base / "gemini-extension.json", json.dumps({**manifest, "contextFileName": "EDEN.md"}, indent=2)))
        files.append((base / "EDEN.md", eden_md("gemini")))
        files += [(base / "agents" / fn, c) for fn, c in (agent_file("gemini", *a, ai=ai) for a in ags)]
        files.append((base / "hooks" / "hooks.json", json.dumps(hooks_gemini(), indent=2)))
        for sk in skills():
            meta = parse_frontmatter(split_frontmatter((sk / "SKILL.md").read_text(encoding="utf-8"))[0])
            desc = adapt_text(meta.get("description", ""))[:300]
            prompt = (f"Usa el skill `eden-{sk.name}` de Eden (está en {(SKILLS / ('eden-' + sk.name)).as_posix()}/SKILL.md: "
                      "léelo y síguelo). Argumentos del dev: {{args}}")
            files.append((base / "commands" / "eden" / f"{sk.name}.toml",
                          f"description = {json.dumps(desc, ensure_ascii=False)}\nprompt = {json.dumps(prompt, ensure_ascii=False)}\n"))
        notes.append("Antigravity (`agy`): impórtala con `agy plugin import gemini` tras instalar.")
    elif host == "opencode":
        base = HOME / ".config" / "opencode"
        files += [(base / "agents" / fn, c) for fn, c in (agent_file("opencode", *a, ai=ai) for a in ags)]
        files.append((base / "plugins" / "eden.js", opencode_plugin()))
        notes.append("OpenCode: el plugin eden.js carga las reglas (EDEN.md) y los dos guards; no hace falta tocar "
                     "opencode.json. Reinicia OpenCode (o su servicio: `opencode service`) para que lo cargue.")
    elif host == "kimi":
        base = EDEN / "hosts" / "kimi"
        files.append((base / "kimi.plugin.json", json.dumps({**manifest, "agents": "./agents"}, indent=2)))
        files += [(base / "agents" / fn, c) for fn, c in (agent_file("kimi", *a, ai=ai) for a in ags)]
        files.append((base / "hooks.toml", hooks_kimi_toml()))
        notes.append(f"Kimi Code: instala el plugin de {base.as_posix()} con el comando de plugins de Kimi y "
                     f"añade {(base / 'hooks.toml').as_posix()} a ~/.kimi-code/config.toml (Eden no toca esa config). "
                     "Sin verificar en Kimi: si no aparecen los skills, enlaza ~/.agents/skills en ~/.kimi-code/skills; "
                     "si no aparecen los agentes, Kimi solo los carga con `--agent-file`.")
    elif host == "universal":
        notes.append(f"Cualquier herramienta que lea AGENTS.md (Crush, Aider…): enlaza {(EDEN / 'EDEN.md').as_posix()} "
                     "desde tu AGENTS.md. Sin hooks: instala `/eden-setup githooks` en cada repo para el guard.")
    else:
        raise SystemExit(f"Herramienta desconocida: {host}. Opciones: {', '.join(HOSTS)}")
    return files, merges, notes


def merge_hooks(data, ours):
    """Eden's hooks into an existing Claude-format hooks.json, replacing older Eden entries."""
    data = json.loads(json.dumps(data or {}))
    hooks = data.setdefault("hooks", {})
    for event, groups in list(hooks.items()):
        kept = [{**g, "hooks": [h for h in g.get("hooks", []) if "eden_" not in h.get("command", "")]} for g in groups]
        hooks[event] = [g for g in kept if g["hooks"]]
    for event, groups in ours["hooks"].items():
        hooks.setdefault(event, []).extend(groups)
    data["hooks"] = {k: v for k, v in hooks.items() if v}
    return data


# ---------------------------------------------------------------- apply / record

def load_record():
    try:
        return json.loads(RECORD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"hosts": {}, "kit": []}


def save_record(rec):
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(rec, indent=1), encoding="utf-8")


def write(dest, content):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, Path):
        shutil.copy2(content, dest)
    else:
        dest.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8", newline="\n")


def backup(path):
    if path.exists():
        dest = EDEN / "backups" / STAMP / path.relative_to(HOME)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        return dest
    return None


def detect():
    found = {}
    for host, exes in CLIS.items():
        exe = next((x for x in (eden_ai.find_cli(e) for e in exes) if x), None)
        d = HOST_DIRS.get(host)
        found[host] = {"cli": exe, "dir": bool(d and d.is_dir())}
    return found


def _version_key(v):
    """Semver order, prereleases first: 3.17.0 < 4.0.0-beta.1 < 4.0.0-beta.2 < 4.0.0."""
    core, _, pre = (v or "0").partition("-")
    nums = tuple(int(x) if x.isdigit() else 0 for x in core.split("."))
    nums += (0,) * (3 - len(nums))
    pre_key = tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.-]", pre)) if pre else ()
    return nums + ((0,) + pre_key if pre else (1,))


def native_state(host):
    """For tools that load the Claude plugin themselves: (installed version or None, warnings)."""
    current = (ROOT / "VERSION").read_text().strip()
    warn, ver = [], None
    if host == "codex":
        cache = HOME / ".codex" / "plugins" / "cache" / "eden-kit" / "eden"
        vers = sorted((p.name for p in cache.iterdir() if p.is_dir()), key=_version_key) if cache.is_dir() else []
        ver = vers[-1] if vers else None
        if ver:
            try:
                cfg = (HOME / ".codex" / "config.toml").read_text(encoding="utf-8")
            except OSError:
                cfg = ""
            # Codex records trusted hooks as [hooks.state."<id>"] trusted_hash = "sha256:…"; none naming
            # Eden means its hooks never run (verified with Codex 0.167).
            if not re.search(r'\[hooks\.state\.[^\]]*eden', cfg, re.I):
                warn.append("sus hooks no tienen tu confianza, así que no corren: abre Codex y usa `/hooks` "
                            "(o protege cada repo con `/eden:setup githooks`)")
    elif host == "qwen":
        man = HOME / ".qwen" / "extensions" / "eden" / "qwen-extension.json"
        try:
            ver = json.loads(man.read_text(encoding="utf-8")).get("version")
        except (OSError, ValueError):
            ver = None
    if ver and _version_key(ver) < _version_key(current):
        how = {"codex": "`codex plugin marketplace upgrade` (trae lo que haya en la rama principal del repo)",
               "qwen": "`qwen extensions uninstall eden` y `qwen extensions install <carpeta>/plugins/eden` "
                       "(`update` no ve los cambios de un origen local)"}.get(host, "reinstálalo")
        warn.insert(0, f"tiene Eden {ver} y el plugin va en {current}: actualízalo con {how}")
    return ver, warn


def cmd_detect():
    found = detect()
    rec = load_record()
    for host, st in found.items():
        nat_ver, warns = native_state(host) if host in ("codex", "qwen") else (None, [])
        if host in NATIVE or (host == "codex" and nat_ver):
            state = f"nativo{f' {nat_ver}' if nat_ver else ''}" + (" + agentes" if host in rec["hosts"] else "")
        else:
            state = "instalado" if host in rec["hosts"] else ("universal" if host == "crush" else "sin instalar")
        seen = st["cli"] or ("config en " + str(HOST_DIRS[host]) if st["dir"] else "")
        if seen:
            say(f"  {host:<9} Eden: {state:<22} {seen}")
            for w in warns:
                say(f"            ⚠️ {w}")
    say("Instalar para una: `install <herramienta>` (en seco) · todas las detectadas: `install --detected`.")


def targets():
    skip = {sys.argv[sys.argv.index("--out") + 1]} if "--out" in sys.argv[:-1] else set()
    hosts = [a for a in sys.argv[2:] if not a.startswith("--") and a not in skip]
    if "--detected" in sys.argv:
        found = detect()
        hosts += [h for h in HOSTS if h in found and (found[h]["cli"] or found[h]["dir"])]
    return list(dict.fromkeys(hosts))


def sha(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def ownership(path, rec):
    """ours (written by Eden, untouched) · edited (Eden's, changed since) · foreign (not Eden's) · absent."""
    current = sha(path)
    if current is None:
        return "absent"
    recorded = rec.get("hashes", {}).get(str(path))
    if recorded is None:
        return "foreign"
    return "ours" if recorded == current else "edited"


def safe_write(dest, content, rec, report):
    """Write one file Eden owns. A foreign file is backed up first (and restored on uninstall); a file of
    Eden's that the dev edited is backed up before it is replaced. Records the new hash."""
    state = ownership(dest, rec)
    if state in ("foreign", "edited"):
        b = backup(dest)
        if state == "foreign":
            rec.setdefault("preexisting", {})[str(dest)] = str(b)
        report.append(("existía" if state == "foreign" else "lo modificaste") + f": {dest} → respaldo en {b}")
    write(dest, content)
    rec.setdefault("hashes", {})[str(dest)] = sha(dest)


def safe_remove(path, rec, report):
    """Remove a file only if it is Eden's and untouched; an edited one stays, and the dev is told."""
    state = ownership(path, rec)
    if state == "ours":
        Path(path).unlink(missing_ok=True)
    elif state == "edited":
        report.append(f"lo modificaste, así que no lo borro: {path}")
    rec.get("hashes", {}).pop(str(path), None)
    pre = rec.get("preexisting", {}).pop(str(path), None)
    if pre and Path(pre).exists() and not Path(path).exists():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pre, path)
        report.append(f"restaurado el que tenías: {path}")


def cmd_install(hosts=None):
    hosts = hosts if hosts is not None else targets()
    if not hosts:
        return say(f"¿Para qué herramienta? Opciones: {', '.join(HOSTS)} (o --detected). "
                   f"{', '.join(NATIVE)} cargan el plugin tal cual.")
    for h in hosts:
        if h in NATIVE:
            say(f"{h}: carga el plugin de Claude tal cual — no hace falta instalar nada.")
    hosts = [h for h in hosts if h not in NATIVE]
    rec = load_record()
    need_skills = any(h in SHARED_SKILLS for h in [*hosts, *rec["hosts"]])
    kit = plan_kit(with_skills=need_skills)
    say(f"{'APLICADO' if APPLY else 'haría'}: kit compartido en {KIT} ({len(kit)} archivos"
        + (f", incluye {len(skills())} skills en {SKILLS.as_posix()}/eden-*" if need_skills else ", sin skills compartidos")
        + f" y {(EDEN / 'EDEN.md').as_posix()})")
    plans = {h: plan_host(h) for h in hosts}
    clashes = [str(d) for d, _ in kit + [f for fs, _, _ in plans.values() for f in fs]
               if ownership(d, rec) in ("foreign", "edited")]
    for h, (files, merges, notes) in plans.items():
        say(f"{'APLICADO' if APPLY else 'haría'}: {h} — {len(files)} archivos"
            + "".join(f"; fusionar en {m[0]} (respaldo antes)" for m in merges))
        for d in sorted({str(f[0].parent) for f in files})[:6]:
            say(f"    {d}")
    if clashes:
        say(f"  ⚠️ {len(clashes)} archivo(s) que no son de Eden o que modificaste se respaldan antes de reemplazarlos"
            + "".join(f"\n    {c}" for c in clashes[:8]))
    if not APPLY or sys.argv[1] == "plan":
        say("(nada escrito: vuelve a correr `install` con --apply tras el sí del dev)")
        return
    report = []
    new_kit = {str(d) for d, _ in kit}
    for old in rec.get("kit", []):
        if old not in new_kit:
            safe_remove(old, rec, report)
    for dest, content in kit:
        safe_write(dest, content, rec, report)
    rec["kit"] = sorted(new_kit)
    rec["version"] = (ROOT / "VERSION").read_text().strip()
    for h, (files, merges, notes) in plans.items():
        new_files = {str(d) for d, _ in files}
        for old in rec["hosts"].get(h, {}).get("files", []):
            if old not in new_files:
                safe_remove(old, rec, report)
        for dest, content in files:
            safe_write(dest, content, rec, report)
        merged = []
        for path, fn in merges:
            b = backup(path)
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            write(path, json.dumps(fn(data), indent=2))
            merged.append({"file": str(path), "backup": str(b) if b else None})
        rec["hosts"][h] = {"files": sorted(new_files), "merged": merged, "at": STAMP, "version": rec["version"]}
        for n in notes:
            say(f"  → {n}")
    save_record(rec)
    for line in report:
        say(f"  · {line}")
    say(f"Listo. Registro en {RECORD}. Para quitarlo: `uninstall {' '.join(hosts)}`.")


def _prune_empty(root):
    root = Path(root)
    if not root.is_dir():
        return
    for sub in sorted(root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if sub.is_dir() and not any(sub.iterdir()):
            sub.rmdir()
    if not any(root.iterdir()):
        root.rmdir()


def cmd_uninstall():
    rec = load_record()
    hosts = [h for h in targets() if h in rec["hosts"]] or (list(rec["hosts"]) if "--all" in sys.argv else [])
    if not hosts:
        return say("No hay nada instalado para esas herramientas (ver `detect`).")
    report = []
    for h in hosts:
        entry = rec["hosts"][h]
        edited = [f for f in entry["files"] if ownership(f, rec) == "edited"]
        say(f"{'QUITADO' if APPLY else 'quitaría'}: {h} — {len(entry['files'])} archivos"
            + "".join(f"; Eden sale de {m['file']}" for m in entry.get("merged", []))
            + (f"; {len(edited)} que modificaste se conservan" if edited else ""))
        if APPLY:
            for f in entry["files"]:
                safe_remove(f, rec, report)
            for m in entry.get("merged", []):
                p = Path(m["file"])
                if p.exists():
                    data = merge_hooks(json.loads(p.read_text(encoding="utf-8")), {"hooks": {}})
                    write(p, json.dumps(data, indent=2))
            del rec["hosts"][h]
    if APPLY and not rec["hosts"]:
        say(f"QUITADO: kit compartido ({KIT}) y skills eden-* (ya no lo usa ninguna herramienta)")
        for f in rec.get("kit", []):
            safe_remove(f, rec, report)
        for d in [KIT, *SKILLS.glob("eden-*")]:
            _prune_empty(d)
        if (EDEN / "EDEN.md").exists() and ownership(EDEN / "EDEN.md", rec) != "edited":
            (EDEN / "EDEN.md").unlink(missing_ok=True)
        rec["kit"] = []
    if APPLY:
        save_record(rec)
        for line in report:
            say(f"  · {line}")
    else:
        say("(nada tocado: vuelve a correr con --apply tras el sí del dev)")


def cmd_doctor():
    """Is everything Eden installed still there, untouched and current? Changes nothing."""
    rec = load_record()
    current = (ROOT / "VERSION").read_text().strip()
    problems = 0
    py = shutil.which("python")
    say(f"python (los hooks lo llaman así): {py or 'NO ENCONTRADO — los hooks no correrán; ver Requisitos en el README'}")
    problems += not py
    if rec.get("kit"):
        states = [ownership(f, rec) for f in rec["kit"]]
        missing, edited = states.count("absent"), states.count("edited")
        stale = _version_key(rec.get("version")) < _version_key(current)
        say(f"kit compartido {rec.get('version')} ({len(states)} archivos): "
            + ("al día" if not stale else f"VIEJO (el plugin va en {current}) → `sync --apply`")
            + (f" · {missing} faltan" if missing else "") + (f" · {edited} modificados" if edited else ""))
        problems += bool(missing or edited or stale)
        guard = KIT / "hooks" / "eden_guard.py"
        if guard.exists() and py:
            import subprocess
            r = subprocess.run([py, "-I", str(guard)], input='{"tool_input":{"command":"ls"}}', capture_output=True,
                               text=True, timeout=30)
            say("hooks del kit: " + ("corren" if r.returncode == 0 else "FALLAN: " + (r.stderr or "")[-200:]))
            problems += r.returncode != 0
    for h, entry in rec.get("hosts", {}).items():
        states = [ownership(f, rec) for f in entry["files"]]
        missing, edited = states.count("absent"), states.count("edited")
        say(f"{h}: {len(states)} archivos"
            + (" · todo en su sitio" if not (missing or edited) else "")
            + (f" · {missing} faltan → `sync --apply`" if missing else "")
            + (f" · {edited} modificados por ti (se respaldan al actualizar)" if edited else ""))
        problems += bool(missing)
    for h in ("codex", "qwen"):
        ver, warns = native_state(h)
        if ver:
            say(f"{h} (nativo {ver}): " + ("; ".join(warns) if warns else "al día"))
            problems += bool(warns)
    if not rec.get("kit") and not rec.get("hosts"):
        say("No hay paquetes de Eden instalados con `hosts install` (los nativos se revisan arriba).")
    say("Sin problemas." if not problems else f"{problems} cosa(s) por revisar.")


def cmd_sync():
    """After a plugin update: reinstall every recorded tool from the current plugin (dry run first)."""
    hosts = list(load_record().get("hosts", {}))
    if not hosts:
        return say("No hay herramientas instaladas con `hosts install`: nada que sincronizar.")
    say(f"Sincronizando con el plugin {(ROOT / 'VERSION').read_text().strip()}: {', '.join(hosts)}")
    cmd_install(hosts)


def cmd_build():
    """One tool's package (kit included) under --out, with paths pointing there. Touches nothing else."""
    global KIT, SKILLS, EDEN, HOME
    if "--out" not in sys.argv[:-1]:
        return say("Uso: build <herramienta> --out DIR")
    out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    hosts = targets() or ["universal"]
    real_home = HOME
    HOME, EDEN = out, out / ".eden"
    KIT, SKILLS = EDEN / "kit", out / ".agents" / "skills"
    _rebase(real_home, out)
    n = 0
    for dest, content in plan_kit():
        write(dest, content)
        n += 1
    for h in hosts:
        files, merges, notes = plan_host(h)
        for dest, content in files:
            write(dest, content)
            n += 1
        for path, fn in merges:
            write(path, json.dumps(fn({}), indent=2))
            n += 1
    say(f"{n} archivos en {out} ({', '.join(hosts)})")


def _rebase(old_home, new_home):
    for k, v in list(HOST_DIRS.items()):
        HOST_DIRS[k] = new_home / v.relative_to(old_home)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "detect"
    {"detect": cmd_detect, "plan": cmd_install, "install": cmd_install, "uninstall": cmd_uninstall,
     "build": cmd_build, "doctor": cmd_doctor, "sync": cmd_sync}.get(cmd, cmd_detect)()


if __name__ == "__main__":
    main()
