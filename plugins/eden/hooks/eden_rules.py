"""Eden rules — SessionStart hook that integrates the kit rules with the dev's global rules.

A plugin cannot ship always-on instructions, so this hook decides what the session needs:
  - The dev's own global rules (~/.claude/rules) are already loaded by Claude Code: they are detected,
    listed and declared to take priority over the kit.
  - If the full Eden rules are synced into ~/.claude/rules and identical to this plugin's, they are
    already in context: only a one-line note is added.
  - Otherwise the compact DIGEST (always under the 10,000-char cap) is injected, plus an index of the
    full rules inside the plugin to Read on demand, and how to sync them (/eden:setup rules).
Exits 0 and stays silent on any error: a broken hook must never break a session.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_host  # one hook contract for every host (see hooks/eden_host.py)

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or HERE.parent).resolve()
RULES = ROOT / "rules"
GLOBAL_RULES = Path.home() / ".claude" / "rules"
CAP = 9500  # stay under Claude Code's 10,000-char additionalContext cap


def norm(p):
    try:
        return p.read_text(encoding="utf-8").replace("\r\n", "\n").lstrip("﻿").strip()
    except OSError:
        return None


def plugin_version():
    try:
        return json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return "?"


def rules_index(pending, outdated=()):
    """Compact index of the full rules to Read: the base path once, the core by name, each stack with its
    flavours. A path per line (≈3.8 KB for 36 rules) pushed the digest past the context cap; this is ≈1 KB."""
    core, stacks = [], {}
    for rel in sorted(pending, key=lambda r: r.as_posix()):
        parts = rel.parts
        mark = " (desactualizada)" if rel in outdated else ""
        if len(parts) == 1:
            core.append(rel.stem + mark)
        else:
            entry = stacks.setdefault(parts[0], {"module": [], "flavors": []})
            (entry["flavors"] if "flavors" in parts else entry["module"]).append(rel.stem + mark)
    lines = [f"## Reglas completas a leer cuando toque (Read)\nBase: `{RULES.as_posix()}/` — `{{nombre}}.md`."]
    if core:
        lines.append("- Núcleo: " + ", ".join(core))
    for stack, e in stacks.items():
        flav = f" · sabores en `{stack}/flavors/`: " + ", ".join(e["flavors"]) if e["flavors"] else ""
        lines.append(f"- `{stack}/`: " + ", ".join(e["module"]) + flav)
    lines.append("Ninguna está en `~/.claude/rules`" if not outdated else
                 "Las demás no están en `~/.claude/rules`")
    lines[-1] += "; para tenerlas siempre activas: `/eden:setup rules` (con el sí del dev)."
    return "\n".join(lines)


def main():
    eden_host.read_payload()  # only to learn which host is asking; this hook needs nothing else
    if os.environ.get("EDEN_DISTILLER"):
        return
    # Git hooks installed by `/eden:setup githooks` find the plugin through this pointer; keep it on the
    # current version after an update. Only refreshed once the dev opted in (the file exists).
    pointer = Path.home() / ".claude" / "eden-cache" / "plugin_root"
    if pointer.exists() and norm(pointer) != ROOT.as_posix():
        pointer.write_text(ROOT.as_posix(), encoding="utf-8")
    # rules/on-demand/ is read only by the flows that need it: never indexed, never synced always-on.
    kit = sorted(p.relative_to(RULES) for p in RULES.rglob("*.md")
                 if p.name != "DIGEST.md" and "on-demand" not in p.relative_to(RULES).parts)
    synced, outdated, missing = [], [], []
    for rel in kit:
        theirs = norm(GLOBAL_RULES / rel)
        if theirs is None:
            missing.append(rel)
        elif theirs == norm(RULES / rel):
            synced.append(rel)
        else:
            outdated.append(rel)
    kit_names = {r.as_posix() for r in kit}
    own = sorted(p.relative_to(GLOBAL_RULES).as_posix() for p in GLOBAL_RULES.rglob("*.md")
                 if p.relative_to(GLOBAL_RULES).as_posix() not in kit_names) if GLOBAL_RULES.is_dir() else []

    root = ROOT.as_posix()
    out = [f"# Eden {plugin_version()} — reglas del kit",
           f"Las rutas `rules/…`, `teams/…`, `skills/…`, `hooks/…`, `config/…`, `team/…`, `profiles/…` y "
           f"`brain/…` que citan los skills y agentes de Eden son relativas al plugin: `{root}`."]

    if own:
        out.append("## Reglas propias del dev (ya cargadas por Claude Code; mandan sobre las del kit)\n"
                   + ", ".join(f"`{n}`" for n in own)
                   + "\nSi una choca con una regla de Eden, gana la del dev; si la duda importa, se pregunta.")

    if not outdated and not missing:
        out.append(f"Las {len(synced)} reglas Eden completas están activas desde `~/.claude/rules` y al día "
                   "con el plugin: aplícalas tal cual.")
    else:
        if synced:
            out.append(f"{len(synced)} reglas Eden completas activas desde `~/.claude/rules`.")
        out.append(rules_index(outdated + missing, outdated))
        digest = norm(RULES / "DIGEST.md") or ""
        room = CAP - len("\n\n".join(out)) - 4
        if room > 500:
            out.insert(2 if own else 1, digest if len(digest) <= room else digest[:room - 40] + "\n[… resumen truncado …]")

    context = "\n\n".join(out)
    eden_host.emit("SessionStart", context[:CAP])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
