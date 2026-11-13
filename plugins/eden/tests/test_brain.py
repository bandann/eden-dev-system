import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "hooks" / "eden_brain.py"
spec = importlib.util.spec_from_file_location("eden_brain", SRC)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

tmp = Path(tempfile.mkdtemp())
b.BRAIN = tmp / "eden-brain"
b.STATE = b.BRAIN / ".state"
b.QUEUE = b.STATE / "queue"
b.LOGS = b.STATE / "logs"
b.STATUS = b.STATE / "distill_status.json"
b.QUARANTINE = b.STATE / "quarantine"
proj = tmp / "proj-brain"
header = {"project_brain": proj.as_posix(), "global_brain": b.BRAIN.as_posix()}
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def note(target, path, body="---\ntitle: x\n---\nhello", action="create"):
    return f"=== EDEN NOTE ===\ntarget: {target}\npath: {path}\naction: {action}\n---\n{body}\n=== END NOTE ===\n"


# good: two notes
out = "Resumen.\n" + note("project", "semantic/a.md") + note("inbox", "2026-10-22-b.md") + "=== EDEN RESULT: notes=2 ===\n"
ok, kind, w, q = b.apply_output(header, out)
check("good blocks written", ok and len(w) == 2 and (proj / "semantic/a.md").exists()
      and (b.BRAIN / "inbox/2026-10-22-b.md").exists())
check("content kept", (proj / "semantic/a.md").read_text(encoding="utf-8").endswith("hello\n"))

# none
check("none result ok", b.apply_output(header, "=== EDEN RESULT: none ===")[:2] == (True, "ok"))
# CRLF output
crlf = (note("project", "semantic/crlf.md") + "=== EDEN RESULT: notes=1 ===").replace("\n", "\r\n")
check("crlf ok", b.apply_output(header, crlf)[0] and (proj / "semantic/crlf.md").exists())

bad = {
    "dotdot": note("project", "../escape.md"),
    "absolute": note("project", "C:/x/abs.md"),
    "abs-posix": note("project", "/etc/abs.md"),
    "inbox subdir": note("inbox", "sub/x.md"),
    "dot folder": note("project", ".obsidian/x.md"),
    "underscore": note("project", "_templates/x.md"),
    "not md": note("project", "semantic/x.txt"),
    "bad target": note("global", "semantic/x.md"),
}
for name, blk in bad.items():
    ok, kind, w, q = b.apply_output(header, blk + "=== EDEN RESULT: notes=1 ===")
    check(f"reject {name}", not ok and kind == "format" and not w)
check("nothing escaped", not (tmp / "escape.md").exists())

# a bad block among good ones writes nothing
ok, kind, w, q = b.apply_output(header, note("project", "semantic/ok2.md") + bad["dotdot"] + "=== EDEN RESULT: notes=2 ===")
check("all-or-nothing", not ok and not (proj / "semantic/ok2.md").exists())
check("count mismatch", b.apply_output(header, note("project", "semantic/c.md") + "=== EDEN RESULT: notes=2 ===")[1] == "format")
check("no result line = format", b.apply_output(header, note("project", "semantic/d.md"))[1] == "format")
check("denied = permission", b.apply_output(header, "I need permission to write; Permission denied for that sensitive file.")[1] == "permission")

# secret quarantine
key = "ghp_" + "A" * 36
ok, kind, w, q = b.apply_output(header, note("project", "semantic/leak.md", f"token {key}") + note("project", "semantic/fine.md") + "=== EDEN RESULT: notes=2 ===")
check("secret quarantined", ok and len(q) == 1 and not (proj / "semantic/leak.md").exists() and (proj / "semantic/fine.md").exists())

# chunking
entries = [f"\n[DEV] pregunta {i} " + "x" * 300 if i % 3 == 0 else f"[CLAUDE] r{i} " + "y" * 300 for i in range(200)]
parts = b.split_parts(entries, 5000)
joined = "\n".join(parts)
check("chunks within limit", all(len(p) <= 5000 for p in parts) and len(parts) > 5)
check("nothing dropped", all(e.strip()[:12] in joined for e in entries))
check("cut before dev msg", sum(p.lstrip("\n").startswith("[DEV]") for p in parts[1:]) >= len(parts[1:]) - 1)
check("short session one part", b.split_parts(["a", "b"], 5000) == ["a\nb"])

