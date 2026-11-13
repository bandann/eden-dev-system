import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "scripts" / "eden_port.py"
spec = importlib.util.spec_from_file_location("eden_port", SCRIPT)
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


# --- text transforms
kit = Path("/k/kit")
t = port.adapt_text('python -I "${CLAUDE_PLUGIN_ROOT}/scripts/x.py" · run `/eden:setup ai` · agent `eden:explorer` '
                    "and `eden:shopify-*` · arg: `$ARGUMENTS` · Autorizado en /eden: sí · eden-config.json", kit)
check("plugin root → kit", '"/k/kit/scripts/x.py"' in t and "CLAUDE_PLUGIN_ROOT" not in t)
check("/eden:x → /eden-x", "`/eden-setup ai`" in t)
check("eden:agent → eden-agent", "`eden-explorer`" in t and "`eden-shopify-*`" in t)
check("$ARGUMENTS → prose", "$ARGUMENTS" not in t and "lo que el dev escribió" in t)
check("lone '/eden: sí' and file names untouched", "/eden: sí" in t and "eden-config.json" in t)
check("skill dir var", port.adapt_text("${CLAUDE_SKILL_DIR}/a.py", kit, Path("/s/eden-x")) == "/s/eden-x/a.py")

# --- frontmatter
meta = port.parse_frontmatter("name: explorer\ndescription: >\n  line one\n  line two\ntools: Read, Grep\nmodel: sonnet")
check("folded description joined", meta["description"] == "line one line two" and meta["model"] == "sonnet")
check("read-only by tools", port.read_only({"tools": "Read, Grep, Glob, Bash"})
      and not port.read_only({"tools": "Read, Write, Edit"}) and not port.read_only({}))
check("read-only by disallowedTools", port.read_only({"tools": "Read, Write, Edit", "disallowedTools": "Write, Edit, NotebookEdit"}))

# --- agents in every format
ags = port.agents()
N = len(list((PLUGIN / "agents").glob("*.md")))
check("every agent read", len(ags) == N and all(m.get("description") for _, m, _ in ags))
for host in ("codex", "cursor", "gemini", "opencode", "kimi"):
    files = [port.agent_file(host, *a, ai={}) for a in ags]
    names = [fn for fn, _ in files]
    check(f"{host}: one file per agent, eden- prefixed", len(set(names)) == N and all(n.startswith("eden-") for n in names))
    if host == "codex":
        parsed = [tomllib.loads(c) for _, c in files]
        check("codex: every TOML parses, has instructions, no model field",
              all(p["name"].startswith("eden-") and p["developer_instructions"].strip() and "model" not in p for p in parsed))
    else:
        heads = [c.split("---")[1] for _, c in files]
        check(f"{host}: frontmatter with a description", all("description: \"" in h for h in heads))
        check(f"{host}: no Claude-only text left", not any("CLAUDE_PLUGIN_ROOT" in c or "/eden:" in c.replace("/eden: ", "")
                                                          for _, c in files))
cur = dict(port.agent_file("cursor", *a, ai={}) for a in ags)
check("cursor: read-only explorer, inherit model", "readonly: true" in cur["eden-explorer.md"] and "model: inherit" in cur["eden-explorer.md"])
oc = dict(port.agent_file("opencode", *a, ai={}) for a in ags)
check("opencode: subagent, edit denied for reviewers", "mode: subagent" in oc["eden-qa-reviewer.md"]
      and "edit: deny" in oc["eden-qa-reviewer.md"] and "edit: deny" not in oc["eden-implementer.md"])
check("kimi: no model field", all("model:" not in c.split("---")[1] for _, c in (port.agent_file("kimi", *a, ai={}) for a in ags)))
check("ai.tiers reaches the agent file", "model: deepseek/x" in port.agent_file(
    "opencode", *ags[0], ai={"tiers": {"opencode": {"fast": "deepseek/x"}}})[1])

# --- hook configs
g = port.hooks_gemini(kit)["hooks"]
check("gemini: secret guard on reads and shell", any(gr.get("matcher") == "read_file|read_many_files|run_shell_command"
                                                     for gr in g["BeforeTool"]))
check("gemini events", set(g) == {"SessionStart", "BeforeAgent", "SessionEnd", "PreCompress", "BeforeTool"}
      and g["BeforeTool"][0]["matcher"] == "run_shell_command")
c = port.hooks_cursor(kit)
check("cursor events", c["version"] == 1 and {"sessionStart", "beforeShellExecution", "beforeMCPExecution",
                                              "beforeReadFile", "beforeSubmitPrompt", "sessionEnd", "preCompact"} == set(c["hooks"]))
check("cursor: secret guard on file reads and shell", any("eden_secret_guard.py" in h["command"] for h in c["hooks"]["beforeReadFile"])
      and any("eden_secret_guard.py" in h["command"] for h in c["hooks"]["beforeShellExecution"]))
