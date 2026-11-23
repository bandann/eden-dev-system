import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "hooks" / "eden_design.py"
spec = importlib.util.spec_from_file_location("eden_design", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

tmp = Path(tempfile.mkdtemp())
fake_brain = tmp / "eden-brain"
b = m.brain()
b.BRAIN = fake_brain
b.HOME = tmp / "home"
m.brain = lambda: b                      # every call sees the fake brain
m.NO_BRAIN_CACHE = tmp / "no-brain-cache"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def wj(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")
    return str(path)


# --- parse
p = m.parse_url("https://www.figma.com/design/AbCdEf1234567890/Client-Site?node-id=123-456&t=x")
check("parse file key + node", p["file_key"] == "AbCdEf1234567890" and p["node_id"] == "123:456")
check("parse encoded colon", m.parse_url("https://figma.com/file/AbCdEf1234567890/x?node-id=1%3A2")["node_id"] == "1:2")
check("parse no node", m.parse_url("https://figma.com/design/AbCdEf1234567890/x")["node_id"] == "")

# --- where: no brain at all -> eden-cache, never the repo
proj = tmp / "client-repo"
(proj / ".git").mkdir(parents=True)
d, root = m.cache_dir(str(proj))
check("no brain -> ~/.claude/eden-cache", d == m.NO_BRAIN_CACHE / "client-repo" and not (proj / ".claude").exists())
# global brain exists -> projects/{slug}/design
fake_brain.mkdir()
d, root = m.cache_dir(str(proj))
check("global brain -> projects/slug/design", d == fake_brain / "projects" / "client-repo" / "design")
# a legacy in-repo vault is ignored: the cache never lives in the client repo
(proj / ".claude" / "brain").mkdir(parents=True)
d, root = m.cache_dir(str(proj))
check("legacy vault ignored -> still projects/slug/design", d == fake_brain / "projects" / "client-repo" / "design")

# --- file state extraction
check("state from file data", m.file_state({"name": "Site", "lastModified": "2026-10-01T10:00:00Z", "version": "111"})
      == {"name": "Site", "last_modified": "2026-10-01T10:00:00Z", "version": "111"})
check("state from versions list", m.file_state({"versions": [{"id": "999", "created_at": "2026-10-02T00:00:00Z"}]})
      == {"version": "999", "last_modified": "2026-10-02T00:00:00Z"})
check("state nested", m.file_state({"file": {"lastModified": "T1"}}).get("last_modified") == "T1")
check("compare same", m.compare_state({"last_modified": "T1"}, {"last_modified": "T1"}) == "same")
check("compare changed", m.compare_state({"last_modified": "T1", "version": "1"}, {"last_modified": "T2", "version": "1"}) == "changed")
check("compare version fallback", m.compare_state({"version": "1"}, {"version": "2"}) == "changed")
check("compare unknown", m.compare_state({}, {"version": "2"}) == "unknown")

# --- save first time
url = "https://www.figma.com/design/AbCdEf1234567890/Client?node-id=10-20"
s1 = {"source": {"node_name": "Hero"}, "breakpoints": [390, 1440],
      "hero": {"title": {"390": {"font_size": 36}, "1440": {"font_size": 64}, "color": "token(--color-foreground)"},
               "button": {"1440": {"width": 180}}}}
shots = tmp / "shots"
shots.mkdir()
(shots / "desktop.png").write_bytes(b"\x89PNG")
meta1 = wj(tmp / "meta1.json", {"name": "Client", "lastModified": "T1", "version": "v1"})
r = m.cmd_save(d, root, wj(tmp / "s1.json", s1), "Hero", url, meta1, str(shots))
check("first save", r["ok"] and r["first_time"] and Path(r["spec"]).exists() and Path(r["md"]).exists())
check("md rendered", "font_size: 64" in Path(r["md"]).read_text(encoding="utf-8"))
check("shots copied + gitignored", (d / "shots" / "AbCdEf1234567890" / "10-20" / "desktop.png").exists()
      and "shots/" in (d / ".gitignore").read_text(encoding="utf-8"))

# --- lookup
lk = m.cmd_lookup(d, [url])
check("lookup by url hit", lk["cached"] and lk["section"] == "hero" and lk["file_state"]["last_modified"] == "T1")
check("lookup by section", m.cmd_lookup(d, ["hero"])["node_id"] == "10:20")
check("lookup by key+node (dash form)", m.cmd_lookup(d, ["AbCdEf1234567890", "10-20"])["cached"])
miss = m.cmd_lookup(d, ["https://www.figma.com/design/AbCdEf1234567890/Client?node-id=99-1"])
check("lookup other node miss lists cached", not miss["cached"] and "10:20" in miss["cached_nodes"])
check("lookup unknown file", m.cmd_lookup(d, ["https://www.figma.com/design/ZZZZZZZZZZZZ/x?node-id=1-1"])["reason"] == "file not cached")

# --- check-file
same = m.cmd_check_file(d, "AbCdEf1234567890", wj(tmp / "m.json", {"lastModified": "T1"}), "10-20")
check("check same -> no recheck", same["verdict"] == "same" and same["node_verdict"] == "same" and not same["nodes_to_recheck"])
chg = m.cmd_check_file(d, "AbCdEf1234567890", wj(tmp / "m2.json", {"lastModified": "T2"}), "10:20")
check("check changed -> recheck node", chg["verdict"] == "changed" and chg["nodes_to_recheck"] == ["10:20"])

# --- re-save identical spec at new state: same
r2 = m.cmd_save(d, root, wj(tmp / "s1b.json", s1), "Hero", url, wj(tmp / "m3.json", {"lastModified": "T2"}))
check("resave unchanged -> same", not r2["first_time"] and r2["same"])

# --- re-save modified spec: report deltas
s2 = json.loads(json.dumps(s1))
s2["hero"]["title"]["1440"]["font_size"] = 72
s2["hero"]["cta_secondary"] = {"1440": {"width": 160}}
del s2["hero"]["button"]
r3 = m.cmd_save(d, root, wj(tmp / "s2.json", s2), "Hero", url, wj(tmp / "m4.json", {"lastModified": "T3"}))
txt = "\n".join(r3["summary"])
check("diff changed", "~ hero.title.1440.font_size: 64 → 72" in txt)
check("diff added", "+ hero.cta_secondary.1440.width: 160" in txt)
check("diff removed", "- hero.button.1440.width: 180" in txt)
check("prev kept", (d / "specs" / "AbCdEf1234567890" / "10-20.prev.json").exists())
check("source not a design change", not any("source" in l for l in r3["summary"]))

# --- per-node state: saving node B at T4 must not make node A current
r4 = m.cmd_save(d, root, wj(tmp / "sb.json", {"source": {}, "footer": {"x": 1}}), "Footer",
                "https://www.figma.com/design/AbCdEf1234567890/Client?node-id=30-40", wj(tmp / "m5.json", {"lastModified": "T4"}))
c = m.cmd_check_file(d, "AbCdEf1234567890", wj(tmp / "m6.json", {"lastModified": "T4"}), "10:20")
check("older node still rechecked", c["verdict"] == "same" and c["node_verdict"] == "changed" and "30:40" in c["nodes_current"])

# --- list diff keyed by id
dl = m.diff_specs({"items": [{"id": "a", "w": 1}, {"id": "b", "w": 2}]}, {"items": [{"id": "b", "w": 2}, {"id": "a", "w": 3}]})
check("list keyed by id (order-insensitive)", len(dl["changed"]) == 1 and dl["changed"][0]["path"] == "items[a].w")

# --- status
st = m.cmd_status(d, root)
check("status", st["exists"] and st["files"][0]["nodes"] == 2 and st["sections"] == ["footer", "hero"])

# --- fingerprints (primary check, bridge only)
fk = "AbCdEf1234567890"
sec_url = "https://www.figma.com/design/AbCdEf1234567890/Client?node-id=50-1"  # a SECTION with 2 frames
fp1 = wj(tmp / "fp1.json", {"success": True, "result": {"fileKey": fk, "nodes": [
    {"id": "50:2", "hash": "aaaa"}, {"id": "50:3", "hash": "bbbb"}]}})
for nid, bp in (("50:2", 1440), ("50:3", 390)):
    m.cmd_save(d, root, wj(tmp / f"about-{bp}.json", {"source": {"file_key": fk, "node_id": nid},
               "about": {str(bp): {"gap": 24}}}), "About", None, None, None, fp1, "50-1")
al = m.cmd_lookup(d, [sec_url])
check("alias lookup returns both frames", al["cached"] and al["alias_of"] == "about"
      and sorted(al["check_nodes"]) == ["50:2", "50:3"] and al["frames"][0]["fingerprint"] in ("aaaa", "bbbb"))
same_fp = m.cmd_check_nodes(d, fk, fp1)
check("fingerprints same", same_fp["all_same"] and not same_fp["to_extract"])
fp2 = wj(tmp / "fp2.json", [{"id": "50:2", "hash": "aaaa"}, {"id": "50:3", "hash": "cccc"}, {"id": "77:7", "hash": "x"}])
chg_fp = m.cmd_check_nodes(d, fk, fp2)
check("one frame changed", chg_fp["nodes"] == {"50:2": "same", "50:3": "changed", "77:7": "not cached"}
      and chg_fp["to_extract"] == ["50:3", "77:7"])
js = m.main(["fingerprint-js", "50-2", "50:3"])
check("fingerprint-js fills ids", isinstance(js, str) and '["50:2", "50:3"]' in js and "__IDS__" not in js
      and "figma.getNodeByIdAsync" in js)

# --- disabled per project
(proj / ".claude" / "project-config.json").write_text('{"design_cache": {"enabled": false}}', encoding="utf-8")
out = m.main(["lookup", url, "--cwd", str(proj)])
check("disabled project skips cache", out.get("disabled") and not out["cached"])
(proj / ".claude" / "project-config.json").unlink()
check("enabled again", m.main(["lookup", url, "--cwd", str(proj)])["cached"])

# --- save without file key fails cleanly
try:
    m.cmd_save(d, root, wj(tmp / "bad.json", {"x": 1}))
    check("save needs key", False)
except SystemExit as e:
    check("save needs key", "file_key" in str(e))

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