# worktree root
main = tmp / "mainrepo"
(main / ".git" / "worktrees" / "wt1").mkdir(parents=True)
wt = tmp / "wt" / "wt1"
wt.mkdir(parents=True)
(wt / ".git").write_text(f"gitdir: {main.as_posix()}/.git/worktrees/wt1\n", encoding="utf-8")
check("worktree maps to main repo", b.project_root(wt).resolve() == main.resolve())
check("normal repo unchanged", b.project_root(main).resolve() == main.resolve())

# finish keeps item on failure, retires on success
b.QUEUE.mkdir(parents=True, exist_ok=True)
qf = b.QUEUE / "x.md"
qf.write_text("q", encoding="utf-8")
b.finish(qf, False, "format", [], [], "test", 0)
check("failure keeps queue item", qf.exists() and b.load_status()["last_error"]["kind"] == "format")
b.finish(qf, True, "ok", [], [], "test", 0)
check("success retires item", not qf.exists() and "last_error" not in b.load_status())

# prompt carries the part
hdr = {"part": 2, "parts": 3, "global_brain": "g", "project": "p", "project_brain": "pb",
       "project_brain_is_local": False, "date": "d", "session_id": "s", "branch": "b", "max_notes": 6}
pr = b.run_prompt(Path("q.md"), hdr)
check("prompt has part + protocol", "Tramo 2 de 3" in pr and "EDEN RESULT" in pr)

# no-window flag
check("NO_WINDOW set on windows", b.NO_WINDOW == 0x08000000)
src = SRC.read_text(encoding="utf-8")
check("no DETACHED_PROCESS / acceptEdits / Write tool", "0x00000008" not in src and "acceptEdits" not in src
      and '"Read,Write' not in src)

# --- tool-less provider (an API): session + notes travel inline, and the distill round trip works
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

b.eden_ai.CLAUDE_DIR = tmp  # never read the dev's real eden-config.json
pb = tmp / "inline-proj"
(pb / "semantic").mkdir(parents=True)
(pb / "semantic" / "old.md").write_text("---\ntitle: old\n---\nexisting fact", encoding="utf-8")
(b.BRAIN / "me").mkdir(parents=True, exist_ok=True)
(b.BRAIN / "me" / "style.md").write_text("---\ntitle: style\n---\nbody", encoding="utf-8")
(b.BRAIN / "projects" / "other").mkdir(parents=True, exist_ok=True)
(b.BRAIN / "projects" / "other" / "secret-client.md").write_text("other project", encoding="utf-8")
ihdr = dict(hdr, part=1, parts=1, project_brain=pb.as_posix(), global_brain=b.BRAIN.as_posix())
b.QUEUE.mkdir(parents=True, exist_ok=True)
iq = b.QUEUE / "inline-test.md"
iq.write_text("```json\n" + json.dumps(ihdr) + "\n```\n\n[DEV] siempre usa pnpm\n", encoding="utf-8")
ip = b.run_prompt(iq, ihdr, inline=True)
check("inline prompt carries the session", "[DEV] siempre usa pnpm" in ip and "léela completa" not in ip)
check("inline prompt carries project notes in full", "existing fact" in ip and "semantic/old.md" in ip)
check("inline prompt lists global notes, skips other projects", "me/style.md" in ip and "secret-client" not in ip)
check("default prompt stays path-based", "léela completa" in b.run_prompt(iq, ihdr) and "pnpm" not in b.run_prompt(iq, ihdr))

seen = {}


class FakeAPI(BaseHTTPRequestHandler):
    def do_POST(self):
        seen["prompt"] = json.loads(self.rfile.read(int(self.headers["content-length"])))["messages"][0]["content"]
        text = note("project", "semantic/pnpm.md", "---\ntitle: pnpm\n---\nuse pnpm") + "=== EDEN RESULT: notes=1 ===\n"
        out = json.dumps({"content": [{"type": "text", "text": text}]}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), FakeAPI)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["EDEN_TEST_KEY"] = "k"
