#!/usr/bin/env python3
"""Eden explain-video: a short video that explains a finished ticket (script, screenshots, code animations).

The video lives outside the client's repo, in ~/.claude/eden-videos/{project}/{name}/:

    video.json      the script: beats (what is said + one visual action each); the dev approves it first
    shots.json      which real pages to capture, at which viewport
    shots/*.png     the captures
    script.md       the script, readable, for the dev to review
    video.mp4|webm  the result (mp4 with a system ffmpeg; webm with the ffmpeg bundled by Playwright)
    video.srt/.vtt  subtitles from the narration

Commands (print JSON unless noted):
    doctor                         node, browser and ffmpeg available, and which output format results
    init [--name N] [--cwd DIR]    create the folder with a video.json and shots.json to fill in
    shots <shots.json>             capture the real pages (http/https only)
    check <video.json>             validate the script, resolve durations, list problems
    script <video.json>            write and print script.md (for the dev's approval)
    voice <video.json> [--provider P] [--voice V]   narrate each beat (scripts/eden_voice.py); beats then
                                   last exactly what is said
    render <video.json> [--fps N]  render the video and the subtitles, and merge the voice when there is one

Stdlib only; the renderer is scripts/video/render.mjs (Node 22+, no npm packages) and the voice
scripts/eden_voice.py (system voice, Kokoro, OpenAI or ElevenLabs).
"""
import json
import os
import re
import importlib.util as _ilu
import shutil
import subprocess
import sys
from datetime import datetime
from glob import glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
_vs = _ilu.spec_from_file_location("eden_voice", HERE / "eden_voice.py")
voice = _ilu.module_from_spec(_vs)
_vs.loader.exec_module(voice)
RENDER = HERE / "video" / "render.mjs"
HOME = Path.home()
VIDEOS = HOME / ".claude" / "eden-videos"
KINDS = {"text": ["text"], "badge": ["text"], "icon": ["name"], "card": ["title"], "shot": ["src"],
         "counter": ["value"], "bars": ["items"], "prompt": ["text"], "code": ["lines"], "list": ["items"]}
ICONS = {"check", "code", "bug", "mobile", "desktop", "page", "link", "image", "cart", "clock", "sparkle", "layers",
         "search", "bolt", "arrow", "eye", "shield", "gauge"}
LAYOUT = {"x", "y", "w", "h", "scale", "opacity", "rotate", "key", "kind"}
CAPTION_WORDS = 4
WPS = 2.6           # narration speed, words per second (~155 wpm)
MAX_BEAT_WORDS = 16 # a beat says one thing; longer → split it
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def out(data, code=0):
    print(json.dumps(data, indent=1, ensure_ascii=False))
    sys.exit(code)


def opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


# --- tools ----------------------------------------------------------------------------------------

def node_ok():
    exe = shutil.which("node")
    if not exe:
        return None, None
    try:
        v = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    major = int(re.sub(r"[^0-9.]", "", v).split(".")[0] or 0)
    return (exe, v) if major >= 22 else (None, v)