cx = port.hooks_claude_format("codex", kit)["hooks"]
check("codex: Claude format, --host, names", all("--host codex" in h["command"] and h["statusMessage"].startswith("eden-")
                                               for gs in cx.values() for gr in gs for h in gr["hooks"]))
check("every hook calls the kit", all("/k/kit/hooks/" in gr["hooks"][0]["command"] for gs in g.values() for gr in gs))
kt = tomllib.loads(port.hooks_kimi_toml(kit))
check("kimi hooks.toml parses", len(kt["hooks"]) == len(port.HOOKS) == 9 and kt["hooks"][5]["matcher"] == "Bash"
      and kt["hooks"][7]["matcher"] == "Read|Bash")
merged = port.merge_hooks({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "mine.sh"}]},
                                                    {"hooks": [{"command": "python old/eden_guard.py"}]}]}},
                          port.hooks_claude_format("codex", kit))
pre = [h["command"] for gr in merged["hooks"]["PreToolUse"] for h in gr["hooks"]]
check("merge keeps the dev's hook, replaces old Eden ones", "mine.sh" in pre and "python old/eden_guard.py" not in pre
      and sum("eden_guard.py" in x for x in pre) == 1)

# --- context files other tools truncate or misparse
for host in ("gemini", "universal", "opencode"):
    md = port.eden_md(host, kit)
    check(f"{host}: EDEN.md under Antigravity's 24 KB per-file cap (and a 20k-token budget)", len(md.encode("utf-8")) < 20000)
    check(f"{host}: EDEN.md code fences balanced (an open fence makes Gemini drop what follows)", md.count("```") % 2 == 0)

# --- install / uninstall for real, in a throwaway HOME
home = Path(tempfile.mkdtemp())
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
(home / ".codex").mkdir()
(home / ".codex" / "hooks.json").write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [{"command": "mine.sh"}]}]}}))


def run(*args):
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", env=env)


r = run("install", "codex", "gemini")
check("dry run writes nothing", "haría" in r.stdout and not (home / ".eden").exists() and not (home / ".agents").exists())
check("plan never writes, even with --apply", run("plan", "codex", "--apply").returncode == 0 and not (home / ".eden").exists())
r = run("install", "codex", "--apply")
check("codex install ok", r.returncode == 0 and "Listo" in r.stdout and "codex plugin add eden@eden-kit" in r.stdout)
check("codex: 55 agents, kit, no shared skills", len(list((home / ".codex/agents").glob("eden-*.toml"))) == N
      and (home / ".eden/kit/hooks/eden_guard.py").exists() and not list((home / ".agents/skills").glob("eden-*")))
check("codex: hooks.json untouched (the native plugin brings the hooks)",
      json.loads((home / ".codex/hooks.json").read_text()) == {"hooks": {"SessionStart": [{"hooks": [{"command": "mine.sh"}]}]}})
r = run("install", "gemini", "--apply")
check("gemini install adds the shared skills", (home / ".agents/skills/eden-setup/SKILL.md").exists() and (home / ".eden/EDEN.md").exists())
skill = (home / ".agents/skills/eden-setup/SKILL.md").read_text(encoding="utf-8")
check("installed skill renamed and points at the kit", "name: eden-setup" in skill
      and (home / ".eden/kit").as_posix() in skill and "CLAUDE_PLUGIN_ROOT" not in skill)
check("codex agents survive the second install", len(list((home / ".codex/agents").glob("eden-*.toml"))) == N)
ext = home / ".gemini/extensions/eden"
check("gemini extension", json.loads((ext / "gemini-extension.json").read_text())["contextFileName"] == "EDEN.md"
      and (ext / "commands/eden/setup.toml").exists() and len(list((ext / "agents").glob("*.md"))) == N)
res = subprocess.run(json.loads((ext / "hooks/hooks.json").read_text())["hooks"]["BeforeTool"][0]["hooks"][0]["command"],
                     shell=True, input=json.dumps({"hook_event_name": "BeforeTool", "tool_name": "run_shell_command",
                                                   "tool_input": {"command": "ls"}}), capture_output=True, text=True, env=env)
check("installed gemini hook runs from the kit", res.returncode == 0)
r = run("install", "opencode", "--apply")
plug = (home / ".config/opencode/plugins/eden.js").read_text(encoding="utf-8")
check("opencode: v2 plugin (default export with id + setup, tool and context hooks)",
      "export default {" in plug and 'id: "eden"' in plug and 'ctx.tool.hook("execute.before"' in plug
      and 'ctx.session.hook("context"' in plug and "tool.execute.before\": async (input" not in plug
      and "eden_secret_guard.py" in plug)
check("opencode: shares the brain (recall at start, learn on session.idle)", "eden_brain.py" in plug
      and '"start"' in plug and '"learn"' in plug and "session.idle" in plug and "tool_use" in plug)
