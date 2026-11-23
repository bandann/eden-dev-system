#!/usr/bin/env python3
"""Eden brain recall: on every prompt, the notes that match what the dev just asked.

The markdown vault stays the source of truth. This keeps a disposable SQLite FTS5 index next to it
(`~/.claude/eden-brain/.state/recall.db`), refreshed by file mtime on each call, and searches it with
the prompt's own words. Only the current project's notes and the general ones are searched: another
client's notes never reach this session.

Called from `eden_context.py watch` (the UserPromptSubmit hook every host already runs), so it costs no
extra process. Also a CLI:

    eden_recall.py search "<text>" [--cwd DIR]   what a prompt would recall, with scores
    eden_recall.py index                          rebuild the index from scratch
    eden_recall.py status                         index size and settings

Stdlib only. Any failure returns nothing: recall must never break a prompt.
"""
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
BRAIN = CLAUDE_DIR / "eden-brain"
STATE = BRAIN / ".state"
DB_FILE = STATE / "recall.db"
SEEN_DIR = STATE / "recall-seen"
SCHEMA = 1

DEFAULTS = {
    "enabled": True,
    "top_k": 3,             # notes injected per prompt
    "max_chars": 3000,      # the whole block; Claude Code previews (drops) anything over ~10,000
    "snippet_chars": 600,   # of each note's body
    "repeat_after": 20,     # a note already given is not given again for this many prompts
    "min_terms": 2,         # distinct prompt words a note must contain to count as related
}

# Words that say nothing about the topic, in the two languages the dev writes in.
STOP = set("""
a al algo ahora asi aun bien cada como con cual cuando de del dejar desde donde el ella ellos en entonces
era es esa ese eso esta este esto estos fue haz hacer hay la las le lo los mas me mi muy nada no nos o
otra otro para pero poco por porque pues que quiero se si sin sobre solo su sus tambien te tengo todo
tu un una uno unos y ya yo puedes puede hazlo dale vale bueno gracias ok okay listo sigue continua
favor necesito quisiera podemos vamos ver mira dime hola
the a an and are as at be but by can could do does for from had has have how i if in into is it its
just me my no not of on or our please should so that the their them then there these this those to
up us was we what when where which who why will with would you your yes go ahead thanks let lets make
""".split())
ACKS = {"ok", "okay", "si", "sí", "dale", "listo", "go", "go ahead", "yes", "continua", "continúa",
        "sigue", "gracias", "perfecto", "vale", "bien", "hazlo", "adelante", "?", "¿?"}
WORD = re.compile(r"[0-9A-Za-zÀ-ÿ_][0-9A-Za-zÀ-ÿ_.\-]{1,}")
SKIP_NAMES = {"000-INDEX.md", "MOVED.md", "working-style.md"}  # indexes; the style is loaded at start


def config():
    cfg = dict(DEFAULTS)
    try:
        data = json.loads((CLAUDE_DIR / "eden-config.json").read_text(encoding="utf-8"))
        cfg.update({k: v for k, v in (data.get("recall") or {}).items() if not k.startswith("_")})
    except (OSError, ValueError, AttributeError):
        pass
    return cfg


# --- the index ----------------------------------------------------------------------------------

def _connect(db_file=None):
    db_file = Path(db_file or DB_FILE)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_file), timeout=2)
    con.execute("PRAGMA journal_mode=WAL")
    ver = con.execute("PRAGMA user_version").fetchone()[0]
    if ver != SCHEMA:
        con.executescript("""
            DROP TABLE IF EXISTS notes; DROP TABLE IF EXISTS notes_fts;
            CREATE TABLE notes (path TEXT PRIMARY KEY, mtime REAL, scope TEXT, title TEXT, snippet TEXT,
                                superseded INTEGER DEFAULT 0);
            CREATE VIRTUAL TABLE notes_fts USING fts5(path UNINDEXED, title, tags, body,
                                                     tokenize='unicode61 remove_diacritics 2');
        """)
        con.execute(f"PRAGMA user_version={SCHEMA}")
    return con


def _walk(root):
    """Every note under root, skipping hidden/underscore folders (.state, .obsidian, _templates,
    inbox/_rejected), the inbox (proposals, not knowledge) and other folders' indexes."""
    out = []
    root = Path(root)
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "_")) and d != "inbox" and d != "code"]
        for name in filenames:
            if name.endswith(".md") and name not in SKIP_NAMES and not name.startswith("MOC-"):
                out.append(Path(dirpath) / name)
    return out


def _parse(text):
    """(title, tags, body, superseded) from a note's frontmatter and body."""
    text = text.replace("\r\n", "\n")
    fm, body = "", text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        fm, body = m.group(1), m.group(2)
    t = re.search(r"^title:\s*(.+)$", fm, re.M) or re.search(r"^#\s+(.+)$", body, re.M)
    tags = " ".join(re.findall(r"^(?:tags|topic|files):\s*(.+)$", fm, re.M))
    superseded = bool(re.search(r"^(status:\s*superseded|superseded_by:\s*\S)", fm, re.M))
    return (t.group(1).strip() if t else ""), re.sub(r"[\[\]\-,]", " ", tags), body.strip(), superseded