def browser():
    local = os.environ.get("LOCALAPPDATA", "")
    cands = [os.environ.get("EDEN_VIDEO_BROWSER"),
             "C:/Program Files/Google/Chrome/Application/chrome.exe",
             "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
             local and os.path.join(local, "Google/Chrome/Application/chrome.exe"),
             "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
             "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
             "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]
    return next((c for c in cands if c and os.path.exists(c)), None)


def ffmpeg():
    """(exe, codec, extension). A full ffmpeg makes mp4/h264; the one Playwright ships only knows VP9 webm."""
    env = os.environ.get("EDEN_VIDEO_FFMPEG")
    if env and os.path.exists(env):
        return env, "h264", "mp4"
    sysff = shutil.which("ffmpeg")
    if sysff:
        return sysff, "h264", "mp4"
    roots = [os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"),
             str(HOME / ".cache" / "ms-playwright"), str(HOME / "Library" / "Caches" / "ms-playwright")]
    found = sorted(f for r in roots for f in glob(os.path.join(r, "ffmpeg-*", "ffmpeg*")) if os.path.isfile(f))
    if found:
        return found[-1], "vp9", "webm"
    return None, None, None


def cmd_doctor():
    node, nv = node_ok()
    br = browser()
    ff, codec, ext = ffmpeg()
    checks = [
        {"check": "Node 22+ (built-in WebSocket)", "ok": bool(node), "detail": nv or "not found"},
        {"check": "Chrome / Edge / Chromium", "ok": bool(br), "detail": br or "not found (set EDEN_VIDEO_BROWSER)"},
        {"check": "ffmpeg", "ok": bool(ff), "detail": (f"{ff} → {ext}" if ff else
                  "not visible from Python: `node scripts/video/render.mjs tools` shows what the renderer finds "
                  "(Playwright's bundled one gives .webm); none at all → install ffmpeg (Windows: winget install "
                  "Gyan.FFmpeg · macOS: brew install ffmpeg) — the dev decides")},
    ]
    note = None
    if ff and codec == "vp9":
        note = "using the ffmpeg bundled with Playwright: output is .webm (VP9). Install a full ffmpeg for .mp4 and, in phase 2, audio."
    out({"ok": all(c["ok"] for c in checks), "format": ext, "checks": checks, **({"note": note} if note else {})})


# --- the folder -----------------------------------------------------------------------------------

def project_slug(cwd):
    spec = __import__("importlib.util").util.spec_from_file_location("eden_brain", HERE.parent / "hooks" / "eden_brain.py")
    b = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(b)
    root = b.project_root(cwd)
    branch = ""
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, capture_output=True,
                                text=True, timeout=10, creationflags=NO_WINDOW).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return b.project_slug(root), branch


def slug(s):
    return re.sub(r"[^a-z0-9-]+", "-", (s or "").lower()).strip("-")[:80] or "video"


TEMPLATE = {
    "title": "{ticket title}",
    "lang": "en",
    "format": "vertical",
    "accent": "#f97316",
    "fps": 30,
    "beats": [
        {"say": "{the problem, in the client's words}", "actors": [
            {"key": "badge", "kind": "badge", "text": "{TICKET-ID}", "x": 50, "y": 18, "w": 60},
            {"key": "headline", "kind": "text", "text": "{what was wrong, *key word*}", "x": 50, "y": 40, "w": 86, "size": 104}]},
        {"say": "{what we changed}", "actors": [
            {"key": "badge", "kind": "badge", "text": "{TICKET-ID}", "x": 50, "y": 10, "w": 60},
            {"key": "page", "kind": "shot", "device": "browser", "before": "shots/before-desktop.png",
             "src": "shots/after-desktop.png", "x": 50, "y": 38, "w": 92, "h": 30}]},
        {"say": "{how it looks on a phone}", "actors": [
            {"key": "page", "kind": "shot", "device": "phone", "src": "shots/after-mobile.png", "x": 50, "y": 38, "w": 52, "h": 52,
             "marks": [{"x": 4, "y": 10, "w": 92, "h": 14}]}]},
        {"say": "{a number that shows the size of it}", "actors": [
            {"key": "metric", "kind": "counter", "value": 66, "label": "{what was counted}", "x": 50, "y": 38, "w": 80}]},
        {"say": "{the key change in the code}", "actors": [
            {"key": "code", "kind": "code", "file": "{path/to/file}", "lines": [{"t": "-", "s": "{old}"}, {"t": "+", "s": "{new}"}],
             "x": 50, "y": 38, "w": 92}]},
        {"say": "{what is ready for review}", "actors": [
            {"key": "done", "kind": "list", "items": ["{…}", "{…}"], "x": 50, "y": 36, "w": 84}]},
    ],
}
SHOTS = {"out": "shots", "shots": [
    {"name": "before-desktop", "url": "{live or main preview URL of the page}", "width": 1440, "height": 900},
    {"name": "after-desktop", "url": "{preview URL with the change}", "width": 1440, "height": 900},
    {"name": "after-mobile", "url": "{preview URL with the change}", "width": 390, "height": 844, "mobile": True,
     "fullPage": False, "blur": [], "hide": []},
]}