r = run("uninstall", "codex", "--apply")
check("uninstall codex: agents gone, dev's hooks.json intact", not list((home / ".codex/agents").glob("eden-*"))
      and "mine.sh" in (home / ".codex/hooks.json").read_text())
check("kit stays while others use it", (home / ".eden/kit").exists() and (home / ".agents/skills/eden-setup").exists())
r = run("uninstall", "gemini", "opencode", "--apply")
check("last uninstall removes kit and skills", not (home / ".eden/kit").exists()
      and not list((home / ".agents/skills").glob("eden-*")) and not (ext / "gemini-extension.json").exists()
      and not (home / ".config/opencode/plugins/eden.js").exists())

# --- ownership by hash: never lose a file that is not Eden's or that the dev edited
oh = Path(tempfile.mkdtemp())
oenv = dict(os.environ, HOME=str(oh), USERPROFILE=str(oh))


def orun(*args):
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", env=oenv)


agent_dir = oh / ".config/opencode/agents"
agent_dir.mkdir(parents=True)
(agent_dir / "eden-explorer.md").write_text("MY OWN AGENT", encoding="utf-8")  # foreign file at a target path
r = orun("install", "opencode")
check("dry run warns about the foreign file", "respaldan" in r.stdout)
r = orun("install", "opencode", "--apply")
rec = json.loads((oh / ".eden/installed.json").read_text(encoding="utf-8"))
check("foreign file backed up before being replaced", "existía" in r.stdout
      and any(b.read_text(encoding="utf-8") == "MY OWN AGENT" for b in (oh / ".eden/backups").rglob("eden-explorer.md")))
check("every written file has a hash", all(rec["hashes"].get(f) for f in rec["hosts"]["opencode"]["files"]))
skill = oh / ".agents/skills/eden-setup/SKILL.md"
skill.write_text(skill.read_text(encoding="utf-8") + "\nmy note\n", encoding="utf-8")  # the dev edits Eden's file
d = orun("doctor")
check("doctor sees the edited file", "modificados" in d.stdout)
(oh / ".config/opencode/agents/eden-qa-reviewer.md").unlink()
d = orun("doctor")
check("doctor sees a missing file", "faltan" in d.stdout and "sync --apply" in d.stdout)
r = orun("sync", "--apply")
check("sync reinstalls the missing file", (oh / ".config/opencode/agents/eden-qa-reviewer.md").exists() and "Listo" in r.stdout)
check("…and backs up the dev's edit before replacing it", "lo modificaste" in r.stdout
      and any("my note" in b.read_text(encoding="utf-8") for b in (oh / ".eden/backups").rglob("SKILL.md")))
(oh / ".config/opencode/agents/eden-implementer.md").write_text("edited by me", encoding="utf-8")
r = orun("uninstall", "opencode", "--apply")
check("uninstall keeps a file the dev edited", (oh / ".config/opencode/agents/eden-implementer.md").read_text(encoding="utf-8")
      == "edited by me" and "no lo borro" in r.stdout)
check("uninstall restores the file that was there before", (agent_dir / "eden-explorer.md").read_text(encoding="utf-8")
      == "MY OWN AGENT" and "restaurado" in r.stdout)
check("Eden's untouched files are gone", not (oh / ".config/opencode/plugins/eden.js").exists()
      and not (oh / ".eden/kit/hooks/eden_guard.py").exists())

# --- native installs: stale version and untrusted Codex hooks are reported
nh = Path(tempfile.mkdtemp())
(nh / ".codex/plugins/cache/eden-kit/eden/3.11.0").mkdir(parents=True)
(nh / ".codex/config.toml").write_text('[plugins."eden@eden-kit"]\nenabled = true\n', encoding="utf-8")
(nh / ".qwen/extensions/eden").mkdir(parents=True)
(nh / ".qwen/extensions/eden/qwen-extension.json").write_text(json.dumps({"version": "3.11.0"}), encoding="utf-8")
port.HOME = nh
ver, warns = port.native_state("codex")
check("codex: old native version and untrusted hooks reported", ver == "3.11.0" and any("3.11.0" in w for w in warns)
      and any("/hooks" in w for w in warns))
(nh / ".codex/config.toml").write_text('[hooks.state."eden@eden-kit:pre_tool_use:0"]\ntrusted_hash = "sha256:x"\n',
                                       encoding="utf-8")
check("codex: trusted hooks not reported", not any("/hooks" in w for w in port.native_state("codex")[1]))
ver, warns = port.native_state("qwen")
check("qwen: old native version reported", ver == "3.11.0" and any("qwen extensions install" in w for w in warns))
check("version compare is numeric", port._version_key("3.16.0") > port._version_key("3.9.0"))
k = port._version_key
check("prereleases sort before their release", k("3.17.0") < k("4.0.0-beta.1") < k("4.0.0-beta.2") < k("4.0.0") < k("4.0.1"))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
