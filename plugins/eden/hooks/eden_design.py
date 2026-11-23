"""Eden design cache — a project's Figma, measured once and remembered.

The first extraction of a Figma section is saved as a Design Spec (JSON, plus a readable .md) in the
project's memory. Next time the same link comes up, one cheap call tells whether the node changed:
a read-only script run through the Desktop Bridge (figma-fingerprint.js) returns a short hash per
node — no REST token needed, and exact per node.
  - same    → the saved spec is used, nothing else is read from Figma;
  - changed → only that node is extracted again, and `save` reports what is new or modified.

Usage: python -I eden_design.py <command> [args] [--cwd DIR]
  where                                 cache folder for the project
  parse <url>                           file_key, node_id (API form) and the url's node-id
  lookup <url | file_key [node_id] | section>
                                        is it cached, from which state, and where the spec is
  fingerprint-js <node_id…>             the JS to run with figma_execute (read-only)
  check-nodes <file_key> <fp.json>      compare that run's hashes with the cached ones (primary check)
  check-file <file_key> <meta.json> [node_id]
                                        compare the file's lastModified/version with the state each
                                        cached node was extracted from
  save <spec.json> [--section S] [--url U] [--meta meta.json] [--shots DIR] [--fingerprint fp.json|hash]
       [--alias LINK_NODE]
                                        store a spec; prints the diff against the previous one
  diff <old.json> <new.json>            what changed between two specs
  status                                what the cache holds
Stdlib only. Prints JSON. Never contacts Figma: the skills call the MCP and hand the results over.
"""
import importlib.util
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = Path(__file__).resolve().parent
SCHEMA_SPEC = "eden-design-spec/1"
SCHEMA_CACHE = "eden-design-cache/1"
NO_BRAIN_CACHE = Path.home() / ".claude" / "eden-cache" / "design"