def cmd_init(argv):
    cwd = opt(argv, "--cwd") or os.getcwd()
    proj, branch = project_slug(cwd)
    name = slug(opt(argv, "--name") or branch or datetime.now().strftime("%Y-%m-%d"))
    d = VIDEOS / proj / name
    (d / "shots").mkdir(parents=True, exist_ok=True)
    made = []
    for fname, data in (("video.json", TEMPLATE), ("shots.json", SHOTS)):
        f = d / fname
        if not f.exists():
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            made.append(f.as_posix())
    out({"ok": True, "dir": d.as_posix(), "created": made, "project": proj, "branch": branch})


# --- checking and timing ----------------------------------------------------------------------------

PLACEHOLDER = re.compile(r"(?<![$\w])\{(?:…|[A-Za-z][^{}]*)\}")  # {ticket title}, {TICKET-ID}, {…}; not ${code}


def strings(obj, key=None):
    """(top-level key, text) for every string in a scene; code lines are skipped by the caller."""
    if isinstance(obj, str):
        yield key, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(v, key or k)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v, key)


def estimate(say):
    words = len(re.findall(r"\S+", (say or "").replace("*", "")))
    return round(max(1.8, words / WPS + 0.5), 2)


def content(a):
    return json.dumps({k: v for k, v in a.items() if k not in LAYOUT}, sort_keys=True)


def check(spec, base):
    """Problems of a beats script, and the spec with every beat's duration resolved."""
    problems = []
    beats = spec.get("beats")
    if not isinstance(beats, list) or not beats:
        return ["`beats` must be a non-empty list (one beat = one short thing said + one visual action)"], spec
    if spec.get("format", "vertical") not in ("vertical", "horizontal"):
        problems.append("`format` must be vertical or horizontal")
    prev = {}
    for b in beats:
        b["_explicit"] = "duration" in b
    for i, b in enumerate(beats, 1):
        say = (b.get("say") or "").strip()
        if not say:
            problems.append(f"beat {i}: missing `say` (what the narration says in this beat)")
        elif len(say.replace("*", "").split()) > MAX_BEAT_WORDS:
            problems.append(f"beat {i}: `say` has {len(say.split())} words; split it (≤ {MAX_BEAT_WORDS}, one idea per beat)")
        actors = b.get("actors") or []
        if not actors:
            problems.append(f"beat {i}: no actors — every beat needs a visual action")
        now = {}
        for j, a in enumerate(actors, 1):
            kind, where = a.get("kind"), f"beat {i} actor {a.get('key') or j}"
            if kind not in KINDS:
                problems.append(f"{where}: unknown kind {kind!r} (use {', '.join(KINDS)})")
                continue
            for k in KINDS[kind]:
                if a.get(k) in (None, "", []):
                    problems.append(f"{where} ({kind}): missing `{k}`")
            if kind == "icon" and a.get("name") not in ICONS:
                problems.append(f"{where}: unknown icon {a.get('name')!r} (use {', '.join(sorted(ICONS))})")
            for k in ("src", "before"):
                v = a.get(k)
                if not v:
                    continue
                if re.match(r"^([a-z]+:|/|\\)", v, re.I) or ".." in Path(v).parts:
                    problems.append(f"{where}: `{k}` must be a path inside the video folder")
                elif not (base / v).is_file():
                    problems.append(f"{where}: `{k}` file not found: {v}")
            if any(PLACEHOLDER.search(v) for k, v in strings(a) if k != "lines"):
                problems.append(f"{where}: still has template placeholders {{…}}")
            now[a.get("key") or f"{i}:{j}"] = a
        if PLACEHOLDER.search(say):
            problems.append(f"beat {i}: `say` still has template placeholders {{…}}")
        # one visual action per beat: something enters, leaves, moves or changes
        if i > 1 and actors and now.keys() == prev.keys() and all(
                content(now[k]) == content(prev[k]) and all(now[k].get(x) == prev[k].get(x) for x in ("x", "y", "w", "h", "scale"))
                for k in now):
            problems.append(f"beat {i}: nothing changes on screen — give it its own visual action")
        prev = now
        b["duration"] = float(b.get("duration") or estimate(say))
    voiced = voice.durations_for(spec, base)
    if voiced:  # the narration audio decides: a beat lasts at least what is said in it
        for b, d in zip(beats, voiced):
            b["duration"] = max(d, float(b["duration"]) if "duration" in b and b.get("_explicit") else d)
    return problems, spec


