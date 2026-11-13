"""Tests for the context watcher (hooks/eden_context.py) against a fake brain and fake transcripts."""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
spec = importlib.util.spec_from_file_location("eden_context", HOOKS / "eden_context.py")
ctx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctx)

tmp = Path(tempfile.mkdtemp())
b = ctx.brain()
b.HOME = tmp / "home"
b.BRAIN = tmp / "home" / ".claude" / "eden-brain"
b.STATE = b.BRAIN / ".state"
b.QUEUE = b.STATE / "queue"
b.LOGS = b.STATE / "logs"
b.STATUS = b.STATE / "distill_status.json"
b.QUARANTINE = b.STATE / "quarantine"
b.CLAUDE_DIR = tmp / "home" / ".claude"
b.spawn = lambda *a, **k: None            # never launch the real distiller
ctx.CLAUDE_DIR = b.CLAUDE_DIR
ctx.PROJECTS = b.CLAUDE_DIR / "projects"
b.BRAIN.mkdir(parents=True)
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def run(fn, payload):
    ctx.read_payload = lambda: payload
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn()
    s = out.getvalue().strip()
    return json.loads(s) if s.startswith("{") else s


proj = tmp / "client-project"
(proj / ".git").mkdir(parents=True)
(proj / ".claude").mkdir()


def transcript(path, used, model="claude-opus-5-5", users=3):
    lines = []
    for i in range(users):
        lines.append({"type": "user", "cwd": str(proj), "message": {"role": "user", "content": f"request {i}"}})
        lines.append({"type": "assistant", "cwd": str(proj), "message": {
            "role": "assistant", "model": model,
            "content": [{"type": "text", "text": f"answer {i}"},
                        {"type": "tool_use", "name": "Read", "input": {"file_path": f"/x/{i}.py"}}],
            "usage": {"input_tokens": 2, "cache_creation_input_tokens": used - 1002, "cache_read_input_tokens": 1000}}})
    lines.append({"type": "assistant", "isSidechain": True, "message": {"model": model, "usage": {
        "input_tokens": 1, "cache_creation_input_tokens": 1, "cache_read_input_tokens": 1}}})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    return str(path)


# --- window and measurement ------------------------------------------------------------------------
cfg = dict(ctx.DEFAULTS)
check("opus 5 → 1M", ctx.window_for("claude-opus-5-5", cfg) == 1_000_000)
check("fable → 1M", ctx.window_for("claude-fable-5-1", cfg) == 1_000_000)
check("sonnet 4.6 → 200k", ctx.window_for("claude-sonnet-4-6", cfg) == 200_000)
check("[1m] suffix → 1M", ctx.window_for("claude-sonnet-4-6[1m]", cfg) == 1_000_000)
check("configured window wins", ctx.window_for("claude-opus-5-5", dict(cfg, window=500_000)) == 500_000)
os.environ["CLAUDE_CODE_DISABLE_1M_CONTEXT"] = "1"
check("1M disabled → 200k", ctx.window_for("claude-opus-5-5", cfg) == 200_000)
del os.environ["CLAUDE_CODE_DISABLE_1M_CONTEXT"]

t1 = transcript(ctx.PROJECTS / "p" / "sess-aaaa1111.jsonl", 300_000)
used, model = ctx.usage_from_transcript(t1)
check("usage = input + cache creation + cache read, sidechain ignored", used == 300_000 and model == "claude-opus-5-5")
m = ctx.measure("sess-aaaa1111", t1, cfg)
check("measure from transcript", m["pct"] == 30.0 and m["source"] == "transcript")
ctx.state_dir().mkdir(parents=True, exist_ok=True)
ctx.sensor_path("sess-aaaa1111").write_text(json.dumps({"pct": 41.5, "at": time.time()}), encoding="utf-8")
check("fresh status-line reading preferred", ctx.measure("sess-aaaa1111", t1, cfg)["pct"] == 41.5)
ctx.sensor_path("sess-aaaa1111").write_text(json.dumps({"pct": 41.5, "at": time.time() - 3600}), encoding="utf-8")
check("stale reading ignored", ctx.measure("sess-aaaa1111", t1, cfg)["source"] == "transcript")

# --- watch: below the threshold, nothing ------------------------------------------------------------
sid = "sess-bbbb2222"
tp = ctx.PROJECTS / "p" / f"{sid}.jsonl"
payload = {"session_id": sid, "transcript_path": str(tp), "cwd": str(proj)}
transcript(tp, 400_000)
check("40 % → silent", run(ctx.cmd_watch, payload) == "")

