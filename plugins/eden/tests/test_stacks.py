"""Structural checks for Eden stacks: rosters, agents, leads, setups, rule modules and detection."""
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eden_stack", ROOT / "scripts" / "eden_stack.py")
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


# --- role vocabulary (closed) ---------------------------------------------------------------------
team = (ROOT / "rules" / "eden-team-rules.md").read_text(encoding="utf-8")
vocab_block = team.split("### Vocabulario de roles")[1].split("###")[0]
VOCAB = set(re.findall(r"^\| `([a-z-]+)` \|", vocab_block, re.M))
check("vocabulary has tester", "tester" in VOCAB)
check("vocabulary size", len(VOCAB) == 15)

AGENTS = {p.stem for p in (ROOT / "agents").glob("*.md")}
SKILLS = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()}

# --- frontmatter of every agent: name matches the file, tools/model declared ------------------------
for p in sorted((ROOT / "agents").glob("*.md")):
    head = p.read_text(encoding="utf-8").split("---")[1]
    check(f"agent {p.stem}: name matches file", re.search(rf"^name: {re.escape(p.stem)}$", head, re.M) is not None)
    # no tools: line = inherits every tool (the router-* agents do that on purpose)
    check(f"agent {p.stem}: model declared", re.search(r"^model: \w+", head, re.M) is not None)

# --- every skill is invoked by the dev, never by the model (mydaily also runs as a routine) -----------
for name in sorted(SKILLS):
    head = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    check(f"skill {name}: name matches folder", re.search(rf"^name: {re.escape(name)}$", head, re.M) is not None)
    if name != "mydaily":
        check(f"skill {name}: disable-model-invocation", "disable-model-invocation: true" in head)

# --- every roster: roles in vocabulary, agents exist ------------------------------------------------
for roster in sorted((ROOT / "teams").glob("*/roster.md")):
    stack = roster.parent.name
    text = roster.read_text(encoding="utf-8")
    rows = re.findall(r"^\| `([a-z-]+)` \| ([^|]+)\|", text, re.M)
    check(f"{stack}: roster has role rows", bool(rows))
    for role, agents in rows:
        check(f"{stack}: role `{role}` in vocabulary", role in VOCAB)
        for a in re.findall(r"`eden:([a-z0-9-]+)`", agents):
            check(f"{stack}: agent eden:{a} exists", a in AGENTS)

# --- every stack marked ✅ in eden-stack-rules has its module; stacks with a lead have it -------------
stack_rules = (ROOT / "rules" / "eden-stack-rules.md").read_text(encoding="utf-8")
for name, module, flavors, status in re.findall(
        r"^\| `([a-z-]+)` \| `?([^|`]+?)`?(?: \+ `flavors/`)? \| ([^|]+) \| [^|]+ \| (✅|🔜) \|", stack_rules, re.M):
    if status != "✅":
        continue
    check(f"{name}: rule module exists", (ROOT / module.strip()).is_file())
    if flavors.strip() != "—":
        for fl in [f.strip() for f in flavors.split("·")]:
            check(f"{name}: flavor {fl} has a file", (ROOT / "rules" / name / "flavors" / f"{fl}.md").is_file())
    roster = ROOT / "teams" / name / "roster.md"
    if roster.is_file():
        lead = re.search(r"Líder: \*\*`/eden:([a-z-]+)`\*\*", roster.read_text(encoding="utf-8"))
        if lead:
            check(f"{name}: lead skill /eden:{lead.group(1)} exists", lead.group(1) in SKILLS)
    if name not in ("shopify", "wordpress"):  # stacks added from 3.4 on must ship the full set
        check(f"{name}: roster exists", roster.is_file())
        check(f"{name}: lead skill exists", name in SKILLS)
        check(f"{name}: setup skill exists", f"{name}-setup" in SKILLS)

# --- detection --------------------------------------------------------------------------------------
def project(files):
    d = Path(tempfile.mkdtemp())
    for rel, body in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return d