def load(path):
    p = Path(path).resolve()
    try:
        return p, json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out({"ok": False, "error": f"cannot read {p}: {exc}"}, 1)


def cmd_check(argv):
    p, spec = load(argv[0])
    problems, spec = check(spec, p.parent)
    out({"ok": not problems, "problems": problems, "beats": len(spec.get("beats") or []),
         "format": spec.get("format", "vertical"),
         "duration_seconds": round(sum(b.get("duration", 0) for b in spec.get("beats") or []), 1)})


def action(a, before):
    kind, key = a.get("kind"), a.get("key", "")
    what = a.get("text") or a.get("title") or a.get("name") or a.get("src") or a.get("file") or a.get("label") or ""
    if kind == "counter":
        what = f"{a.get('value')} {a.get('label', '')}".strip()
    if before is None:
        verb = "enters"
    elif content(a) != content(before):
        verb = "changes"
    else:
        verb = "moves"
    return f"{kind} `{key}` {verb}" + (f": {str(what)[:40]}" if what and verb != "moves" else "")


def script_md(spec):
    beats = spec["beats"]
    lines = [f"# {spec.get('title', 'Explain video')}", "",
             f"Format: {spec.get('format', 'vertical')} · Language: {spec.get('lang', 'en')} · "
             f"Total: {sum(b['duration'] for b in beats):.0f} s · {len(beats)} beats", "",
             "| # | Says | Visual action | s |", "|---|---|---|---|"]
    prev = {}
    for i, b in enumerate(beats, 1):
        now = {a.get("key") or f"{i}:{j}": a for j, a in enumerate(b.get("actors") or [], 1)}
        acts = [action(a, prev.get(k)) for k, a in now.items()
                if prev.get(k) is None or content(a) != content(prev[k])
                or any(a.get(x) != prev[k].get(x) for x in ("x", "y", "w", "h", "scale"))]
        acts += [f"`{k}` leaves" for k in prev if k not in now]
        say = (b.get("say") or "").replace("|", "/")
        lines.append(f"| {i} | {say} | {'; '.join(acts) or '—'} | {b['duration']:.1f} |")
        prev = now
    return "\n".join(lines) + "\n"


def cmd_script(argv):
    p, spec = load(argv[0])
    problems, spec = check(spec, p.parent)
    md = script_md(spec)
    (p.parent / "script.md").write_text(md, encoding="utf-8")
    print(md)
    if problems:
        print("Problems:\n- " + "\n- ".join(problems))


# --- subtitles ------------------------------------------------------------------------------------

def chunk_words(say, n=CAPTION_WORDS):
    """The player's caption chunks: at most n words, ending early at punctuation."""
    words = (say or "").replace("*", "").split()
    out_, i = [], 0
    while i < len(words):
        k = min(n, len(words) - i)
        for m in range(1, k):
            if re.search(r"[,.;:!?]$", words[i + m - 1]):
                k = m
                break
        out_.append(" ".join(words[i:i + k]))
        i += k
    return out_