def brain():
    """eden_brain.py resolves projects and brains; one source of truth (python -I can't import siblings)."""
    spec = importlib.util.spec_from_file_location("eden_brain", HERE / "eden_brain.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- where ------------------------------------------------------------------------------------

def cache_dir(cwd=None):
    """The project's folder in the global brain (`design/`); without a brain,
    ~/.claude/eden-cache/design/{project}. Never inside the client repo."""
    b = brain()
    root = b.project_root(cwd or os.getcwd())
    pbrain, is_local = b.project_brain(root)
    if is_local or b.BRAIN.is_dir():
        return pbrain / "design", root
    return NO_BRAIN_CACHE / b.project_slug(root), root


def disabled(root):
    """The project turned the cache off: .claude/project-config.json → design_cache.enabled: false."""
    try:
        cfg = json.loads((root / ".claude" / "project-config.json").read_text(encoding="utf-8"))
        return (cfg.get("design_cache") or {}).get("enabled") is False
    except (OSError, ValueError, AttributeError):
        return False


def load_manifest(d):
    try:
        return json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema": SCHEMA_CACHE, "files": {}, "sections": {}}


def save_manifest(d, data):
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# --- parse ------------------------------------------------------------------------------------

FILE_KEY = re.compile(r"/(?:design|file|proto|board|make)/([A-Za-z0-9]{10,})")


def parse_url(url):
    u = urlparse(url.strip())
    m = FILE_KEY.search(u.path)
    raw = (parse_qs(u.query).get("node-id") or [""])[0]
    node = unquote(raw).replace("-", ":") if raw else ""
    return {"file_key": m.group(1) if m else "", "node_id": node, "url_node_id": raw,
            "url": url.strip()}


def norm_node(node):
    return (node or "").replace("-", ":")


# --- file state -------------------------------------------------------------------------------

def file_state(meta):
    """Pull lastModified/version out of whatever the Figma tool returned (file data or versions list)."""
    if not isinstance(meta, dict):
        return {}
    found = {}

    def walk(x, depth=0):
        if depth > 3 or not isinstance(x, dict):
            return
        for k, v in x.items():
            kl = k.lower()
            if kl in ("lastmodified", "last_modified") and isinstance(v, str):
                found.setdefault("last_modified", v)
            elif kl in ("version", "version_id", "versionid") and isinstance(v, (str, int)):
                found.setdefault("version", str(v))
            elif kl == "name" and depth == 0 and isinstance(v, str):
                found.setdefault("name", v)
            elif isinstance(v, dict):
                walk(v, depth + 1)
        versions = x.get("versions")
        if isinstance(versions, list) and versions and isinstance(versions[0], dict):
            found.setdefault("version", str(versions[0].get("id", "")))
            found.setdefault("last_modified", versions[0].get("created_at", ""))

    walk(meta)
    return {k: v for k, v in found.items() if v}


def compare_state(cached, current):
    """same | changed | unknown. lastModified moves on every edit; version only on saved versions."""
    if not cached or not current:
        return "unknown"
    if cached.get("last_modified") and current.get("last_modified"):
        return "same" if cached["last_modified"] == current["last_modified"] else "changed"
    if cached.get("version") and current.get("version"):
        return "same" if cached["version"] == current["version"] else "changed"
    return "unknown"


# --- diff -------------------------------------------------------------------------------------

VOLATILE = {"source"}  # who/when extracted: not a design change


def flatten(x, prefix=""):
    out = {}
    if isinstance(x, dict):
        for k, v in x.items():
            if not prefix and k in VOLATILE:
                continue
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(x, list):
        keyed = all(isinstance(i, dict) and ("id" in i or "name" in i) for i in x) and x
        for i, v in enumerate(x):
            key = str(v.get("id", v.get("name"))) if keyed else str(i)
            out.update(flatten(v, f"{prefix}[{key}]"))
    else:
        out[prefix] = x
    return out


def diff_specs(old, new):
    a, b = flatten(old or {}), flatten(new or {})
    changed = [{"path": k, "from": a[k], "to": b[k]} for k in sorted(a.keys() & b.keys()) if a[k] != b[k]]
    added = [{"path": k, "value": b[k]} for k in sorted(b.keys() - a.keys())]
    removed = [{"path": k, "value": a[k]} for k in sorted(a.keys() - b.keys())]
    return {"same": not (changed or added or removed), "changed": changed, "added": added, "removed": removed}


def diff_lines(d, limit=60):
    """Human summary of a diff, one line per change (the skill translates it for the dev)."""
    lines = [f"~ {c['path']}: {c['from']} → {c['to']}" for c in d["changed"]]
    lines += [f"+ {c['path']}: {c['value']}" for c in d["added"]]
    lines += [f"- {c['path']}: {c['value']}" for c in d["removed"]]
    return lines[:limit] + ([f"… {len(lines) - limit} more"] if len(lines) > limit else [])


# --- markdown rendering -----------------------------------------------------------------------

def scalar(v):
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False) if (not v or re.search(r"[:#{}\[\],&*!|>'\"%@`]|^\s|\s$", v)) else v
    return json.dumps(v, ensure_ascii=False)


def yaml_lines(x, indent=0):
    pad = "  " * indent
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                out += yaml_lines(v, indent + 1)
            else:
                out.append(f"{pad}{k}: {scalar(v) if not isinstance(v, (dict, list)) else json.dumps(v)}")
    elif isinstance(x, list):
        for v in x:
            if isinstance(v, (dict, list)) and v:
                sub = yaml_lines(v, indent + 1)
                out.append(f"{pad}- {sub[0].strip()}")
                out += sub[1:]
            else:
                out.append(f"{pad}- {scalar(v)}")
    return out


