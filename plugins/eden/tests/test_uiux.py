import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eden_uiux", PLUGIN / "scripts" / "eden_uiux.py")
ux = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ux)
os.environ.pop("EDEN_UIUX_PATH", None)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def fake_install(base, version, echo="UIUX"):
    """A stand-in for UI/UX Pro Max: search.py echoes its args, sibling module import included."""
    scripts = base / ".claude" / "skills" / "ui-ux-pro-max" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "core.py").write_text(f"TAG = {echo!r}\n", encoding="utf-8")
    (scripts / "search.py").write_text("import sys\nfrom core import TAG\nprint(TAG, ' '.join(sys.argv[1:]))\n",
                                       encoding="utf-8")
    (base / ".claude-plugin").mkdir(parents=True)
    (base / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    return scripts / "search.py"


home, proj = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
check("nothing installed -> None", ux.locate(proj, home) is None)

# Claude Code plugin install (cache/<marketplace>/ui-ux-pro-max/<version>/...), two versions
cache = home / ".claude" / "plugins" / "cache" / "ui-ux-pro-max-skill" / "ui-ux-pro-max"
fake_install(cache / "2.14.0", "2.14.0", "OLD")
newest = fake_install(cache / "2.15.0", "2.15.0", "NEW")
found = ux.locate(proj, home)
check("finds the plugin install, newest version", found == newest and ux.version_of(found) == "2.15.0")

# a `uipro init` style install in another tool's skills folder is found too
other = Path(tempfile.mkdtemp())
s = other / ".cursor" / "skills" / "ui-ux-pro-max" / "scripts"
s.mkdir(parents=True)
(s / "search.py").write_text("print('cursor copy')\n", encoding="utf-8")
check("finds a skills-folder install of another tool", ux.locate(None, other) == s / "search.py")

# --- the consent gate and the write guard
code, out = ux.run(["x", "--design-system"], proj, approved=False, search_py=newest)
check("refuses without --approved, says to ask the dev", code == 2 and "sí del dev" in out)
for bad in (["x", "--persist"], ["x", "--force"], ["x", "--output-dir", "/p"], ["x", "--output-dir=/p"], ["x", "-o", "/p"]):
    code, out = ux.run(bad, proj, approved=True, search_py=newest)
    check(f"refuses {bad[1]} (never writes into the project)", code == 2 and "no escribe en el proyecto" in out)
code, out = ux.run(["x"], proj, approved=True, search_py=None)
check("not installed: install hint, no run", code == 3 and "ui-ux-pro-max-skill" in out) if ux.locate(proj) is None else None

# --- an approved run passes the args through and can save to .claude/context
code, out = ux.run(["spa wellness", "--design-system", "-p", "Serenity"], proj, approved=True, save="Hero Spa!",
                   search_py=newest)
check("approved run executes the installed tool (sibling imports work)", code == 0 and out.startswith("NEW spa wellness --design-system"))
saved = list((proj / ".claude" / "context").glob("uiux-*-hero-spa.md"))
check("--save writes only to .claude/context, slugged", len(saved) == 1 and "NEW spa wellness" in saved[0].read_text(encoding="utf-8"))
check("nothing else written in the project", sorted(p.name for p in proj.iterdir()) == [".claude"])

# --- stack map and the project's mode
check("stack map", ux.stack_for("react", "next") == "nextjs" and ux.stack_for("php", "laravel") == "laravel"
      and ux.stack_for("mobile", "react-native") == "react-native" and ux.stack_for("shopify") == "html-tailwind"
      and ux.stack_for("node", "express") == "")
check("mode defaults to ask", ux.mode(proj) == "ask")
(proj / ".claude" / "project-config.json").write_text(json.dumps({"uiux": {"mode": "off"}}), encoding="utf-8")
check("mode off is honoured", ux.mode(proj) == "off")
(proj / ".claude" / "project-config.json").write_text(json.dumps({"uiux": {"mode": "auto"}}), encoding="utf-8")
check("there is no automatic mode (falls back to ask)", ux.mode(proj) == "ask")

# --- the skill can only be invoked by the dev, and the flows only propose it
skill = (PLUGIN / "skills" / "uiux-pro" / "SKILL.md").read_text(encoding="utf-8")
check("skill: model can't invoke it on its own", "disable-model-invocation: true" in skill)
check("skill: always --approved after the dev's yes", "run --approved" in skill and "nunca corre sin un sí" in skill.lower())
for rel in ("skills/ignition-task/SKILL.md", "skills/create-new-section/SKILL.md", "skills/section-mod/SKILL.md",
            "skills/create-fundaments/SKILL.md"):
    t = (PLUGIN / rel).read_text(encoding="utf-8")
    check(f"{rel.split('/')[1]}: proposes and waits", "uiux-pro" in t and ("espera" in t))

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
