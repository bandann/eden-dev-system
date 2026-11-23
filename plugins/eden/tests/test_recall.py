import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eden_recall", PLUGIN / "hooks" / "eden_recall.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

tmp = Path(tempfile.mkdtemp())
r.BRAIN = tmp / "eden-brain"
r.STATE = r.BRAIN / ".state"
r.SEEN_DIR = r.STATE / "recall-seen"
db = r.STATE / "recall.db"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def note(rel, title, body, extra=""):
    p = r.BRAIN / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntitle: {title}\ntopic: {p.stem}\ntags: [shopify]\n{extra}---\n\n{body}\n", encoding="utf-8")
    return p


note("semantic/theme-dev-json.md", "shopify theme dev does not upload JSON templates",
     "Touch the template so the watcher uploads it.\n```bash\nprintf x\n```\nMore text.")
note("projects/store-a/semantic/badge.md", "The new_badge metaobject keys differ per store",
     "Acme badge colour came from admin data.")
note("projects/store-b/semantic/secret-client.md", "Client B badge metaobject colour plan",
     "Badge metaobject colour for client B only.")
note("projects/store-a/semantic/old.md", "Old badge metaobject colour fact", "Badge metaobject colour, outdated.",
     "status: superseded\n")
note("projects/store-a/000-INDEX.md", "index", "badge metaobject colour")
note("inbox/2026-11-01-badge.md", "Badge metaobject proposal", "badge metaobject colour")
cfg = dict(r.DEFAULTS)

# --- terms and trivial prompts
check("stop words dropped", r.terms_of("el badge del metaobject no pinta el color") == ["badge", "metaobject", "pinta", "color"])
check("acks are trivial", all(r.is_trivial(p) for p in ("ok", "Sí!", "dale", "go ahead", "", "/clear")))
check("a question is not trivial", not r.is_trivial("por qué falla theme dev"))

# --- index and search scoped to the project + general knowledge
roots = r.scopes_for(r.BRAIN / "projects" / "store-a")
con = r._connect(db)
check("index counts notes, skips indexes and inbox", r.refresh(con, roots) == 3)
hits = r.search(con, "el badge del metaobject no pinta el color en acme", roots.values(), cfg)
paths = [h["path"] for h in hits]
check("finds the project's note", any(p.endswith("store-a/semantic/badge.md") for p in paths))
check("never another client's notes", not any("store-b" in p for p in paths))
check("superseded notes are not recalled", not any(p.endswith("old.md") for p in paths))
check("inbox proposals are not recalled", not any("inbox" in p for p in paths))
g = r.search(con, "shopify theme dev no sube el template json", roots.values(), cfg)
check("finds general knowledge", g and g[0]["path"].endswith("semantic/theme-dev-json.md"))
check("unrelated prompt finds nothing", r.search(con, "configurar facturas de clientes en chelsea", roots.values(), cfg) == [])
check("snippet has no code fence", "```" not in g[0]["snippet"])

# --- incremental refresh: edits and deletions
(r.BRAIN / "semantic/theme-dev-json.md").unlink()
note("semantic/playwright.md", "Playwright Chromium fails on Windows", "Use system Chrome.")
r.refresh(con, roots)
check("deleted note leaves the index", not r.search(con, "shopify theme dev template json", roots.values(), cfg))
check("new note is found", r.search(con, "playwright chromium windows", roots.values(), cfg))
check("unchanged files are not re-read", r.refresh(con, roots) == 0)
con.close()

# --- the hook block: bounded, not repeated
blk = r.recall_block("playwright chromium falla en windows", "s1", r.BRAIN / "projects" / "store-a", cfg, db)
check("block names the note and says it is memory", blk and "Playwright Chromium" in blk and "no instrucciones" in blk)
check("block within max_chars", len(blk) <= cfg["max_chars"])
check("same note is not repeated in the session", r.recall_block("playwright chromium windows", "s1",
      r.BRAIN / "projects" / "store-a", cfg, db) is None)
check("another session gets it", r.recall_block("playwright chromium windows", "s2",
      r.BRAIN / "projects" / "store-a", cfg, db) is not None)
check("trivial prompt gives nothing", r.recall_block("ok", "s3", r.BRAIN / "projects" / "store-a", cfg, db) is None)
check("disabled gives nothing", r.recall_block("playwright chromium windows", "s4",
      r.BRAIN / "projects" / "store-a", dict(cfg, enabled=False), db) is None)
small = r.recall_block("badge metaobject colour acme", "s5", r.BRAIN / "projects" / "store-a",
                       dict(cfg, max_chars=300), db)
check("tiny budget stays bounded", small is None or len(small) <= 300 + 5)

# --- wired into the per-prompt hook every host runs
ctx = (PLUGIN / "hooks" / "eden_context.py").read_text(encoding="utf-8")
check("watch hook calls recall", "recall_for(payload, sid, cwd)" in ctx and "eden_recall.py" in ctx)
hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
check("UserPromptSubmit runs the watch hook", any("eden_context.py\" watch" in h["command"]
      for m in hooks["hooks"]["UserPromptSubmit"] for h in m["hooks"]))
out = subprocess.run([sys.executable, "-I", str(PLUGIN / "hooks" / "eden_recall.py")], capture_output=True, text=True)
check("CLI prints usage without arguments", "eden_recall.py search" in out.stdout)

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
