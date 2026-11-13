"""Eden setup — inspect and (only with --apply) prepare the dev's machine for the Eden plugin.

Usage: python -I eden_setup.py <status|rules|brain|config|migrate|ai|githooks|hosts> [--apply]
       githooks [--remove]   the secret / AI-signature guard as git hooks of the repo in the cwd
       hosts [detect | install <tool…> | uninstall <tool…> | doctor | sync]   Eden for Codex, Cursor, Gemini, OpenCode, Kimi…
       ai [detect | auto [--pick N] | set <provider> [--model M] [--key-env VAR] [--base-url URL]
          [--api anthropic|openai] | test]
Without --apply every command only reports what it would do. Everything it replaces is backed up
under ~/.claude/backups/ first; nothing is deleted outright.
"""
import json
import shutil
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

try:  # Windows consoles default to cp1252; the report uses accents and arrows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_ai  # provider-agnostic model access (see scripts/eden_ai.py)

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = Path.home() / ".claude"
APPLY = "--apply" in sys.argv
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

# Kit skills as they were named by the old file-copy installer (dev-system-eden <= 2.1.0).
OLD_SKILL_NAMES = {"eden", "eden-brain", "eden-memory", "eden-context", "eden-shopify"}


def say(msg):
    print(msg)


def backup(path, label):
    dest = CLAUDE / "backups" / f"{label}-{STAMP}" / path.relative_to(CLAUDE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(dest))
    return dest


def norm(p):
    try:
        return p.read_text(encoding="utf-8").replace("\r\n", "\n").lstrip("﻿").strip()
    except OSError:
        return None


def kit_rules():
    rules = ROOT / "rules"
    # rules/on-demand/ stays inside the plugin: those rules are read by the flows that need them,
    # never synced to ~/.claude/rules where they would load in every session.
    return sorted(p.relative_to(rules) for p in rules.rglob("*.md")
                  if p.name != "DIGEST.md" and "on-demand" not in p.relative_to(rules).parts)


def rules_state():
    state = {"synced": [], "outdated": [], "missing": []}
    for rel in kit_rules():
        g = norm(CLAUDE / "rules" / rel)
        key = "missing" if g is None else ("synced" if g == norm(ROOT / "rules" / rel) else "outdated")
        state[key].append(rel.as_posix())
    return state


def legacy_items():
    """What the old file-copy installer left in ~/.claude that the plugin now provides."""
    items = []
    plugin_skills = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    for name in sorted(plugin_skills | OLD_SKILL_NAMES):
        p = CLAUDE / "skills" / name
        if p.is_dir():
            items.append(p)
    items += sorted((CLAUDE / "agents").glob("eden-*.md"))
    for rel in ("eden/hooks", "brain/project", "teams/_generic", "teams/shopify", "teams/wordpress",
                "profiles/_template", "team/project-config.example.json"):
        p = CLAUDE / rel
        if p.exists():
            items.append(p)
    return items