def pkg(*deps, dev=()):
    return {"name": "x", "dependencies": {d: "1" for d in deps}, "devDependencies": {d: "1" for d in dev}}


cases = {
    "shopify app beats react": ({"shopify.app.toml": "", "package.json": pkg("react", "@shopify/app-bridge-react")},
                                ("shopify-app", None)),
    "shopify theme": ({"sections/a.liquid": "", "snippets/b.liquid": "", "config/settings_schema.json": "[]"},
                      ("shopify", None)),
    "wordpress": ({"wp-config.php": "<?php"}, ("wordpress", None)),
    "wordpress theme style.css": ({"style.css": "/*\nTheme Name: X\n*/"}, ("wordpress", None)),
    "laravel beats php": ({"composer.json": {"require": {"laravel/framework": "^11"}}, "artisan": ""},
                          ("php", "laravel")),
    "plain php": ({"composer.json": {"require": {"monolog/monolog": "^3"}}}, ("php", "php")),
    "php files only": ({"index.php": "<?php"}, ("php", "php")),
    "expo beats react": ({"package.json": pkg("expo", "react", "react-native")}, ("mobile", "react-native")),
    "ionic beats react": ({"package.json": pkg("@ionic/react", "react")}, ("mobile", "ionic")),
    "capacitor config": ({"capacitor.config.ts": "", "package.json": pkg("@angular/core")}, ("mobile", "ionic")),
    "next beats react": ({"package.json": pkg("next", "react", "react-dom")}, ("react", "next")),
    "next by config file": ({"next.config.mjs": "", "package.json": pkg("react")}, ("react", "next")),
    "nest beats express": ({"package.json": pkg("@nestjs/core", "@nestjs/platform-express", "express")},
                           ("node", "nest")),
    "express": ({"package.json": pkg("express", "zod")}, ("node", "express")),
    "react spa": ({"package.json": pkg("react", "react-dom", dev=("vite",))}, ("react", "spa")),
    "plain node": ({"package.json": pkg("commander")}, ("node", "node")),
    "astro has no module": ({"astro.config.mjs": "", "package.json": pkg("astro")}, ("astro", None)),
    "empty": ({"README.md": "x"}, (None, None)),
}
for name, (files, (stack, flavor)) in cases.items():
    r = st.detect(project(files))
    check(f"detect {name} → {stack}/{flavor}", (r["stack"], r["flavor"]) == (stack, flavor) and not r["ambiguous"])

mono = st.detect(project({"package.json": {"name": "mono", "workspaces": ["apps/*"]},
                          "apps/web/package.json": pkg("next", "react"),
                          "apps/api/package.json": pkg("@nestjs/core")}))
check("monorepo flagged ambiguous with both apps",
      mono["ambiguous"] and {(c["path"], c["stack"]) for c in mono["candidates"]} == {("apps/web", "react"),
                                                                                      ("apps/api", "node")})
same = st.detect(project({"package.json": pkg("next", "react"), "apps/docs/package.json": pkg("next")}))
check("same stack in subproject is not ambiguous", not same["ambiguous"] and same["stack"] == "react")
dec = st.detect(project({".claude/project-config.json": {"project": {"stack": "react"}, "react": {"flavor": "next"}},
                         "package.json": pkg("react")}))
check("declared stack reported", dec["declared"] == {"stack": "react", "flavor": "next",
                                                     "source": ".claude/project-config.json"})
md = st.detect(project({"CLAUDE.md": "x <!-- fl-stack: shopify --> y"}))
check("legacy fl-stack marker read", md["declared"]["stack"] == "shopify")
for name in ("AGENTS.md", "GEMINI.md", "QWEN.md"):
    md = st.detect(project({name: "<!-- eden-stack: react -->"}))
    check(f"stack marker read from {name}", md["declared"]["stack"] == "react" and md["declared"]["source"] == name)
md = st.detect(project({"CLAUDE.md": "<!-- eden-stack: php -->", "AGENTS.md": "<!-- eden-stack: node -->"}))
check("CLAUDE.md first when several exist", md["declared"]["stack"] == "php")

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
