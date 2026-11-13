"""Eden ↔ UI/UX Pro Max — design direction when a task has no design, only with the dev's yes.

UI/UX Pro Max (https://github.com/nextlevelbuilder/ui-ux-pro-max-skill, MIT) is an external dependency:
Eden never ships or copies it. This script finds an installed copy, reports how to install it when there
is none, and runs its search tool — only when the call carries `--approved`, which the skill
`/eden:uiux-pro` adds after the dev said yes in the conversation. Nothing here ever runs on its own.

Usage: python -I eden_uiux.py <status | stack <eden-stack> [flavor] | run --approved [--save NAME] -- <args>>
  status   where UI/UX Pro Max is (or how to install it), its version, and the project's uiux.mode
  stack    the UI/UX Pro Max `--stack` for an Eden stack / flavour (empty = use the general UX rules)
  run      search.py with <args>; --save NAME also writes the output to .claude/context/uiux-<date>-NAME.md

Safety: `--persist`, `--force` and `--output-dir` are refused — UI/UX Pro Max never writes into the
project; what is kept goes to .claude/context/ (or, with another yes, through create-fundaments).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

SKILL = "ui-ux-pro-max"
CONFIG_DIRS = (".claude", ".agents", ".codex", ".cursor", ".gemini", ".qwen", ".kiro", ".windsurf", ".opencode",
               ".config/opencode", ".kimi-code", ".grok")
INSTALL = {
    "claude": ["/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill",
               "/plugin install ui-ux-pro-max@ui-ux-pro-max-skill"],
    "other": ["npm install -g ui-ux-pro-max-cli", "uipro init --ai <claude|cursor|codex|gemini|opencode|…>"],
}
REFUSED = ("--persist", "--force", "--output-dir", "-o")
# Eden stack / flavour → UI/UX Pro Max --stack. Liquid (Shopify) and WordPress themes have no stack of
# their own there: html-tailwind is the closest for plain HTML/CSS guidance; None = general UX rules only.
STACKS = {
    ("react", "next"): "nextjs", ("react", "spa"): "react", ("react", None): "react",
    ("php", "laravel"): "laravel", ("mobile", "react-native"): "react-native",
    ("shopify", None): "html-tailwind", ("wordpress", None): "html-tailwind", ("shopify-app", None): "react",
}


def candidates(project=None, home=None):
    home = Path(home or Path.home())
    roots = [home] + ([Path(project)] if project else [])
    out = []
    for root in roots:
        for d in CONFIG_DIRS:
            out.append(root / d / "skills" / SKILL / "scripts" / "search.py")
    cache = home / ".claude" / "plugins" / "cache"
    if cache.is_dir():  # Claude Code plugin install: cache/<marketplace>/ui-ux-pro-max/<version>/…
        out += sorted(cache.glob(f"*/{SKILL}/*/.claude/skills/{SKILL}/scripts/search.py"))
    env = os.environ.get("EDEN_UIUX_PATH")
    if env:
        out.insert(0, Path(env))
    return out


def version_of(search_py):
    for up in list(Path(search_py).parents)[:6]:
        for f in (up / ".claude-plugin" / "plugin.json", up / "package.json"):
            try:
                return json.loads(f.read_text(encoding="utf-8")).get("version")
            except (OSError, ValueError):
                continue
    return None


def _vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.-]", v or "0"))


def locate(project=None, home=None):
    """The newest installed search.py, or None."""
    found = [p for p in candidates(project, home) if p.is_file()]
    if not found:
        return None
    return max(found, key=lambda p: (_vkey(version_of(p)), p.stat().st_mtime))


def mode(project):
    try:
        data = json.loads((Path(project) / ".claude" / "project-config.json").read_text(encoding="utf-8"))
        m = str((data.get("uiux") or {}).get("mode", "ask")).lower()
    except (OSError, ValueError, AttributeError):
        m = "ask"
    return m if m in ("ask", "off") else "ask"  # there is no automatic mode, by design


def stack_for(stack, flavor=None):
    return STACKS.get((stack, flavor)) or STACKS.get((stack, None)) or ""


def run(args, project, approved=False, save=None, search_py=None):
    """(exit code, output). Refuses without approval or with an option that would write to the project."""
    if not approved:
        return 2, ("No se ejecuta: UI/UX Pro Max solo corre después del sí del dev. Pregúntale primero "
                   "(bloque 🎨 de /eden:uiux-pro) y vuelve a llamar con --approved.")
    bad = [a for a in args if a.split("=", 1)[0] in REFUSED]
    if bad:
        return 2, f"No se permite {', '.join(bad)}: UI/UX Pro Max no escribe en el proyecto. Usa --save NAME."
    search_py = search_py or locate(project)
    if not search_py:
        return 3, "UI/UX Pro Max no está instalado. " + install_hint()
    # Not -I: the tool imports its sibling modules from its own folder. It is the dev's own install.
    r = subprocess.run([sys.executable, str(search_py), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(Path(search_py).parent), timeout=120,
                       creationflags=0x08000000 if os.name == "nt" else 0)
    out = (r.stdout or "") + (("\n" + r.stderr) if r.returncode and r.stderr else "")
    if r.returncode == 0 and save:
        ctx = Path(project) / ".claude" / "context"
        ctx.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^a-z0-9-]+", "-", save.lower()).strip("-") or "proposal"
        dest = ctx / f"uiux-{datetime.now():%Y-%m-%d}-{name}.md"
        dest.write_text(f"<!-- UI/UX Pro Max {version_of(search_py) or ''} · {' '.join(args)} -->\n\n{out}",
                        encoding="utf-8")
        out += f"\n\n(guardado en {dest.as_posix()})"
    return r.returncode, out


def install_hint():
    return ("En Claude Code: " + " · ".join(f"`{c}`" for c in INSTALL["claude"])
            + ". En otras herramientas: " + " · ".join(f"`{c}`" for c in INSTALL["other"])
            + ". Instalarlo lo decide el dev.")


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "status"
    project = os.getcwd()
    if cmd == "status":
        p = locate(project)
        print(f"UI/UX Pro Max: {p.as_posix() + ' (' + (version_of(p) or 'versión ?') + ')' if p else 'no instalado — ' + install_hint()}")
        print(f"uiux.mode de este proyecto: {mode(project)} (ask = se propone y se pregunta; off = nunca se propone)")
    elif cmd == "stack":
        print(stack_for(argv[1] if len(argv) > 1 else "", argv[2] if len(argv) > 2 else None))
    elif cmd == "run":
        rest = argv[1:]
        approved = "--approved" in rest
        save = rest[rest.index("--save") + 1] if "--save" in rest[:-1] else None
        tool_args = rest[rest.index("--") + 1:] if "--" in rest else []
        code, out = run(tool_args, project, approved=approved, save=save)
        print(out)
        sys.exit(code)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
