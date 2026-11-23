import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eden_video", PLUGIN / "scripts" / "eden_video.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
RENDER = PLUGIN / "scripts" / "video" / "render.mjs"
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


tmp = Path(tempfile.mkdtemp())
(tmp / "shots").mkdir()
# a 1x1 PNG is enough for validation
png = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4480000000049454e44ae426082")
(tmp / "shots" / "a.png").write_bytes(png)

# --- validation (beats: one short thing said + one visual action)
good = {"format": "vertical", "beats": [
    {"say": "Every ticket ends with a *question*.", "actors": [{"key": "hero", "kind": "icon", "name": "page"}]},
    {"say": "Here is the page, before and after.", "actors": [
        {"key": "page", "kind": "shot", "src": "shots/a.png", "before": "shots/a.png", "device": "browser"}]},
    {"say": "Same page, on a phone.", "actors": [{"key": "page", "kind": "shot", "src": "shots/a.png", "device": "phone", "w": 50}]},
    {"say": "Sixty six links fixed.", "actors": [{"key": "n", "kind": "counter", "value": 66, "label": "links"}]},
    {"say": "The change.", "actors": [{"key": "c", "kind": "code", "lines": [{"t": "+", "s": "{{ link.text | default: x }} ${a}"}]}]},
]}
problems, s = v.check(json.loads(json.dumps(good)), tmp)
check("a valid beats script has no problems", problems == [])
check("durations come from what is said", all(b["duration"] >= 1.8 for b in s["beats"]))
check("code braces are not placeholders", not any("placeholder" in p for p in problems))
bad = {"format": "square", "beats": [
    {"say": "", "actors": [{"kind": "nope"}]},
    {"say": "x", "actors": [{"kind": "shot", "src": "../outside.png"}]},
    {"say": "y", "actors": [{"kind": "shot", "src": "shots/missing.png"}]},
    {"say": "{what was done}", "actors": [{"kind": "text", "text": "{headline}"}]},
    {"say": "z", "actors": [{"kind": "list"}, {"kind": "icon", "name": "unicorn"}]},
    {"say": " ".join(["word"] * 20), "actors": [{"kind": "badge", "text": "ok"}]},
    {"say": "nothing new", "actors": []},
]}
problems, _ = v.check(bad, tmp)
txt = " | ".join(problems)
check("unknown kind reported", "unknown kind" in txt)
check("format must be vertical or horizontal", "`format`" in txt)
check("missing say reported", "missing `say`" in txt)
check("paths outside the folder refused", "inside the video folder" in txt)
check("missing files reported", "missing.png" in txt)
check("template placeholders reported", "placeholders" in txt)
check("missing required fields reported", "missing `items`" in txt)
check("unknown icon reported", "unknown icon" in txt)
check("long beat must be split", "split it" in txt)
check("beat without actors reported", "needs a visual action" in txt)
static = {"beats": [{"say": "a b", "actors": [{"key": "k", "kind": "badge", "text": "x"}]},
                    {"say": "c d", "actors": [{"key": "k", "kind": "badge", "text": "x"}]}]}
check("a beat where nothing changes is refused", any("nothing changes" in p for p in v.check(static, tmp)[0]))
moved = {"beats": [{"say": "a b", "actors": [{"key": "k", "kind": "badge", "text": "x", "y": 20}]},
                   {"say": "c d", "actors": [{"key": "k", "kind": "badge", "text": "x", "y": 40}]}]}
check("moving a persistent actor counts as an action", v.check(moved, tmp)[0] == [])
check("empty script refused", v.check({"beats": []}, tmp)[0] != [])
check("the template itself is not renderable", v.check(json.loads(json.dumps(v.TEMPLATE)), tmp)[0] != [])

# --- captions: at most 4 words, cut at punctuation, timed inside each beat
check("chunks of at most 4 words", v.chunk_words("one two three four five six") == ["one two three four", "five six"])
check("chunks end at punctuation", v.chunk_words("Hi, this is it. Done") == ["Hi,", "this is it.", "Done"])
_, s = v.check(json.loads(json.dumps(good)), tmp)
cs = v.cues(s)
check("every cue has ≤ 4 words and no markup", all(len(x.split()) <= 4 and "*" not in x for _, _, x in cs))
check("cues are in order and inside the video", all(a < b for a, b, _ in cs)
      and cs[-1][1] <= sum(x["duration"] for x in s["beats"]))
v.write_subs(s, tmp)
srt = (tmp / "video.srt").read_text(encoding="utf-8")
check("srt and vtt written", srt.startswith("1\n00:00:00,000 --> ") and (tmp / "video.vtt").read_text(encoding="utf-8").startswith("WEBVTT"))
md = v.script_md(s)
check("script.md shows what is said and the visual action", "| # | Says | Visual action | s |" in md
      and "shot `page` changes" in md and "`hero` leaves" in md)