icfg = dict(b.DEFAULTS, ai={"provider": "fake", "providers": {"fake": {
    "api": "anthropic", "base_url": f"http://127.0.0.1:{srv.server_port}", "api_key_env": "EDEN_TEST_KEY",
    "model": "m"}}})
ok = b.distill_one(iq, icfg)
srv.shutdown()
check("API distill writes the note and retires the item", ok and (pb / "semantic" / "pnpm.md").exists()
      and not iq.exists())
check("API received the inline session", "[DEV] siempre usa pnpm" in seen.get("prompt", ""))

iq.write_text("```json\n" + json.dumps(ihdr) + "\n```\n\nx\n", encoding="utf-8")
os.environ.pop("EDEN_TEST_KEY")
check("missing key keeps the item queued", not b.distill_one(iq, icfg) and iq.exists()
      and b.load_status()["last_error"]["kind"] == "missing_key")

# --- project key from the git remote (legacy folder-name brains keep their folder)
def repo_with(url, name="some-folder"):
    r = tmp / "repos" / name
    (r / ".git").mkdir(parents=True, exist_ok=True)
    (r / ".git" / "config").write_text(f'[core]\n\tbare = false\n[remote "origin"]\n\turl = {url}\n'
                                       '\tfetch = +refs/heads/*:refs/remotes/origin/*\n', encoding="utf-8")
    return r


for url in ("git@github.com:acme/shop-theme.git", "https://github.com/acme/shop-theme", "https://user:tok3n@github.com/acme/shop-theme.git",
            "ssh://git@gitlab.example.com:2222/acme/shop-theme.git"):
    check(f"remote key from {url.split('@')[-1][:30]}", b.remote_key(repo_with(url)) == "acme-shop-theme")
check("credentials never reach the key", "tok3n" not in (b.remote_key(repo_with("https://user:tok3n@github.com/acme/x")) or ""))
nr = tmp / "repos" / "no-remote"
(nr / ".git").mkdir(parents=True)
(nr / ".git" / "config").write_text("[core]\n", encoding="utf-8")
check("no remote: folder name", b.remote_key(nr) is None and b.project_slug(nr) == "no-remote")
r1, r2 = repo_with("git@github.com:acme/shop-theme.git", "clone-a"), repo_with("git@github.com:acme/shop-theme.git", "clone-b")
check("two clones of one repo share a brain", b.project_slug(r1) == b.project_slug(r2) == "acme-shop-theme")
check("same folder name, different repos: different brains",
      b.project_slug(repo_with("git@github.com:acme/site.git", "web")) != b.project_slug(repo_with("git@github.com:other/site.git", "web2")))
legacy = repo_with("git@github.com:acme/legacy-app.git", "legacy-folder")
(b.BRAIN / "projects" / "legacy-folder").mkdir(parents=True, exist_ok=True)
check("an existing folder-name brain is kept (nothing renamed)", b.project_slug(legacy) == "legacy-folder")

# --- one topic, one note: a new note on an existing topic updates that note
tb = tmp / "topic-brain"
(tb / "semantic").mkdir(parents=True)
(tb / "semantic" / "theme-check.md").write_text("---\ntitle: old\ntopic: theme-check-ignores\n---\nold body\n", encoding="utf-8")
th = {"project_brain": tb.as_posix(), "global_brain": b.BRAIN.as_posix()}
out = note("project", "semantic/theme-check-config.md", "---\ntitle: new\ntopic: theme-check-ignores\n---\nnew body") \
    + note("project", "semantic/other.md", "---\ntitle: other\ntopic: something-else\n---\nx") + "=== EDEN RESULT: notes=2 ===\n"
ok, kind, w, q = b.apply_output(th, out)
check("same topic merged into the existing note", ok and (tb / "semantic" / "theme-check.md").read_text(encoding="utf-8").endswith("new body\n")
      and not (tb / "semantic" / "theme-check-config.md").exists())
check("a new topic is a new note", (tb / "semantic" / "other.md").exists())
check("note_topic reads the frontmatter only", b.note_topic("---\ntopic: a-b\n---\ntopic: not-this") == "a-b"
      and b.note_topic("no frontmatter") is None)

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