def render_md(spec, section):
    src = spec.get("source", {})
    head = [f"# Design Spec — {section}", "",
            f"Cached from Figma `{src.get('file_key', '?')}` node `{src.get('node_id', '?')}` · extracted "
            f"{src.get('extracted', '?')} · file state {src.get('last_modified') or src.get('version') or 'unknown'}.",
            "Generated from the .json next to it by eden_design.py — do not edit by hand; re-extract instead.",
            "", "```yaml"]
    return "\n".join(head + yaml_lines(spec) + ["```", ""])


# --- commands ---------------------------------------------------------------------------------

def section_slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "section"


def entry_view(d, man, fkey, node, entry):
    sec = entry.get("section")
    f = man["files"].get(fkey, {})
    return {"cached": True, "file_key": fkey, "node_id": node, "section": sec,
            "spec": (d / entry["spec"]).as_posix(), "md": (d / entry["md"]).as_posix(),
            "shots": [(d / s).as_posix() for s in entry.get("shots", [])],
            "extracted": entry.get("extracted"), "fingerprint": entry.get("fingerprint"),
            "file_state": entry.get("file_state", {}),
            "file_checked": f.get("checked"), "section_nodes": man["sections"].get(sec, {}).get("nodes", [])}


def cmd_lookup(d, args):
    man = load_manifest(d)
    first = args[0] if args else ""
    if "figma.com" in first:
        p = parse_url(first)
        fkey, node = p["file_key"], p["node_id"]
    elif len(args) >= 2 or (first and first not in man["sections"]):
        fkey, node = first, norm_node(args[1] if len(args) > 1 else "")
    else:  # a section name
        sec = man["sections"].get(first)
        if not sec:
            return {"cached": False, "reason": "unknown section"}
        fkey, node = sec["nodes"][0].split("|", 1)
    f = man["files"].get(fkey)
    if not f:
        return {"cached": False, "file_key": fkey, "node_id": node, "reason": "file not cached"}
    if not node:
        return {"cached": False, "file_key": fkey, "reason": "no node-id in the link",
                "cached_nodes": {n: e.get("section") for n, e in f["nodes"].items()}}
    entry = f["nodes"].get(node)
    alias = man.get("aliases", {}).get(f"{fkey}|{node}")
    if not entry and alias in man["sections"]:
        # the link points at a container (a Figma SECTION, a page group) whose frames were cached
        nodes = man["sections"][alias]["nodes"]
        views = [entry_view(d, man, *k.split("|", 1), f["nodes"][k.split("|", 1)[1]])
                 for k in nodes if k.split("|", 1)[1] in f["nodes"]]
        return {"cached": bool(views), "file_key": fkey, "node_id": node, "alias_of": alias,
                "section": alias, "frames": views, "check_nodes": [v["node_id"] for v in views]}
    if not entry:
        # a child of a cached frame isn't cached on its own: the skill decides whether to extract it
        return {"cached": False, "file_key": fkey, "node_id": node, "reason": "node not cached",
                "cached_nodes": {n: e.get("section") for n, e in f["nodes"].items()}}
    return entry_view(d, man, fkey, node, entry)


def fingerprints(data):
    """{node_id: hash} from the figma_execute result of figma-fingerprint.js (raw or wrapped)."""
    if isinstance(data, dict):
        data = data.get("result", data)
        data = data.get("nodes", data) if isinstance(data, dict) else data
    return {norm_node(n["id"]): n.get("hash") for n in data or [] if isinstance(n, dict) and n.get("id")}


def cmd_check_nodes(d, fkey, fp_file):
    """The primary check: each cached node's fingerprint against the one just taken in Figma.
    Needs only the Desktop Bridge (no REST token) and is exact per node."""
    man = load_manifest(d)
    current = fingerprints(json.loads(Path(fp_file).read_text(encoding="utf-8")))
    f = man["files"].get(fkey, {"nodes": {}})
    verdicts = {}
    for node, h in current.items():
        e = f["nodes"].get(node)
        verdicts[node] = ("not cached" if not e else "unknown" if not e.get("fingerprint") or not h
                          else "same" if e["fingerprint"] == h else "changed")
    if fkey in man["files"]:
        f["checked"] = datetime.now().isoformat(timespec="seconds")
        save_manifest(d, man)
    return {"file_key": fkey, "nodes": verdicts,
            "all_same": bool(verdicts) and all(v == "same" for v in verdicts.values()),
            "to_extract": sorted(n for n, v in verdicts.items() if v != "same")}