# --- voice-over: per-beat clips set the beat durations; one track; merge or preview
import array
import wave
vo = v.voice
vd = tmp / "voiced"
(vd / "audio").mkdir(parents=True)
(vd / "shots").mkdir()
(vd / "shots" / "a.png").write_bytes(png)
spec2 = json.loads(json.dumps(good))
def tone(path, seconds, rate=22050):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(array.array("h", [1000] * int(seconds * rate)).tobytes())
lens = [1.0, 2.0, 0.5, 1.5, 0.8]
for i, L in enumerate(lens, 1):
    tone(vd / "audio" / f"beat-{i:02d}.wav", L, 22050 if i != 3 else 24000)
orig = vo.say_system
vo.say_system = lambda texts, outs, voice=None, rate=0: [tone(o, 1.0) for o in outs]
try:
    m = vo.synthesize(spec2, vd, provider="system")
finally:
    vo.say_system = orig
check("voice: every beat lasts its speech plus lead and tail", all(abs(e["duration"] - max(e["speech"] + vo.LEAD + vo.TAIL, 1.2)) < 1e-6
      for e in m["beats"]))
check("voice: one track, one sample rate, as long as the beats", abs(vo.wav_info(vd / "audio" / "voice.wav")[3]
      - sum(e["duration"] for e in m["beats"])) < 0.01)
check("voice: manifest matches the script", vo.durations_for(spec2, vd) == [e["duration"] for e in m["beats"]])
changed = json.loads(json.dumps(spec2)); changed["beats"][1]["say"] = "Something else entirely."
check("voice: an edited line invalidates the timing", vo.durations_for(changed, vd) is None)
_, chk = v.check(json.loads(json.dumps(spec2)), vd)
check("check uses the voice durations", [b["duration"] for b in chk["beats"]] == [e["duration"] for e in m["beats"]])
calls = []
vo.say_system = lambda texts, outs, voice=None, rate=0: (calls.append(list(texts)), [tone(o, 1.0) for o in outs])
try:
    vo.synthesize(changed, vd, provider="system")
finally:
    vo.say_system = orig
check("voice: only changed lines are narrated again", calls == [["Something else entirely."]])
check("voice: auto never picks a paid API", vo.resolve_provider({"provider": "auto"}) in ("kokoro", "system"))
check("voice: markup is not spoken", vo.plain("Ready for *review*.") == "Ready for review.")
try:
    vo.synthesize(spec2, vd, provider="openai-ish")
    check("voice: unknown provider refused", False)
except RuntimeError as exc:
    check("voice: unknown provider refused", "unknown TTS provider" in str(exc))
os.environ.pop("OPENAI_API_KEY", None)
try:
    vo.say_openai(["x"], [vd / "x.wav"], cfg={})
    check("voice: openai needs its key from the environment", False)
except RuntimeError as exc:
    check("voice: openai needs its key from the environment", "OPENAI_API_KEY" in str(exc))
(vd / "video-silent.webm").write_bytes(b"x")
res = v.mux(vd / "video-silent.webm", vd / "audio" / "voice.wav", sys.executable, "vp9")
check("no audio encoder: silent video + voice + preview page", res.get("muxed") is False
      and (vd / "video.webm").exists() and "voice.wav" in (vd / "preview.html").read_text(encoding="utf-8"))
if os.name == "nt" and os.environ.get("EDEN_TEST_TTS", "1") == "1":
    sd = tmp / "sapi"
    sd.mkdir()
    real = vo.synthesize({"beats": [{"say": "Hello from Eden."}]}, sd, provider="system")
    check("the Windows voice really speaks", real["beats"][0]["speech"] > 0.5)

# --- render writes into the video folder (regression: --out once, pointing inside the folder)
seen = {}
v.ffmpeg = lambda: ("ffmpeg-fake", "h264", "mp4")
v.node_run = lambda args, timeout: seen.setdefault("args", args) and {"ok": False, "error": "stop"}
(vd / "video.json").write_text(json.dumps(spec2), encoding="utf-8")
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    try:
        v.cmd_render([str(vd / "video.json")])
    except SystemExit:
        pass
args = seen.get("args", [])
check("render passes --out once, inside the video folder", args.count("--out") == 1
      and Path(args[args.index("--out") + 1]).parent == vd.resolve() and Path(args[args.index("--out") + 1]).name in ("video", "video-silent"))

# --- turnoff-task asks for the video and runs it after the PR, before the tracker
tt = (PLUGIN / "skills" / "turnoff-task" / "SKILL.md").read_text(encoding="utf-8")
check("closing report asks about the video", "🎬 Video explicativo" in tt and "(y dime si quieres el video)" in tt)
check("the yes to commit is not a yes to the video", "El sí al commit no es un sí al video" in tt
      and "Si el dev no dice nada del video, es un no" in tt)