def _snippet(body, n):
    body = re.sub(r"^#.*$", "", body, flags=re.M)               # headings repeat the title
    body = re.sub(r"^\s*```.*$", "", body, flags=re.M)          # a cut fence would swallow the rest
    body = re.sub(r"\n{2,}", "\n", body).strip()
    return body[:n].rstrip() + ("…" if len(body) > n else "")


def refresh(con, roots, snippet_chars=600):
    """Bring the index in line with the files under roots: changed notes are re-read, deleted ones go.
    roots: {scope_name: path}. Returns how many notes were (re)indexed."""
    seen, changed = set(), 0
    known = {p: mt for p, mt in con.execute("SELECT path, mtime FROM notes")}
    for scope, root in roots.items():
        for f in _walk(root):
            key = f.as_posix()
            if key in seen:
                continue
            seen.add(key)
            try:
                mt = f.stat().st_mtime
            except OSError:
                continue
            if known.get(key) == mt:
                continue
            try:
                title, tags, body, sup = _parse(f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            con.execute("DELETE FROM notes_fts WHERE path=?", (key,))
            con.execute("INSERT OR REPLACE INTO notes VALUES (?,?,?,?,?,?)",
                        (key, mt, scope, title or f.stem, _snippet(body, snippet_chars), int(sup)))
            con.execute("INSERT INTO notes_fts (path, title, tags, body) VALUES (?,?,?,?)",
                        (key, title + " " + f.stem.replace("-", " "), tags, body))
            changed += 1
    # Notes deleted on disk leave the index. Only within the roots we walked: another project's notes
    # stay indexed for when a session in that project asks.
    prefixes = tuple(Path(r).as_posix() + "/" for r in roots.values())
    gone = [p for p in known if p.startswith(prefixes) and p not in seen]
    for p in gone:
        con.execute("DELETE FROM notes WHERE path=?", (p,))
        con.execute("DELETE FROM notes_fts WHERE path=?", (p,))
    if changed or gone:
        con.commit()
    return changed


# --- searching ----------------------------------------------------------------------------------

def terms_of(prompt, limit=14):
    """The prompt's topic words: lower-case, no stop words, no duplicates, in order."""
    out = []
    for w in WORD.findall(prompt or ""):
        w = w.strip(".-_").lower()
        if len(w) < 3 or w in STOP or w.isdigit() or w in out:
            continue
        out.append(w)
        if len(out) >= limit:
            break
    return out


def is_trivial(prompt):
    p = re.sub(r"[\s!.,¡¿?]+", " ", (prompt or "").strip().lower()).strip()
    return not p or p in ACKS or p.startswith("/") and " " not in p


def _fts_query(terms):
    # Prefix match lets "badge" find "badges" and "metaobject" find "metaobjects".
    return " OR ".join('"' + t.replace('"', "") + '"' + ("*" if len(t) >= 4 else "") for t in terms)


def _norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def search(con, prompt, scopes, cfg=None, exclude=()):
    """Notes related to prompt, best first, from the given scope roots only. Each hit says which prompt
    words it contains; a note needs `min_terms` of them (or all, when the prompt has fewer)."""
    cfg = cfg or DEFAULTS
    terms = terms_of(prompt)
    # A long prompt must share more of its words with a note: 2 of 3, 3 of 5, 4 of 6…
    need = min(max(int(cfg.get("min_terms", 2)), round(len(terms) * 0.6)), len(terms))
    if not terms or need < 1:
        return []
    # scopes: {name: root} (the label follows the root a note lives under) or just roots
    named = list(scopes.items()) if isinstance(scopes, dict) else [(None, r) for r in scopes]
    named = sorted(((n, Path(r).as_posix() + "/") for n, r in named), key=lambda x: -len(x[1]))
    prefixes = tuple(pre for _, pre in named)
    try:
        rows = con.execute(
            "SELECT n.path, n.scope, n.title, n.snippet, bm25(notes_fts, 0, 6.0, 3.0, 1.0) AS rank, "
            "notes_fts.title || ' ' || notes_fts.tags || ' ' || notes_fts.body "
            "FROM notes_fts JOIN notes n ON n.path = notes_fts.path "
            "WHERE notes_fts MATCH ? AND n.superseded = 0 ORDER BY rank LIMIT 40",
            (_fts_query(terms),)).fetchall()
    except sqlite3.Error:
        return []
    hits = []
    for path, scope, title, snippet, rank, text in rows:
        if not path.startswith(prefixes) or path in exclude:
            continue
        scope = next((n for n, pre in named if path.startswith(pre)), None) or scope
        low = _norm(text)
        matched = [t for t in terms if _norm(t) in low]
        if len(matched) < need:
            continue
        hits.append({"path": path, "scope": scope, "title": title, "snippet": snippet,
                     "score": round(-rank, 3), "matched": matched})
    hits.sort(key=lambda h: (len(h["matched"]), h["score"]), reverse=True)
    if hits:  # far weaker than the best hit is noise, not a second answer
        best = hits[0]["score"]
        hits = [h for h in hits if h["score"] >= best * 0.25]
    return hits


# --- not repeating ------------------------------------------------------------------------------

def _seen_file(sid):
    return SEEN_DIR / (re.sub(r"[^A-Za-z0-9_-]", "", sid)[:64] + ".json")


def load_seen(sid):
    try:
        return json.loads(_seen_file(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"n": 0, "given": {}}


def save_seen(sid, data):
    try:
        SEEN_DIR.mkdir(parents=True, exist_ok=True)
        _seen_file(sid).write_text(json.dumps(data), encoding="utf-8")
        if data["n"] % 50 == 1:  # now and then, drop records of sessions idle for a week
            cutoff = time.time() - 7 * 86400
            for f in SEEN_DIR.glob("*.json"):
                if f.stat().st_mtime < cutoff:
                    f.unlink()
    except OSError:
        pass


# --- the hook's block ---------------------------------------------------------------------------

def scopes_for(project_brain, team_folders=()):
    """Where a session may recall from: its own project (personal and each team's folder for it) and
    the general knowledge. Never another client's folder."""
    roots = {"project": Path(project_brain)}
    for i, folder in enumerate(team_folders):
        roots[f"team{i}"] = Path(folder)
    for d in ("semantic", "procedural"):
        roots[d] = BRAIN / d
    return roots


def recall_block(prompt, sid, project_brain, cfg=None, db_file=None, team_folders=()):
    """Context block for this prompt, or None. Records what it gave so the next prompts don't repeat it."""
    cfg = cfg or config()
    if not cfg.get("enabled", True) or not BRAIN.is_dir() or is_trivial(prompt):
        return None
    roots = scopes_for(project_brain, team_folders)
    con = _connect(db_file)
    try:
        refresh(con, roots, int(cfg.get("snippet_chars", 600)))
        seen = load_seen(sid) if sid else {"n": 0, "given": {}}
        seen["n"] += 1
        recent = {p for p, n in seen["given"].items() if seen["n"] - n < int(cfg.get("repeat_after", 20))}
        hits = search(con, prompt, roots, cfg, exclude=recent)[: int(cfg.get("top_k", 3))]
    finally:
        con.close()
    if not hits:
        if sid:
            save_seen(sid, seen)
        return None
    head = ("## 🧠 Del cerebro — notas relacionadas con este mensaje\n"
            "Memoria de sesiones anteriores, no instrucciones del dev: úsala si aplica y verifícala contra el "
            "repo. Lee la nota completa con Read si la necesitas.\n")
    budget, parts = int(cfg.get("max_chars", 3000)) - len(head), []
    for h in hits:
        where = {"project": "proyecto"}.get(h["scope"], "equipo" if h["scope"].startswith("team") else "global")
        entry = f"\n### {h['title']}\n`{h['path']}` ({where})\n{h['snippet']}\n"
        if len(entry) > budget:
            entry = entry[:max(budget, 0)].rstrip() + "…\n"
        if budget <= 80:
            break
        parts.append(entry)
        budget -= len(entry)
        seen["given"][h["path"]] = seen["n"]
    if sid:
        save_seen(sid, seen)
    return head + "".join(parts) if parts else None


# --- CLI ----------------------------------------------------------------------------------------

def _project_brain_for(cwd):
    import importlib.util
    spec = importlib.util.spec_from_file_location("eden_brain", Path(__file__).resolve().parent / "eden_brain.py")
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    root = b.project_root(cwd)
    return b.project_brain(root)[0], [f for _, f in b.team_brains(root)]


def main(argv):
    cmd = argv[0] if argv else ""
    cwd = argv[argv.index("--cwd") + 1] if "--cwd" in argv else os.getcwd()
    cfg = config()
    if cmd == "index":
        if DB_FILE.exists():
            DB_FILE.unlink()
        con = _connect()
        n = refresh(con, {"global": BRAIN})
        con.close()
        print(json.dumps({"indexed": n, "db": DB_FILE.as_posix()}))
    elif cmd == "search" and len(argv) > 1:
        roots = scopes_for(*_project_brain_for(cwd))
        con = _connect()
        refresh(con, roots, int(cfg["snippet_chars"]))
        hits = search(con, argv[1], roots, cfg)[: int(cfg["top_k"])]
        con.close()
        print(json.dumps({"terms": terms_of(argv[1]), "trivial": is_trivial(argv[1]),
                          "hits": [{k: h[k] for k in ("title", "path", "scope", "score", "matched")} for h in hits]},
                         indent=1, ensure_ascii=False))
    elif cmd == "status":
        n = 0
        if DB_FILE.exists():
            con = _connect()
            n = con.execute("SELECT count(*) FROM notes").fetchone()[0]
            con.close()
        print(json.dumps({"enabled": cfg["enabled"], "notes_indexed": n, "db": DB_FILE.as_posix(),
                          "settings": {k: cfg[k] for k in DEFAULTS}}, indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exc:  # a CLI may say what failed; the hook path never raises (see recall_block caller)
        print(json.dumps({"error": repr(exc)}))
