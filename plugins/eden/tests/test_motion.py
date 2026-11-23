"""The animation team: rules, lead skill, agents, roster, patterns and the hand-offs from other skills."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


# --- the rules
rules = read("rules/eden-motion-rules.md")
check("ladder: CSS → scroll-driven/View Transitions → WAAPI → library", all(k in rules for k in (
    "@starting-style", "animation-timeline", "startViewTransition", "Web Animations API", "con el sí del dev")))
check("each proposal names its rung and why", "en qué escalón se quedó y por qué no bastó el anterior" in rules)
check("unsupported browsers see it still and complete", "@supports" in rules and "se ve bien" in rules)
check("only composited properties; layout properties banned", "`transform` y `opacity` siempre" in rules
      and "transition: all" in rules and "width`/`height" in rules)
check("will-change only while animating", "`will-change` solo mientras anima" in rules)
check("no scroll listeners: timelines or IntersectionObserver; passive + rAF", "IntersectionObserver" in rules
      and "passive: true" in rules and "requestAnimationFrame" in rules and "layout thrashing" in rules)
check("Core Web Vitals: LCP visible, CLS 0, INP", "LCP" in rules and "CLS = 0" in rules and "INP" in rules
      and "primer pintado" in rules)
check("offscreen and hidden-tab pausing", "visibilitychange" in rules and "content-visibility" in rules)
check("budget: 60 fps, long tasks, JS weight", "60 fps" in rules and "50 ms" in rules and "30 KB" in rules)
check("cleanup incl. Shopify section reloads", "disconnectedCallback" in rules and "shopify:section:load" in rules)
check("accessibility: reduced motion, 3 flashes, pause after 5 s, menus focus", all(k in rules for k in (
    "prefers-reduced-motion: reduce", "3 veces por segundo", "2.2.2", "aria-expanded", "aria-label")))
check("motion tokens and the minified time gotcha", "--{prefix}-duration" in rules and "`.5s`" in rules)
check("library licences are checked (GSAP is not MIT)", "**no MIT**" in rules and "MIT" in rules)
check("optimizing needs a measured before/after", "antes y después medido" in rules)

# --- lead skill, agents, roster
skill = read("skills/motion/SKILL.md")
head = skill.split("---")[1]
check("lead skill: dev-invoked only", "disable-model-invocation: true" in head and "name: motion" in head)
check("lead skill: four modes", all(f"`{m}`" in skill for m in ("create", "modify", "optimize", "audit")))
check("lead skill: plan waits for the yes; library is a separate yes", "Nada se escribe sin el sí del dev" in skill
      and "Una librería nueva es un sí aparte" in skill)
check("lead skill: verifies reduced motion in the browser", "Emulate CSS" in skill)
for agent, writes in (("motion-architect", False), ("motion-dev", True)):
    text = read(f"agents/{agent}.md")
    fm = text.split("---")[1]
    tools = re.search(r"^tools: (.+)$", fm, re.M).group(1)
    check(f"{agent}: name and model", f"name: {agent}" in fm and re.search(r"^model: \w+", fm, re.M))
    check(f"{agent}: {'can' if writes else 'cannot'} write", ("Write" in tools) == writes and ("Edit" in tools) == writes)
    check(f"{agent}: only inside the team", "SOLO SE USA DENTRO DEL EQUIPO DE ANIMACIÓN" in fm)
dev = read("agents/motion-dev.md")
check("motion-dev stops instead of adding an unapproved library", "te detienes y lo dices" in dev)
roster = read("teams/motion/roster.md")
check("roster: lead and agents", "Líder: **`/eden:motion`**" in roster and "`eden:motion-dev`" in roster
      and "`eden:motion-architect`" in roster)
check("roster: no files of its own; works in the stack's files", "no tiene archivos propios" in roster)
team = read("rules/eden-team-rules.md")
check("role `motion` in the closed vocabulary", "| `motion` |" in team)

# --- pattern library
refs = ROOT / "skills" / "motion" / "references"
for name in ("techniques", "patterns-menus", "patterns-heroes", "patterns-sliders", "patterns-sections", "patterns-text"):
    f = refs / f"{name}.md"
    check(f"pattern file {name} exists and covers reduced motion", f.is_file()
          and ("prefers-reduced-motion" in f.read_text(encoding="utf-8") or "reduced-motion" in f.read_text(encoding="utf-8")))
check("heroes: the LCP is never hidden", "LCP" in (refs / "patterns-heroes.md").read_text(encoding="utf-8"))
check("sliders: scroll-snap first, autoplay with pause", "scroll-snap-type" in (refs / "patterns-sliders.md").read_text(encoding="utf-8")
      and "pausa" in (refs / "patterns-sliders.md").read_text(encoding="utf-8").lower())
check("text: split stays readable", "aria-hidden" in (refs / "patterns-text.md").read_text(encoding="utf-8"))
check("techniques: tokens parsed in ms and s", "endsWith('ms')" in (refs / "techniques.md").read_text(encoding="utf-8"))

# --- hand-offs
for s in ("ignition-task", "create-new-section", "section-mod"):
    check(f"{s} hands animation to the motion role", "**rol `motion`**" in read(f"skills/{s}/SKILL.md")
          and "eden-motion-rules.md" in read(f"skills/{s}/SKILL.md"))
check("/eden:go routes animation requests", "| **Animación** |" in read("skills/go/SKILL.md"))
check("digest mentions motion", "eden-motion-rules.md" in read("rules/DIGEST.md"))
check("quality rules link to motion rules", "eden-motion-rules.md" in read("rules/eden-quality-rules.md"))

# --- phase 2: static analyzer and real measurement
import json
import os
import shutil
import subprocess
import tempfile
MOTION = ROOT / "scripts" / "eden_motion.py"
FIX = ROOT / "tests" / "fixtures" / "motion"


def run(*args, timeout=300):
    r = subprocess.run([sys.executable, "-I", str(MOTION), *args], capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    return json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"raw": r.stdout, "err": r.stderr}


bad = run("lint", str(FIX / "bad.html"))
rules_found = {f["rule"] for f in bad["findings"]}
for rid in ("transition-all", "scroll-listener", "listener-not-passive", "layout-read-in-loop", "style-layout-write",
            "interval-animation", "no-reduced-motion"):
    check(f"lint finds {rid} in the bad page", rid in rules_found)
check("lint: highs make it not ok, with file:line and fix", bad["ok"] is False and all(f["line"] > 0 and f["fix"] for f in bad["findings"]))
good = run("lint", str(FIX / "good.html"))
check("lint: the good page is clean", good["ok"] and good["findings"] == [])
tmp = Path(tempfile.mkdtemp())
(tmp / "a.css").write_text("@keyframes grow { from { width: 0 } to { width: 100% } }" + chr(10) + "* { will-change: transform }"
                           + chr(10) + ".x { transition: transform .3s; }" + chr(10), encoding="utf-8")
(tmp / "b.js").write_text("gsap.to('.x', { x: 100 });" + chr(10), encoding="utf-8")
(tmp / "c.html").write_text('<div data-aos="fade-up">Hi</div><video autoplay muted loop></video>', encoding="utf-8")
(tmp / "node_modules").mkdir()
(tmp / "node_modules" / "lib.css").write_text(".y { transition: all 1s }", encoding="utf-8")
more = {f["rule"] for f in run("lint", str(tmp))["findings"]}
for rid in ("keyframes-layout", "will-change-global", "gsap-no-cleanup", "hidden-until-js", "autoplay-video"):
    check(f"lint finds {rid}", rid in more)
check("lint skips node_modules", not any("node_modules" in f["file"] for f in run("lint", str(tmp))["findings"]))
check("lint: transition of transform only is fine", "transition-all" not in more and "transition-layout" not in more)

node = shutil.which("node")
br = subprocess.run([node, str(ROOT / "scripts" / "video" / "render.mjs"), "tools"], capture_output=True, text=True).stdout if node else ""
if node and '"browser":"' in br.replace(" ", "") and os.environ.get("EDEN_TEST_MEASURE", "1") == "1":
    mb = run("measure", str(FIX / "bad.html"), "--scroll", "--out", str(tmp / "bad.json"))
    mg = run("measure", str(FIX / "good.html"), "--scroll", "--out", str(tmp / "good.json"))
    status = lambda m, cid: next((b["status"] for b in m.get("budget", []) if b["id"] == cid), None)
    check("measure: the bad page animates layout properties", status(mb, "layout-properties") == "fail"
          and {"left", "width"} & {p for a in mb["animations"] for p in a["layout"]})
    check("measure: the bad page does layout work while scrolling", mb["work"]["layouts"] > 50)
    check("measure: the good page animates only composited properties", status(mg, "layout-properties") == "pass"
          and mg["work"]["layouts"] < mb["work"]["layouts"])
    check("measure: frames counted during the interaction", mg["interaction"]["frames"] > 30 and mg["interaction"]["fps"] > 0)
    mr = run("measure", str(FIX / "good.html"), "--scroll", "--reduced")
    check("measure: with reduced motion nothing moves", status(mr, "reduced-motion") == "pass")
    table = subprocess.run([sys.executable, "-I", str(MOTION), "compare", str(tmp / "bad.json"), str(tmp / "good.json")],
                           capture_output=True, text=True, encoding="utf-8").stdout
    check("compare: before → after table", "| layouts |" in table and "✅" in table)
    check("measure refuses non-web urls", run("measure", "javascript:alert(1)").get("ok") is False)
else:
    print("SKIP measurement (no node or browser)")

audit = read("skills/motion-audit/SKILL.md")
check("motion-audit skill: dev-invoked, static + measure + reduced + compare", "disable-model-invocation: true" in audit
      and "lint" in audit and "--reduced" in audit and "compare" in audit and "--throttle 4" in audit)
pa = read("agents/motion-perf-auditor.md")
check("motion-perf-auditor cannot edit", "Write" not in pa.split("---")[1] and "Edit" not in pa.split("---")[1])
check("roster: quality-auditor is the perf auditor", "`quality-auditor` | `eden:motion-perf-auditor`" in read("teams/motion/roster.md"))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
