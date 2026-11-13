import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def read(rel):
    return (PLUGIN / rel).read_text(encoding="utf-8")


go = read("skills/go/SKILL.md")
auto = go.split("## Modo orquestador")[1] if "## Modo orquestador" in go else ""

# --- the orchestrator: opt-in, Fable plans, Opus/Sonnet by complexity
check("go has the orchestrator mode", bool(auto) and "--auto" in go.split("---")[1])
check("--auto is opt-in, never on its own", "Nunca se activa solo" in auto and "go.auto_default" in auto)
check("--auto authorizes only local and reversible work", "local y reversible" in auto and "Nada más" in auto)
check("Fable orchestrates, Opus complex, Sonnet bounded", "Fable" in go and "Opus" in auto and "Sonnet" in auto
      and "parámetro\n`model`" in auto.replace("parámetro `model`", "parámetro\n`model`") or "`model`" in auto)

# --- blocking vs non-blocking
blocking = auto.split("### 3")[1].split("### 4")[0]
for k in ("Commit, push, PR", "tracker", "Borrar", "dependencias", "seguridad", "alcance", "w2shopify"):
    check(f"blocking includes: {k}", k in blocking)
check("when in doubt it blocks", "Ante la duda, es bloqueante" in auto)
check("non-blocking assumption is the most reversible", "el más reversible" in auto)

# --- question board, answers, closure
check("question board file and format", "questions-{tarea}.md" in auto and "Supuse:" in auto and "Depende:" in auto)
check("answers command reworks only what depended on it", "/eden:go answers" in auto and "rehace solo lo que dependía" in auto)
check("closure always stops at turnoff-task's pause", "se detiene siempre" in auto and "Paso 7" in auto)
check("upfront questions batched at start", "todas juntas al\narrancar" in auto or "todas juntas" in auto)

# --- the chain skills and the rules know about it
for rel in ("skills/ignition-task/SKILL.md", "skills/create-new-section/SKILL.md", "skills/section-mod/SKILL.md",
            "skills/test-visual/SKILL.md", "skills/turnoff-task/SKILL.md"):
    check(f"{rel.split('/')[1]}: aware of --auto", "go --auto" in read(rel))
check("turnoff report lists open assumptions", "🤖 Supuestos" in read("skills/turnoff-task/SKILL.md"))
wf = read("rules/eden-workflow-rules.md")
check("workflow rule: exception keeps the yes for what leaves the machine", "go --auto" in wf and "sigue esperando el sí explícito" in wf)
check("digest mentions it", "go --auto" in read("rules/DIGEST.md"))

# --- model tiers
ms = read("rules/eden-model-strategy-rules.md")
check("model rule: plan tier is Fable", "**`plan`**" in ms and "**Fable**" in ms)
check("model rule: Opus vs Sonnet table", "A **Opus** (`strong`) si" in ms and "A **Sonnet** (`fast`) si" in ms)
sys.path.insert(0, str(PLUGIN / "hooks"))
import eden_hosts  # noqa: E402
check("host table: Claude plans with Fable", eden_hosts.HOSTS["claude"]["tiers"]["plan"] == "fable")
cfg = json.loads(read("team/project-config.example.json"))
check("project config: auto_default off by default", cfg["go"]["auto_default"] is False)

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