def cmd_check_file(d, fkey, meta_file, node=None):
    """Each node is judged against the file state IT was extracted from: a later save of another node
    moves the file's state forward without making older nodes current."""
    man = load_manifest(d)
    current = file_state(json.loads(Path(meta_file).read_text(encoding="utf-8")))
    f = man["files"].get(fkey)
    verdict = compare_state((f or {}).get("state"), current)
    nodes = {n: compare_state(e.get("file_state"), current) for n, e in (f or {}).get("nodes", {}).items()}
    if f is not None:
        f["checked"] = datetime.now().isoformat(timespec="seconds")
        f["last_check"] = {"state": current, "verdict": verdict}
        save_manifest(d, man)
    res = {"file_key": fkey, "verdict": verdict, "cached_state": (f or {}).get("state"),
           "current_state": current, "nodes_current": sorted(n for n, v in nodes.items() if v == "same"),
           "nodes_to_recheck": sorted(n for n, v in nodes.items() if v != "same")}
    if node:
        node = norm_node(node)
        res["node_id"] = node
        res["node_verdict"] = nodes.get(node, "not cached")
    return res


def cmd_save(d, root, spec_file, section=None, url=None, meta_file=None, shots=None, fingerprint=None,
             alias=None):
    spec = json.loads(Path(spec_file).read_text(encoding="utf-8"))
    src = spec.setdefault("source", {})
    if url:
        p = parse_url(url)
        src.setdefault("file_key", p["file_key"])
        src.setdefault("node_id", p["node_id"])
        src.setdefault("url", p["url"])
    fkey, node = src.get("file_key"), norm_node(src.get("node_id"))
    if not fkey or not node:
        raise SystemExit(json.dumps({"ok": False, "error": "spec.source needs file_key and node_id (or pass --url)"}))
    state = file_state(json.loads(Path(meta_file).read_text(encoding="utf-8"))) if meta_file else {}
    if fingerprint and Path(fingerprint).is_file():  # the figma_execute result, as a file
        fingerprint = fingerprints(json.loads(Path(fingerprint).read_text(encoding="utf-8"))).get(node)
    if fingerprint:
        src["fingerprint"] = fingerprint
    src["node_id"] = node
    src.setdefault("extracted", datetime.now().strftime("%Y-%m-%d"))
    src.update({k: v for k, v in state.items() if k in ("last_modified", "version")})
    spec.setdefault("schema", SCHEMA_SPEC)
    sec = section_slug(section or spec.get("section") or src.get("node_name") or node)
    spec["section"] = sec

    man = load_manifest(d)
    f = man["files"].setdefault(fkey, {"nodes": {}})
    if state.get("name"):
        f["name"] = state["name"]
    if state:
        f["state"] = state
        f["checked"] = datetime.now().isoformat(timespec="seconds")
    rel = Path("specs") / fkey / f"{node.replace(':', '-')}.json"
    path = d / rel
    previous = None
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        shutil.copy2(path, path.with_suffix(".prev.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    path.with_suffix(".md").write_text(render_md(spec, sec), encoding="utf-8")

    shot_rels = []
    if shots and Path(shots).is_dir():
        dest = d / "shots" / fkey / node.replace(":", "-")
        dest.mkdir(parents=True, exist_ok=True)
        for s in sorted(Path(shots).iterdir()):
            if s.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                shutil.copy2(s, dest / s.name)
                shot_rels.append((dest / s.name).relative_to(d).as_posix())
    # captures are heavy and binary: they never enter git, even inside a versioned vault
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("shots/\n*.prev.json\n", encoding="utf-8")

    old_entry = f["nodes"].get(node, {})
    f["nodes"][node] = {"section": sec, "name": src.get("node_name", old_entry.get("name", "")),
                        "breakpoints": spec.get("breakpoints") or src.get("breakpoints") or [],
                        "spec": rel.as_posix(), "md": rel.with_suffix(".md").as_posix(),
                        "shots": shot_rels or old_entry.get("shots", []),
                        "extracted": src["extracted"], "file_state": state or old_entry.get("file_state", {}),
                        "fingerprint": fingerprint or old_entry.get("fingerprint")}
    s = man["sections"].setdefault(sec, {"nodes": []})
    key = f"{fkey}|{node}"
    if key not in s["nodes"]:
        s["nodes"].append(key)
    if alias:  # the link the dev pasted points at a container of these frames
        man.setdefault("aliases", {})[f"{fkey}|{norm_node(alias)}"] = sec
    save_manifest(d, man)

    result = {"ok": True, "project": root.name, "section": sec, "spec": path.as_posix(),
              "md": path.with_suffix(".md").as_posix(), "first_time": previous is None}
    if previous is not None:
        dd = diff_specs(previous, spec)
        result.update(same=dd["same"], summary=diff_lines(dd),
                      counts={k: len(dd[k]) for k in ("changed", "added", "removed")})
    return result


def cmd_status(d, root):
    man = load_manifest(d)
    files = []
    for k, f in man["files"].items():
        files.append({"file_key": k, "name": f.get("name"), "state": f.get("state"), "checked": f.get("checked"),
                      "nodes": len(f["nodes"]),
                      "sections": sorted({e.get("section") for e in f["nodes"].values()})})
    return {"project": root.name, "cache": d.as_posix(), "exists": (d / "manifest.json").exists(),
            "files": files, "sections": sorted(man["sections"])}


def main(argv):
    cwd = None
    if "--cwd" in argv:
        i = argv.index("--cwd")
        cwd = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    opts = {}
    for flag in ("--section", "--url", "--meta", "--shots", "--fingerprint", "--alias"):
        if flag in argv:
            i = argv.index(flag)
            opts[flag[2:]] = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    cmd, args = (argv[0] if argv else "status"), argv[1:]
    if cmd == "parse":
        return parse_url(args[0])
    if cmd == "fingerprint-js":
        ids = [norm_node(a) for a in args]
        return (HERE / "figma-fingerprint.js").read_text(encoding="utf-8").replace("__IDS__", json.dumps(ids))
    if cmd == "diff":
        load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
        dd = diff_specs(load(args[0]), load(args[1]))
        return dict(dd, summary=diff_lines(dd))
    d, root = cache_dir(cwd)
    if cmd == "where":
        return {"project": root.name, "cache": d.as_posix(), "exists": d.is_dir(), "disabled": disabled(root)}
    if cmd in ("lookup", "check-file", "check-nodes", "save") and disabled(root):
        return {"cached": False, "ok": False, "disabled": True,
                "reason": "design_cache.enabled is false in this project: measure in Figma every time"}
    if cmd == "lookup":
        return cmd_lookup(d, args)
    if cmd == "check-file":
        return cmd_check_file(d, args[0], args[1], args[2] if len(args) > 2 else None)
    if cmd == "check-nodes":
        return cmd_check_nodes(d, args[0], args[1])
    if cmd == "save":
        return cmd_save(d, root, args[0], opts.get("section"), opts.get("url"), opts.get("meta"),
                        opts.get("shots"), opts.get("fingerprint"), opts.get("alias"))
    return cmd_status(d, root)


if __name__ == "__main__":
    out = main(sys.argv[1:])
    print(out if isinstance(out, str) else json.dumps(out, indent=1, ensure_ascii=False))