def settings_hooks():
    try:
        data = json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    found = []
    for event, groups in data.get("hooks", {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                if any(s in h.get("command", "") for s in ("eden_brain.py", "eden_guard.py")):
                    found.append(f"{event}: {h['command']}")
    return found


def cli_logged_in():
    try:
        out = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=20,
                             shell=sys.platform == "win32",
                             creationflags=0x08000000 if sys.platform == "win32" else 0).stdout
        return '"loggedIn": true' in out
    except (OSError, subprocess.TimeoutExpired):
        return False


def cmd_status():
    s = rules_state()
    say(f"Plugin: {ROOT}")
    say(f"Reglas Eden en ~/.claude/rules: {len(s['synced'])} al día · {len(s['outdated'])} desactualizadas · "
        f"{len(s['missing'])} sin sincronizar")
    say(f"Cerebro (~/.claude/eden-brain): {'sí' if (CLAUDE / 'eden-brain').is_dir() else 'no (opcional)'}")
    say(f"Config (~/.claude/eden-config.json): {'sí' if (CLAUDE / 'eden-config.json').exists() else 'no (opcional)'}")
    ai = eden_ai.ai_config()
    provider = ai.get("provider", "claude")
    say(f"Proveedor de IA para el destilador: {eden_ai.describe(ai)}"
        + ("" if "provider" in eden_ai._read_ai_section() else " — sin configurar: `ai` lo detecta y `ai auto` lo deja listo"))
    if provider == "claude":
        say(f"CLI claude con sesión: {'sí' if cli_logged_in() else 'no'}")
    ready = eden_ai.available()
    say("CLIs de IA en el PATH: " + (", ".join(n for n in eden_ai.CLI if ready[n]) or "ninguno"))
    keyed = [n for n, pc in eden_ai.API.items() if pc.get("api_key_env") and ready[n]]
    say("APIs con clave en el entorno: " + (", ".join(keyed) or "ninguna")
        + " · locales sin clave: " + ", ".join(n for n, pc in eden_ai.API.items() if not pc.get("api_key_env"))
        + " (se elige en eden-config.json → ai.provider; alias: "
        + ", ".join(f"{a}→{t}" for a, t in eden_ai.ALIASES.items()) + ")")
    state = CLAUDE / "eden-brain" / ".state"
    queue = list((state / "queue").glob("*.md")) if (state / "queue").is_dir() else []
    try:
        st = json.loads((state / "distill_status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    err = st.get("last_error") or {}
    quarantine = list((state / "quarantine").glob("*.md")) if (state / "quarantine").is_dir() else []
    say(f"Cola del cerebro: {len(queue)} sin destilar · último éxito: {st.get('last_ok', 'nunca')}"
        + (f" · último error: {err.get('kind')} ({err.get('at')})" if err else "")
        + (f" · {len(quarantine)} notas en cuarentena" if quarantine else "")
        + (" → `/eden:brain learn now`, o `/eden:setup ai` para detectar y configurar el proveedor" if queue and err.get("kind") in ("auth", "missing_cli", "missing_key", "config") else ""))
    d, why, gh = githooks_state()
    say("Hooks de git de eden-commit-guard en este repo: " + (why if d is None else
        ", ".join(f"{k}: {'sí' if v == 'eden' else 'no'}" for k, v in gh.items())
        + ("" if all(v == "eden" for v in gh.values()) else " → `githooks` los instala (protege con cualquier IA)")))
    try:
        installed = sorted(json.loads((Path.home() / ".eden" / "installed.json").read_text(encoding="utf-8"))["hosts"])
    except (OSError, ValueError, KeyError):
        installed = []
    others = [h for h, info in eden_ai.eden_hosts.HOSTS.items() if h != "claude"
              and any(eden_ai.find_cli(e) for e in info["clis"])]
    say("Otras herramientas de IA: " + (", ".join(others) or "ninguna detectada")
        + f" · Eden instalado en: {', '.join(installed) or 'ninguna'}"
        + (" → `hosts` dice qué falta en cada una" if others else ""))
    try:
        import eden_uiux  # same folder; external design dependency, only reported here
        found = eden_uiux.locate(Path.cwd())
        say("UI/UX Pro Max (diseño sin Figma, siempre con tu sí): "
            + (f"{found.as_posix()} ({eden_uiux.version_of(found) or 'versión ?'})" if found
               else "no instalado (opcional) → " + eden_uiux.install_hint()))
    except Exception:
        pass
    for tool in ("gitleaks", "osv-scanner", "semgrep", "graphify"):
        say(f"{tool}: {'sí' if shutil.which(tool) else 'no'}")
    legacy, hooks = legacy_items(), settings_hooks()
    say(f"Instalación antigua por copia: {len(legacy)} elementos en ~/.claude, {len(hooks)} hooks en settings.json"
        + (" → `/eden:setup migrate`" if legacy or hooks else ""))


def cmd_rules():
    s = rules_state()
    todo = s["outdated"] + s["missing"]
    if not todo:
        return say("Las reglas Eden de ~/.claude/rules ya están al día. Nada que hacer.")
    for rel in todo:
        state = "actualizar" if rel in s["outdated"] else "copiar"
        say(f"{'APLICADO' if APPLY else 'haría'}: {state} ~/.claude/rules/{rel}")
        if APPLY:
            dest = CLAUDE / "rules" / rel
            if dest.exists():
                backup(dest, "eden-rules")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "rules" / rel, dest)
    if not APPLY:
        say("(nada escrito: vuelve a correr con --apply tras el sí del dev)")


def cmd_brain():
    brain, memory = CLAUDE / "eden-brain", CLAUDE / "eden-memory"
    actions = []
    if not brain.exists():
        actions.append(("crear ~/.claude/eden-brain (vault de Obsidian)", lambda: shutil.copytree(ROOT / "brain" / "global", brain)))
    else:
        for sub in ("inbox/_rejected", "me", "semantic", "procedural", "episodic", "projects"):
            if not (brain / sub).exists():
                actions.append((f"crear eden-brain/{sub}", lambda s=sub: (brain / s).mkdir(parents=True)))
        if not (brain / "me" / "working-style.md").exists():
            actions.append(("sembrar eden-brain/me/working-style.md",
                            lambda: shutil.copy2(ROOT / "brain" / "global" / "me" / "working-style.md", brain / "me")))
    if not memory.exists():
        actions.append(("crear ~/.claude/eden-memory", lambda: shutil.copytree(ROOT / "memory", memory)))
    if not actions:
        return say("El cerebro ya está listo. Nada que hacer.")
    for label, fn in actions:
        say(f"{'APLICADO' if APPLY else 'haría'}: {label}")
        if APPLY:
            fn()
    if not APPLY:
        say("(nada escrito: vuelve a correr con --apply tras el sí del dev)")


def cmd_config():
    cfg = CLAUDE / "eden-config.json"
    if cfg.exists():
        return say("~/.claude/eden-config.json ya existe: se conserva (es tuyo).")
    say(f"{'APLICADO' if APPLY else 'haría'}: crear ~/.claude/eden-config.json desde la plantilla")
    if APPLY:
        shutil.copy2(ROOT / "config" / "eden-config.example.json", cfg)
    else:
        say("(nada escrito: vuelve a correr con --apply tras el sí del dev)")


def cmd_migrate():
    items, hooks = legacy_items(), settings_hooks()
    if not items and not hooks:
        return say("No queda nada de la instalación antigua. Nada que hacer.")
    for p in items:
        say(f"{'RESPALDADO Y RETIRADO' if APPLY else 'retiraría'}: {p}")
        if APPLY:
            backup(p, "eden-file-install")
    for h in hooks:
        say(f"{'QUITADO' if APPLY else 'quitaría'} de settings.json: {h}")
    if APPLY and hooks:
        subprocess.run([sys.executable, "-I", str(ROOT / "hooks" / "install_hooks.py"),
                        str(CLAUDE / "settings.json"), str(ROOT / "hooks"), "--remove"], check=True)
    say("Se conservan: ~/.claude/rules (reglas), eden-brain, eden-memory y eden-config.json (tus datos).")
    if not APPLY:
        say("(nada tocado: vuelve a correr con --apply tras el sí del dev)")
    else:
        say(f"Respaldo en ~/.claude/backups/eden-file-install-{STAMP}/")


# ---------------------------------------------------------------- githooks: the guard for any tool

GIT_HOOKS = ("pre-commit", "commit-msg", "pre-push")
HOOK_MARK = "# eden-guard (managed by Eden: /eden:setup githooks)"
POINTER = CLAUDE / "eden-cache" / "plugin_root"


def hook_script(kind):
    """POSIX sh (Git for Windows runs it too). The plugin path is read at run time from the pointer the
    SessionStart hook keeps current, so a plugin update never breaks the hook; the path at install
    time is the fallback. A hook that was already there runs first, with the same stdin."""
    return f"""#!/bin/sh
{HOOK_MARK}
# Runs Eden's secret / AI-signature guard on every commit and push, whoever makes it.
# Skip once: git ... --no-verify   ·   disable: EDEN_GUARD_OFF=1
root="$(cat "$HOME/.claude/eden-cache/plugin_root" 2>/dev/null)"
[ -f "$root/hooks/eden_guard.py" ] || root="{ROOT.as_posix()}"
input="$(cat)"
if [ -x "$0.eden-prev" ]; then
  printf '%s\\n' "$input" | "$0.eden-prev" "$@" || exit $?
fi
if [ ! -f "$root/hooks/eden_guard.py" ]; then
  echo "eden-guard: no encuentro el plugin Eden; este {kind} sale sin revisar" >&2
  exit 0
fi
PY=python; command -v python >/dev/null 2>&1 || PY=python3
printf '%s\\n' "$input" | "$PY" -I "$root/hooks/eden_guard.py" --git-hook {kind} "$@"
"""


def git_out(*args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=20,
                              creationflags=0x08000000 if sys.platform == "win32" else 0).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def githooks_state():
    """(hooks dir or None, reason, {hook: 'eden' | 'other' | 'none'}) for the repo in the cwd."""
    if not git_out("rev-parse", "--git-dir"):
        return None, "aquí no hay un repositorio git", {}
    custom = git_out("config", "core.hooksPath")
    if custom:
        return None, f"el repo usa core.hooksPath ({custom}, p. ej. husky)", {}
    d = Path(git_out("rev-parse", "--git-path", "hooks")).resolve()
    state = {}
    for k in GIT_HOOKS:
        f = d / k
        state[k] = "none" if not f.exists() else ("eden" if HOOK_MARK in (norm(f) or "") else "other")
    return d, "", state


def cmd_githooks():
    remove = "--remove" in sys.argv
    d, why, state = githooks_state()
    if d is None:
        say(f"No instalo hooks de git: {why}.")
        if why.startswith("el repo usa core.hooksPath"):
            say("Añade a mano, al final de cada hook de esa carpeta (pre-commit, commit-msg, pre-push):")
            say(f'  python -I "{(ROOT / "hooks" / "eden_guard.py").as_posix()}" --git-hook <nombre-del-hook> "$@"')
        return
    for k in GIT_HOOKS:
        f, prev = d / k, d / f"{k}.eden-prev"
        if remove:
            if state[k] != "eden":
                continue
            say(f"{'QUITADO' if APPLY else 'quitaría'}: .git/hooks/{k}" + (" (se restaura el anterior)" if prev.exists() else ""))
            if APPLY:
                f.unlink()
                if prev.exists():
                    prev.rename(f)
            continue
        if state[k] == "eden":
            say(f"al día: .git/hooks/{k}" if norm(f) == hook_script(k).strip() else f"{'ACTUALIZADO' if APPLY else 'actualizaría'}: .git/hooks/{k}")
            if norm(f) == hook_script(k).strip() or not APPLY:
                continue
        elif state[k] == "other":
            say(f"{'APLICADO' if APPLY else 'haría'}: .git/hooks/{k} — el hook que ya tenías pasa a {k}.eden-prev y sigue corriendo primero")
            if APPLY:
                f.rename(prev)
        else:
            say(f"{'APLICADO' if APPLY else 'haría'}: crear .git/hooks/{k}")
        if APPLY:
            d.mkdir(parents=True, exist_ok=True)
            f.write_text(hook_script(k), encoding="utf-8", newline="\n")
            f.chmod(0o755)
    if APPLY and not remove:
        record_plugin_root()
    if not APPLY:
        say("(nada escrito: vuelve a correr con --apply tras el sí del dev)")
    elif not remove:
        say("Listo: el guard revisa cada commit y push de este repo, lo haga quien lo haga.")


def record_plugin_root():
    try:
        POINTER.parent.mkdir(parents=True, exist_ok=True)
        if norm(POINTER) != ROOT.as_posix():
            POINTER.write_text(ROOT.as_posix(), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- ai: provider for Eden's headless calls

def opt(name):
    """Value after --name in argv; "" when the flag is last or followed by another flag (PowerShell drops an
    empty "" argument, so `--model "" --apply` arrives as `--model --apply`); None when absent."""
    if name not in sys.argv:
        return None
    i = sys.argv.index(name)
    nxt = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
    return "" if nxt.startswith("--") else nxt


def load_config():
    cfg = CLAUDE / "eden-config.json"
    src = cfg if cfg.exists() else ROOT / "config" / "eden-config.example.json"
    return json.loads(src.read_text(encoding="utf-8")), cfg.exists()


def merge_ai(data, section):
    """New config dict with `section` (provider/model/providers) folded into data['ai']."""
    data = json.loads(json.dumps(data))
    ai = data.setdefault("ai", {})
    for k, v in section.items():
        if k == "providers":
            provs = ai.setdefault("providers", {})
            for name, override in v.items():
                provs.setdefault(name, {}).update({kk: vv for kk, vv in override.items() if vv not in (None, "")})
        else:
            ai[k] = v
    return data


def write_ai(section, label):
    data, existed = load_config()
    new = merge_ai(data, section)
    try:  # validate exactly what would be written, with the same resolver the distiller uses
        eden_ai.provider_config(eden_ai.ai_config({"ai": eden_ai._clean(new["ai"])}))
    except eden_ai.AIError as exc:
        return say(f"No se escribe nada: {exc}")
    old_ai = {k: v for k, v in (data.get("ai") or {}).items() if not k.startswith("_")}
    new_ai = {k: v for k, v in new["ai"].items() if not k.startswith("_")}
    for k in ("provider", "model"):
        if old_ai.get(k) != new_ai.get(k):
            say(f"  ai.{k}: {old_ai.get(k)!r} → {new_ai.get(k)!r}")
    for name, override in (section.get("providers") or {}).items():
        shown = {k: v for k, v in override.items() if v not in (None, "")}
        if shown:
            say(f"  ai.providers.{name}: {json.dumps(shown, ensure_ascii=False)}")
    target = CLAUDE / "eden-config.json"
    if not APPLY:
        return say(f"(nada escrito: {'se actualizaría' if existed else 'se crearía'} {target} — "
                   "vuelve a correr con --apply tras el sí del dev)")
    if existed:
        dest = CLAUDE / "backups" / f"{label}-{STAMP}" / "eden-config.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
        say(f"Respaldo: {dest}")
    target.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"APLICADO: {target} → proveedor {new_ai.get('provider')}. Comprueba con `ai test`.")


def show_candidates(cands):
    if not cands:
        say("No encontré ningún proveedor: ni CLIs de IA en el PATH, ni claves de API en el entorno, "
            "ni ollama en localhost. Configúralo a mano con `ai set` (ver la guía).")
        return
    say("Proveedores detectados (mejor primero):")
    for i, c in enumerate(cands, 1):
        state = "listo" if c["ready"] else "falta: " + ", ".join(c["needs"])
        model = c["model"] or ("el del CLI" if c["kind"] == "cli" else "—")
        say(f"  {i}. {c['provider']:<10} {c['kind']:<7} modelo {model:<28} {c['why']} · {state}")


def cmd_ai():
    sub = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "detect"
    current = eden_ai.ai_config()
    configured = (CLAUDE / "eden-config.json").exists() and "provider" in eden_ai._read_ai_section()

    if sub == "detect":
        say(f"Configurado ahora: {eden_ai.describe(current)}" + ("" if configured else " (default, sin configurar)"))
        cands = eden_ai.detect(claude_logged_in=cli_logged_in)
        show_candidates(cands)
        best = eden_ai.recommend(cands)
        if best:
            say(f"Recomendado: {best['provider']} — automático con `ai auto`, o elige otro con `ai auto --pick N`.")
        say("Manual (avanzado): `ai set <proveedor> [--model M] [--key-env VAR] [--base-url URL] [--api anthropic|openai]`.")
        return

    if sub == "auto":
        cands = eden_ai.detect(claude_logged_in=cli_logged_in)
        show_candidates(cands)
        pick = opt("--pick")
        if pick:
            try:
                chosen = cands[int(pick) - 1]
            except (ValueError, IndexError):
                return say(f"--pick {pick} no corresponde a ningún proveedor de la lista.")
            if not chosen["ready"]:
                return say(f"{chosen['provider']} no está listo (falta: {', '.join(chosen['needs'])}). "
                           "Complétalo con `ai set` o elige otro.")
        else:
            chosen = eden_ai.recommend(cands)
        if not chosen:
            return say("Nada listo para configurar solo. Usa `ai set` para completar lo que falta.")
        say(f"Configuración automática → {chosen['provider']} ({chosen['why']}):")
        return write_ai(chosen["ai"], "eden-ai")

    if sub == "set":
        name = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
        if not name:
            return say("Uso: ai set <proveedor> [--model M] [--key-env VAR] [--base-url URL] [--api anthropic|openai]"
                       f"\nIntegrados: {', '.join(eden_ai.KNOWN)} · alias: {', '.join(eden_ai.ALIASES)}")
        name = eden_ai.ALIASES.get(name, name)
        override = {"api_key_env": opt("--key-env"), "base_url": opt("--base-url"), "api": opt("--api")}
        section = {"provider": name}
        if opt("--model") is not None:
            section["model"] = opt("--model")
        if any(override.values()):
            section["providers"] = {name: override}
        say(f"Configuración manual → {name}:")
        return write_ai(section, "eden-ai")

    if sub == "test":
        say(f"Proveedor: {eden_ai.describe(current)}")
        if not APPLY:
            return say("(haría UNA llamada corta real al proveedor — gasta unos pocos tokens; "
                       "vuelve a correr con --apply tras el sí del dev)")
        started = time.time()
        try:
            res = eden_ai.run("Reply with exactly this text and nothing else: EDEN-OK", timeout=120)
        except eden_ai.AIError as exc:
            return say(f"FALLÓ ({exc.kind}): {exc}")
        except subprocess.TimeoutExpired:
            return say("FALLÓ: no respondió en 120 s.")
        if res.returncode == 0 and "EDEN-OK" in (res.stdout or ""):
            return say(f"OK: el proveedor respondió en {eden_ai.elapsed(started)} s. El destilador puede usarlo.")
        return say(f"FALLÓ (código {res.returncode}): {((res.stderr or '') + (res.stdout or '')).strip()[:500]}")

    say("Uso: ai [detect | auto [--pick N] | set <proveedor> … | test] [--apply]")


def cmd_hosts():
    """`hosts [detect | install … | uninstall …] [--apply]`: Eden for other AI tools (scripts/eden_port.py)."""
    args = sys.argv[2:] or ["detect"]
    if args[0] not in ("detect", "plan", "install", "uninstall", "doctor", "sync"):
        args = ["install", *args]
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "eden_port.py"), *args])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"status": cmd_status, "rules": cmd_rules, "brain": cmd_brain, "config": cmd_config,
     "migrate": cmd_migrate, "ai": cmd_ai, "githooks": cmd_githooks,
     "hosts": cmd_hosts}.get(cmd, cmd_status)()


if __name__ == "__main__":
    main()