def cues(spec):
    """Subtitles exactly as the video shows them: ≤ 4 words, timed by length inside each beat."""
    t, out_ = 0.0, []
    for b in spec["beats"]:
        parts, dur = chunk_words(b.get("say")), b["duration"]
        weights = [len(x) + 4 for x in parts]
        total, acc, usable = sum(weights) or 1, 0.0, dur - 0.15
        for x, w in zip(parts, weights):
            start = t + usable * acc / total
            acc += w
            out_.append((start, t + usable * acc / total, x))
        t += dur
    return out_


def ts(sec, sep):
    h, rem = divmod(int(sec * 1000), 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_subs(spec, base):
    cs = cues(spec)
    srt = "\n".join(f"{i}\n{ts(a, ',')} --> {ts(b, ',')}\n{x}\n" for i, (a, b, x) in enumerate(cs, 1))
    vtt = "WEBVTT\n\n" + "\n".join(f"{ts(a, '.')} --> {ts(b, '.')}\n{x}\n" for a, b, x in cs)
    (base / "video.srt").write_text(srt, encoding="utf-8")
    (base / "video.vtt").write_text(vtt, encoding="utf-8")


# --- running the renderer -------------------------------------------------------------------------

def node_run(args, timeout):
    node, nv = node_ok()
    if not node:
        out({"ok": False, "error": f"Node 22+ is needed (found {nv or 'none'})"}, 1)
    r = subprocess.run([node, str(RENDER), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, creationflags=NO_WINDOW)
    try:
        return json.loads(r.stdout)  # render.mjs prints one JSON object; progress goes to stderr
    except ValueError:
        return {"ok": False, "error": (r.stdout + r.stderr)[-600:]}


def cmd_shots(argv):
    p = Path(argv[0]).resolve()
    out(node_run(["shots", str(p)], 600))


def cmd_render(argv):
    p, spec = load(argv[0])
    problems, spec = check(spec, p.parent)
    if problems:
        out({"ok": False, "problems": problems}, 1)
    resolved = p.parent / ".render.json"
    resolved.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    write_subs(spec, p.parent)
    (p.parent / "script.md").write_text(script_md(spec), encoding="utf-8")
    fps = opt(argv, "--fps") or str(spec.get("fps", 30))
    node_cmd = ["node", RENDER.as_posix(), "render", resolved.as_posix(), "--out", (p.parent / "video").as_posix(), "--fps", fps]
    ff, codec, _ = ffmpeg()
    if not ff:  # this Python may not see a bundled ffmpeg that Node, run from the shell, does see
        out({"ok": True, "prepared": resolved.as_posix(), "run": " ".join(f'"{x}"' if " " in x else x for x in node_cmd),
             "note": "run this command in the shell: it renders the video and prints the result"
                     + ("; the voice stays in audio/voice.wav (`eden_video.py preview` pairs them)" if voice.durations_for(spec, p.parent) else "")})
    voiced = voice.durations_for(spec, p.parent) is not None
    target = ["--out", (p.parent / ("video-silent" if voiced else "video")).as_posix()]
    res = node_run(node_cmd[2:4] + target + node_cmd[6:] + ["--ffmpeg", ff, "--codec", codec], 3600)
    resolved.unlink(missing_ok=True)
    if res.get("ok") and voiced:
        res.update(mux(Path(res["out"]), p.parent / "audio" / "voice.wav", ff, codec))
    if res.get("ok"):
        res.update({"subtitles": [(p.parent / "video.srt").as_posix(), (p.parent / "video.vtt").as_posix()]})
    out(res, 0 if res.get("ok") else 1)


def has_audio_encoder(ff):
    try:
        enc = subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=20,
                             creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return bool(re.search(r"^ A\S*\s+(aac|libopus|libmp3lame)\b", enc, re.M))


def mux(silent, wav, ff, codec):
    """video.(mp4|webm) = the silent render + the voice track. Needs an ffmpeg with an audio encoder (the
    one Playwright ships has none: then the voice stays next to the video as voice.wav)."""
    final = silent.with_name("video" + silent.suffix)
    if not has_audio_encoder(ff):
        silent.replace(final)
        write_preview(final, wav)
        return {"out": final.as_posix(), "voice": wav.as_posix(), "muxed": False,
                "preview": (final.parent / "preview.html").as_posix(),
                "note": "this ffmpeg has no audio encoder: the video is silent and the voice is voice.wav. Install a full "
                        "ffmpeg (Windows: winget install Gyan.FFmpeg) to merge them — the dev decides"}
    acodec = ["-c:a", "libopus", "-b:a", "128k"] if codec == "vp9" else ["-c:a", "aac", "-b:a", "160k"]
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-af", "apad", *acodec, "-shortest", str(final)], capture_output=True, text=True, timeout=600,
                       creationflags=NO_WINDOW)
    if r.returncode:
        return {"ok": False, "error": "mux failed: " + r.stderr[-300:]}
    silent.unlink(missing_ok=True)
    return {"out": final.as_posix(), "muxed": True}


PREVIEW = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Explain video preview</title>
<style>body{{margin:0;background:#0d0d0f;display:grid;place-items:center;min-height:100vh;font-family:system-ui;color:#aaa}}
video{{max-height:92vh;max-width:96vw;border-radius:12px}}p{{font-size:14px}}</style></head><body>
<div><video id="v" src="{video}" controls playsinline muted></video><audio id="a" src="{audio}"></audio>
<p>Preview: the video and the voice play together. A full ffmpeg merges them into one file.</p></div>
<script>const v=document.getElementById("v"),a=document.getElementById("a");
const sync=()=>{{if(Math.abs(a.currentTime-v.currentTime)>0.15)a.currentTime=v.currentTime}};
v.addEventListener("play",()=>{{sync();a.play()}});v.addEventListener("pause",()=>a.pause());
v.addEventListener("seeked",sync);v.addEventListener("timeupdate",sync);</script></body></html>
"""


def write_preview(video, wav):
    """A local page that plays the silent video with the voice, for when no ffmpeg can merge them."""
    rel = os.path.relpath(wav, video.parent).replace(os.sep, "/")
    (video.parent / "preview.html").write_text(PREVIEW.format(video=video.name, audio=rel), encoding="utf-8")


def cmd_voice(argv):
    """Narrate every beat (only the ones whose text or voice changed) and build audio/voice.wav."""
    p, spec = load(argv[0])
    problems, spec = check(spec, p.parent)
    blocking = [x for x in problems if "missing `say`" in x or "placeholders" in x]
    if blocking:
        out({"ok": False, "problems": blocking}, 1)
    try:
        m = voice.synthesize(spec, p.parent, provider=opt(argv, "--provider"), voice=opt(argv, "--voice"),
                             lang=opt(argv, "--lang"))
    except Exception as exc:  # report the provider's error plainly; the dev picks another provider
        out({"ok": False, "error": str(exc)}, 1)
    out({"ok": True, "provider": m["provider"], "voice": m["voice"], "track": (p.parent / "audio" / "voice.wav").as_posix(),
         "duration_seconds": round(sum(e["duration"] for e in m["beats"]), 1),
         "beats": [e["duration"] for e in m["beats"]]})


def main(argv):
    cmd, rest = (argv[0] if argv else ""), argv[1:]
    if cmd == "doctor":
        cmd_doctor()
    elif cmd == "init":
        cmd_init(rest)
    elif cmd == "preview" and rest:
        d = Path(rest[0]).resolve().parent
        vid = next((d / f"video.{e}" for e in ("mp4", "webm") if (d / f"video.{e}").exists()), None)
        if not vid or not (d / "audio" / "voice.wav").exists():
            out({"ok": False, "error": "needs video.mp4|webm and audio/voice.wav in the folder"}, 1)
        write_preview(vid, d / "audio" / "voice.wav")
        out({"ok": True, "preview": (d / "preview.html").as_posix()})
    elif cmd in ("shots", "check", "script", "voice", "render") and rest:
        {"shots": cmd_shots, "check": cmd_check, "script": cmd_script, "voice": cmd_voice, "render": cmd_render}[cmd](rest)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
