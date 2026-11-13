import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
EXTRACT = PLUGIN / "skills" / "w2shopify" / "references" / "extract.js"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


src = EXTRACT.read_text(encoding="utf-8")
body = "\n".join(l for l in src.splitlines() if not l.startswith("//"))

# --- the extractor: one arrow function that browser_evaluate can take as is
check("extract.js is a single arrow function", body.lstrip().startswith("() => {") and body.rstrip().endswith("}"))
node = shutil.which("node")
if node:
    r = subprocess.run([node, "-e", "const fs=require('fs');const b=fs.readFileSync(process.argv[1],'utf8').split('\\n')"
                        ".filter(l=>!l.startsWith('//')).join('\\n');const f=new Function('return ('+b+')')();"
                        "if(typeof f!=='function')process.exit(3)", str(EXTRACT)], capture_output=True, text=True)
    check("extract.js parses (node)", r.returncode == 0)
else:
    print("SKIP node not installed: parse check")

# read-only and offline by contract: nothing that changes the page or talks to the network
FORBIDDEN = [r"\.innerHTML\s*=", r"\.outerHTML\s*=", r"\.textContent\s*=", r"\.innerText\s*=", r"setAttribute\(",
             r"removeAttribute\(", r"appendChild\(", r"insertBefore\(", r"\.remove\(", r"\.click\(", r"\.submit\(",
             r"\bfetch\(", r"XMLHttpRequest", r"sendBeacon", r"WebSocket", r"localStorage", r"sessionStorage",
             r"document\.cookie", r"\.style\.\w+\s*=", r"classList\.(add|remove|toggle)", r"\beval\(", r"new Function"]
hits = [p for p in FORBIDDEN if re.search(p, body)]
check(f"extract.js never mutates the page or uses the network {hits or ''}", not hits)
check("extract.js reads computed styles and boxes", "getComputedStyle" in body and "getBoundingClientRect" in body)
check("extract.js bounds its output", "MAX_SECTIONS" in body and "MAX_ITEMS" in body and "TXT" in body)
check("fixture page exists for manual / browser runs", (PLUGIN / "tests" / "fixtures" / "w2s-page.html").exists())

# --- the skill: explicit only, rights first, no publish, no code copy
skill = (PLUGIN / "skills" / "w2shopify" / "SKILL.md").read_text(encoding="utf-8")
check("skill only by explicit invocation", "disable-model-invocation: true" in skill and "SOLO POR INVOCACIÓN EXPLÍCITA" in skill)
check("rights are asked before the site is opened", skill.index("Derecho a reproducir") < skill.index("Paso 1"))
check("inspiration mode exists for sites without rights", "inspiration" in skill and "--inspiration" in skill)
check("measures with Playwright, stops without it", "MCP de Playwright" in skill and "detente" in skill)
check("each phase waits for approval", skill.count("Espera el sí") + skill.count("espera aprobación") >= 2)
check("never copies code, never publishes", "Nada del código del sitio" in skill and "no publica" in skill
      and "shopify theme push" in skill)
check("no data migration", "Migrar productos" in skill)

# --- the agent: read-only, private cookie choice, writes only its context folder
agent = (PLUGIN / "agents" / "web-extractor.md").read_text(encoding="utf-8")
check("agent declared on the fast tier", re.search(r"^model: sonnet$", agent, re.M) is not None)
check("agent picks the most private cookie option", "más privada" in agent and "Nunca aceptes" in agent)
check("agent never logs in, fills forms or downloads", all(k in agent for k in ("Rellenar formularios", "Descargar imágenes", "iniciar sesión")))
check("agent writes only to .claude/context/w2s/", "Escribir fuera de `.claude/context/w2s/`" in agent)

# --- wiring
team = (PLUGIN / "rules" / "eden-team-rules.md").read_text(encoding="utf-8")
check("role in the closed vocabulary", "| `web-extractor` |" in team)
check("role in the Shopify roster", "| `web-extractor` | `eden:web-extractor` |" in (PLUGIN / "teams/shopify/roster.md").read_text(encoding="utf-8"))
check("router routes to it", "w2shopify" in (PLUGIN / "skills/go/SKILL.md").read_text(encoding="utf-8"))
for rel in ("skills/create-new-section/SKILL.md", "skills/section-mod/SKILL.md", "skills/test-visual/SKILL.md",
            "skills/create-fundaments/SKILL.md", "rules/eden-design-rules.md"):
    check(f"{rel}: accepts the measured site as a design source", "w2shopify" in (PLUGIN / rel).read_text(encoding="utf-8"))
check("design rule: Figma still wins", "Figma > sitio medido" in (PLUGIN / "rules/eden-design-rules.md").read_text(encoding="utf-8"))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
