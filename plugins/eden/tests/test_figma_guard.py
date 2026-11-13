import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
GUARD = HOOKS / "eden_figma_guard.py"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def run(tool, tool_input=None, cwd=None):
    payload = {"tool_name": tool, "tool_input": tool_input or {}, "cwd": cwd or tempfile.gettempdir()}
    out = subprocess.run([sys.executable, "-I", str(GUARD)], input=json.dumps(payload), text=True,
                         encoding="utf-8", capture_output=True).stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out else None


C = "mcp__figma-console__"
# --- reads pass
for t in ("figma_get_status", "figma_get_component_for_development_deep", "figma_get_variables",
          "figma_capture_screenshot", "figma_navigate", "figma_get_file_data", "figma_search_components",
          "figma_diff_versions", "figma_lint_design", "figjam_get_board_contents", "figma_list_open_files"):
    check(f"read allowed: {t}", run(C + t) is None)
for t in ("get_design_context", "get_metadata", "get_screenshot", "whoami"):
    check(f"official read allowed: {t}", run("mcp__claude_ai_Figma__" + t) is None)

# --- writes blocked
for t in ("figma_set_fills", "figma_set_text", "figma_create_child", "figma_delete_node", "figma_rename_node",
          "figma_post_comment", "figma_update_variable", "figma_batch_create_variables", "figma_move_node",
          "figma_clone_node", "figma_import_tokens", "figma_setup_design_tokens", "figjam_create_sticky",
          "figma_some_future_tool"):
    check(f"write blocked: {t}", run(C + t) is not None)
for t in ("add_code_connect_map", "send_code_connect_mappings"):
    check(f"official write blocked: {t}", run("mcp__plugin_figma_figma__" + t) is not None)
check("non-figma tool ignored", run("mcp__context7__query-docs") is None and run("Bash", {"command": "ls"}) is None)

# --- figma_execute
fp = subprocess.run([sys.executable, "-I", str(HOOKS / "eden_design.py"), "fingerprint-js", "1:2"],
                    capture_output=True, text=True, encoding="utf-8").stdout
check("fingerprint script allowed", run(C + "figma_execute", {"code": fp}) is None)
reads = [
    "const n = await figma.getNodeByIdAsync('1:2'); return { w: n.width, kids: n.children.map(k => k.name) };",
    "const out = []; for (const id of ['1:2']) { const f = await figma.getNodeByIdAsync(id); out.push({ id, h: f.height }); } return out;",
    "const x = node.name === 'a'; return x;",
    "const [first, second] = node.children; return { a: first.name, b: second.name };",
    "let [w, h] = [node.width, node.height]; return w * h;",
]
for i, code in enumerate(reads):
    check(f"read script {i} allowed", run(C + "figma_execute", {"code": code}) is None)
writes = {
    "create": "const r = figma.createRectangle(); return r.id;",
    "remove": "(await figma.getNodeByIdAsync('1:2')).remove();",
    "assign name": "const n = await figma.getNodeByIdAsync('1:2'); n.name = 'x';",
    "assign fills": "node.fills = [];",
    "compound assign": "node.x += 10;",
    "characters": "t.characters = 'hola';",
    "index assign": "node['fills'] = [];",
    "index assign var key": "const k = 'name'; node[k] = 'x';",
    "index compound": "node[\"x\"] += 5;",
    "computed call": "node['re' + 'move']();",
    "appendChild": "frame.appendChild(child);",
    "setProperties": "inst.setProperties({ a: 1 });",
    "variables": "figma.variables.createVariable('a', c, 'COLOR');",
    "setValueForMode": "v.setValueForMode(m, 1);",
    "loadFont": "await figma.loadFontAsync(f);",
    "Object.assign": "Object.assign(node, { name: 'x' });",
    "eval": "eval('node.remove()');",
    "new Function": "new Function('n', 'n.remove()')(node);",
    "group": "figma.group([a, b], p);",
    "hidden after url": "const u = 'https://x'; node.name = 'y';",
    "after comment": "// read only\nnode.visible = false;",
    "resize": "node.resize(10, 10);",
    "pluginData": "node.setPluginData('k', 'v');",
}
for name, code in writes.items():
    check(f"write script blocked: {name}", run(C + "figma_execute", {"code": code}) is not None)
check("across files also checked", run(C + "figma_execute_across_files", {"code": "node.name = 'x';"}) is not None)

# --- explicit project opt-in
proj = Path(tempfile.mkdtemp())
(proj / ".git").mkdir()
(proj / ".claude").mkdir()
cfg = proj / ".claude" / "project-config.json"
cfg.write_text('{"figma": {"allow_writes": false}}', encoding="utf-8")
check("allow_writes false still blocks", run(C + "figma_set_fills", cwd=str(proj)) is not None)
cfg.write_text('{"figma": {"allow_writes": true}}', encoding="utf-8")
check("allow_writes true lets writes through", run(C + "figma_set_fills", cwd=str(proj)) is None)
cfg.write_text('{"figma": {"allow_writes": "yes"}}', encoding="utf-8")
check("only literal true counts", run(C + "figma_set_fills", cwd=str(proj)) is not None)
cfg.write_text("{broken", encoding="utf-8")
check("broken config blocks", run(C + "figma_set_fills", cwd=str(proj)) is not None)

msg = run(C + "figma_set_fills")
check("message explains in Spanish", msg and "solo lectura" in msg)

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