# --- watch: at save_at it saves once ------------------------------------------------------------------
transcript(tp, 650_000)
out = run(ctx.cmd_watch, payload)
check("65 % → user message", isinstance(out, dict) and "guardando" in out.get("systemMessage", ""))
check("65 % → hand-off instruction to Claude",
      "checkpoint.md" in out["hookSpecificOutput"]["additionalContext"]
      and out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit")
st = ctx.load_state(sid)
check("state records the save", st.get("saved_at") and st.get("brain_status") == "queued" and st.get("brain_files"))
check("session queued in the brain", b.pending_for(sid) and all("sess-bbb" in n for n in b.pending_for(sid)))
transcript(tp, 660_000)
check("66 % → no second save", run(ctx.cmd_watch, payload) == "")

# --- watch: at warn_at, safe only when really saved ----------------------------------------------------
transcript(tp, 820_000)
out = run(ctx.cmd_watch, payload)
msg = out["systemMessage"]
check("82 % with queue pending → not safe yet", msg.startswith("⏳") and "destila" in msg and "checkpoint" in msg)
check("82 % missing checkpoint → instruction again", "additionalContext" in out.get("hookSpecificOutput", {}))
transcript(tp, 830_000)
check("83 % → no repeat within the step", run(ctx.cmd_watch, payload) == "")
for q in b.QUEUE.glob("*.md"):         # the distiller finished: notes written, items retired
    q.unlink()
(proj / ".claude" / "checkpoint.md").write_text("# Checkpoint\nTask: X. Next: Y.\n", encoding="utf-8")
transcript(tp, 880_000)
out = run(ctx.cmd_watch, payload)
check("88 % saved + checkpoint → safe, recommends /clear", out["systemMessage"].startswith("✅") and "/clear" in out["systemMessage"])
check("safe message carries no extra instruction", "hookSpecificOutput" not in out)

# --- old checkpoint does not count ------------------------------------------------------------------------
sid2 = "sess-cccc3333"
tp2 = ctx.PROJECTS / "p" / f"{sid2}.jsonl"
p2 = {"session_id": sid2, "transcript_path": str(tp2), "cwd": str(proj)}
old = time.time() - 7200
os.utime(proj / ".claude" / "checkpoint.md", (old, old))
transcript(tp2, 700_000)
run(ctx.cmd_watch, p2)
for q in b.QUEUE.glob("*.md"):
    q.unlink()
transcript(tp2, 900_000)
check("checkpoint older than the save → not safe", run(ctx.cmd_watch, p2)["systemMessage"].startswith("⏳"))

# --- disabled -------------------------------------------------------------------------------------------
(proj / ".claude" / "project-config.json").write_text('{"context": {"enabled": false}}', encoding="utf-8")
check("project disables the watcher", run(ctx.cmd_watch, {"session_id": "sess-dddd", "transcript_path": str(tp2), "cwd": str(proj)}) == "")
(proj / ".claude" / "project-config.json").unlink()

# --- resume after /clear -------------------------------------------------------------------------------
pbrain, _ = b.project_brain(b.project_root(proj))
(pbrain / "semantic").mkdir(parents=True, exist_ok=True)
(pbrain / "semantic" / "a-gotcha.md").write_text("---\ntitle: A fresh gotcha\n---\nbody\n", encoding="utf-8")
(proj / ".claude" / "checkpoint.md").write_text("# Checkpoint\n" + "x" * 8000, encoding="utf-8")
out = run(ctx.cmd_resume, {"cwd": str(proj), "source": "clear"})
ac = out["hookSpecificOutput"]["additionalContext"]
check("resume injects checkpoint and fresh notes", "Checkpoint de la tarea" in ac and "A fresh gotcha" in ac)
check("resume stays under the SessionStart cap", len(ac) <= 9500 and "recortado" in ac)
check("resume event name", out["hookSpecificOutput"]["hookEventName"] == "SessionStart")
empty = tmp / "empty-project"
(empty / ".git").mkdir(parents=True)
check("nothing saved → resume silent", run(ctx.cmd_resume, {"cwd": str(empty), "source": "clear"}) == "")

# --- status line ----------------------------------------------------------------------------------------
line = run(ctx.cmd_statusline, {"session_id": sid, "cwd": str(proj),
                                 "context_window": {"used_percentage": 72.4, "context_window_size": 1_000_000}})
check("status line text", line.startswith("Eden · ctx 72 %") and "🧠" in line)
check("status line records the exact reading", ctx.measure(sid, str(tp), cfg)["pct"] == 72.4)
check("status line before first call", run(ctx.cmd_statusline, {"session_id": "x"}) == "Eden · ctx —")

# --- without a brain: checkpoint only -----------------------------------------------------------------
import shutil
shutil.rmtree(b.BRAIN)
ctx.CLAUDE_DIR = tmp / "home" / ".claude"
sid3 = "sess-eeee5555"
tp3 = ctx.PROJECTS / "p" / f"{sid3}.jsonl"
transcript(tp3, 650_000)
out = run(ctx.cmd_watch, {"session_id": sid3, "transcript_path": str(tp3), "cwd": str(proj)})
check("no brain → still asks for the checkpoint", "sin cerebro" in out["systemMessage"] and "additionalContext" in out["hookSpecificOutput"])
(proj / ".claude" / "checkpoint.md").write_text("# fresh\n", encoding="utf-8")
transcript(tp3, 850_000)
check("no brain + fresh checkpoint → safe", run(ctx.cmd_watch, {"session_id": sid3, "transcript_path": str(tp3), "cwd": str(proj)})["systemMessage"].startswith("✅"))

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