check("video.mode off silences the question", "video.mode: \"off\"" in tt or "video.mode: off" in tt)
i8, i8b, i9 = tt.index("### Paso 8 —"), tt.index("### Paso 8b —"), tt.index("### Paso 9 —")
check("step 8b sits after the PR and before the tracker", i8 < i8b < i9)
step = tt[i8b:i9]
check("step 8b keeps the beats approval and stays out of the PR and repo",
      "se espera el sí del dev" in step and "no va al PR ni al repo" in step and "no bloquea" in step)
cfg = json.loads((PLUGIN / "team" / "project-config.example.json").read_text(encoding="utf-8"))
check("project config: video.mode ask by default", cfg["video"]["mode"] == "ask")
ev = (PLUGIN / "skills" / "explain-video" / "SKILL.md").read_text(encoding="utf-8")
check("explain-video knows the turnoff hand-off", "Desde `turnoff-task`" in ev and "Paso 8b" in ev)

# --- the folder lives outside the client repo
home = tmp / "home"
v.VIDEOS = home / ".claude" / "eden-videos"
proj = tmp / "client"
proj.mkdir()
subprocess.run(["git", "init", "-q"], cwd=proj)
subprocess.run(["git", "remote", "add", "origin", "https://github.com/acme/store.git"], cwd=proj)
try:
    v.cmd_init(["--name", "TICKET-1", "--cwd", str(proj)])
except SystemExit:
    pass
d = v.VIDEOS / "acme-store" / "ticket-1"
check("init creates the folder outside the repo", (d / "video.json").exists() and (d / "shots.json").exists()
      and not (proj / ".claude").exists())

# --- renderer: syntax, tools, and a tiny real render when a browser and ffmpeg exist
node = shutil.which("node")
if node:
    r = subprocess.run([node, "--check", str(RENDER)], capture_output=True, text=True)
    check("render.mjs parses", r.returncode == 0)
    tools = json.loads(subprocess.run([node, str(RENDER), "tools"], capture_output=True, text=True).stdout)
    check("tools reports browser and ffmpeg", "browser" in tools and "ffmpeg" in tools)
    r = subprocess.run([node, str(RENDER), "shots", str(tmp / "x.json")], capture_output=True, text=True)
    check("unknown spec file fails cleanly", r.returncode != 0)
    (tmp / "bad-shots.json").write_text(json.dumps({"shots": [{"name": "x", "url": "file:///etc/passwd"}]}), encoding="utf-8")
    if tools.get("browser"):
        r = subprocess.run([node, str(RENDER), "shots", str(tmp / "bad-shots.json")], capture_output=True, text=True, timeout=60)
        check("shots refuse non-http URLs", '"ok":false' in r.stdout.replace(" ", "") and "http" in r.stdout)
    if tools.get("browser"):
        sp = {"beats": [{"say": "the code", "duration": 2, "actors": [{"kind": "code", "lines": [{"t": "+", "s": "x"}]}]},
                        {"say": "the page", "duration": 2, "actors": [{"kind": "shot", "src": "shots/a.png", "device": "phone",
                                                                       "marks": [{"x": 0, "y": 0, "w": 50, "h": 50}]}]}]}
        (tmp / "still.json").write_text(json.dumps(sp), encoding="utf-8")
        r = subprocess.run([node, str(RENDER), "still", str(tmp / "still.json"), "--at", "3", "--out", str(tmp / "p.png")],
                           capture_output=True, text=True, timeout=120)
        check("still renders one frame as PNG (poster)", (tmp / "p.png").exists()
              and (tmp / "p.png").read_bytes()[1:4] == b"PNG")
    if tools.get("browser") and tools.get("ffmpeg") and os.environ.get("EDEN_TEST_RENDER", "1") == "1":
        tiny = {"fps": 4, "beats": [{"say": "hi", "duration": 1, "actors": [{"kind": "icon", "name": "check"}]},
                                    {"say": "page", "duration": 1, "actors": [{"kind": "shot", "src": "shots/a.png"}]}]}
        (tmp / "tiny.json").write_text(json.dumps(tiny), encoding="utf-8")
        r = subprocess.run([node, str(RENDER), "render", str(tmp / "tiny.json"), "--out", str(tmp / "tiny")],
                           capture_output=True, text=True, timeout=300)
        res = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"error": r.stdout + r.stderr}
        outf = Path(res.get("out", ""))
        check("a tiny real render works (frames counted, file written)", res.get("ok") and res["frames"] == 8
              and outf.exists() and outf.stat().st_size > 1000)
else:
    print("SKIP renderer checks (no node)")

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
