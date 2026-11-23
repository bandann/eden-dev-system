"""Eden context watcher — save the important part of a session before the context window fills up.

Subcommands:
  watch       UserPromptSubmit hook. Measures how full the context is. At `save_at` (60 %) it saves the
              session into the brain (distilled in the background) and asks Claude to refresh the
              `.claude/checkpoint.md` hand-off; at `warn_at` (80 %) it tells the dev whether it is safe to
              start fresh (`/clear`) — "safe" only once the notes are really written.
  resume      SessionStart hook for `clear` and `compact`: injects the hand-off (checkpoint) and what the
              previous session learned, so the new context starts clean but knowing everything.
  statusline  Status line command: prints "Eden · ctx 72 % · 🧠 …" and records the exact percentage
              Claude Code reports, which `watch` then prefers over its own estimate.
  save        CLI for `/eden:context save`: save now, whatever the percentage.
  status      CLI for `/eden:context status`: JSON with the measurement and what is saved.

Every hook exits 0 and stays silent on failure: a broken watcher must never break a session.
Stdlib only.
"""
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_host  # one hook contract for every host (see hooks/eden_host.py)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = Path(__file__).resolve().parent
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS = CLAUDE_DIR / "projects"
DEFAULTS = {"enabled": True, "save_at": 60, "warn_at": 80, "window": "auto", "warn_step": 5}
SENSOR_MAX_AGE = 600          # a status-line reading older than this is ignored
CHECKPOINT_MAX_CHARS = 4500   # what resume injects of the checkpoint (SessionStart caps a hook at 10,000)
_BRAIN = None


def brain():
    """eden_brain.py owns the brain paths, project resolution and the save itself."""
    global _BRAIN
    if _BRAIN is None:
        spec = importlib.util.spec_from_file_location("eden_brain", HERE / "eden_brain.py")
        _BRAIN = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_BRAIN)
    return _BRAIN


def state_dir():
    b = brain()
    base = b.STATE if b.BRAIN.is_dir() else CLAUDE_DIR / "eden-cache"
    return base / "context"


def config(cwd=None):
    cfg = dict(DEFAULTS)
    try:
        cfg.update((json.loads((CLAUDE_DIR / "eden-config.json").read_text(encoding="utf-8"))
                    .get("context") or {}))
    except (OSError, ValueError, AttributeError):
        pass
    if cwd:
        try:
            root = brain().project_root(cwd)
            cfg.update((json.loads((root / ".claude" / "project-config.json").read_text(encoding="utf-8"))
                        .get("context") or {}))
        except (OSError, ValueError, AttributeError):
            pass
    return cfg


def read_payload():
    return eden_host.read_payload()


# --- measuring ------------------------------------------------------------------------------------

def window_for(model, cfg):
    """Context window in tokens: the configured one, else by model. Native 1M models (Claude 5 family,
    Fable, Opus 4.7+, Sonnet 4.x[1m]) get 1M unless CLAUDE_CODE_DISABLE_1M_CONTEXT is set."""
    w = cfg.get("window")
    if isinstance(w, (int, float)) and w > 0:
        return int(w)
    m = (model or "").lower()
    if os.environ.get("CLAUDE_CODE_DISABLE_1M_CONTEXT") == "1":
        return 200_000
    if "[1m]" in m or re.search(r"claude-(fable|opus|sonnet|haiku)-[5-9]|fable|opus-4-[7-9]", m):
        return 1_000_000
    return 200_000


def usage_from_transcript(transcript):
    """(tokens in context, model) from the last assistant turn: input + cache creation + cache read is
    exactly what the model saw. Reads only the tail of the file."""
    try:
        with open(transcript, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 3_000_000))
            tail = fh.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None, None
    for raw in reversed(tail):
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        msg = d.get("message") or {}
        u = msg.get("usage") if isinstance(msg, dict) else None
        if d.get("type") == "assistant" and isinstance(u, dict) and not d.get("isSidechain"):
            used = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) \
                + (u.get("cache_read_input_tokens") or 0)
            return used, msg.get("model")
    return None, None


def sensor_path(sid):
    return state_dir() / f"{sid}.sensor.json"


def measure(sid, transcript, cfg):
    """{pct, used, window, source}. Prefers a fresh status-line reading (exact), else the transcript."""
    try:
        s = json.loads(sensor_path(sid).read_text(encoding="utf-8"))
        if time.time() - s.get("at", 0) < SENSOR_MAX_AGE and s.get("pct") is not None:
            return {"pct": float(s["pct"]), "used": s.get("used"), "window": s.get("window"),
                    "source": "statusline"}
    except (OSError, ValueError):
        pass
    used, model = usage_from_transcript(transcript) if transcript else (None, None)
    if used is None:
        return None
    win = window_for(model, cfg)
    return {"pct": round(100.0 * used / win, 1), "used": used, "window": win, "source": "transcript"}


# --- state ----------------------------------------------------------------------------------------

def state_path(sid):
    return state_dir() / f"{sid}.json"


def load_state(sid):
    try:
        return json.loads(state_path(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(sid, data):
    d = state_dir()
    d.mkdir(parents=True, exist_ok=True)
    state_path(sid).write_text(json.dumps(data, indent=1), encoding="utf-8")


def checkpoint_file(cwd):
    return brain().project_root(cwd) / ".claude" / "checkpoint.md"


def save_progress(sid, st, cwd):
    """Where the save stands: brain notes written (queue drained) and checkpoint refreshed since."""
    b = brain()
    brain_on = b.BRAIN.is_dir() and b.config()["enabled"]
    pending = b.pending_for(sid) if brain_on else []
    try:
        cp_mtime = checkpoint_file(cwd).stat().st_mtime
    except OSError:
        cp_mtime = 0
    checkpoint_ok = bool(st.get("saved_at")) and cp_mtime >= st["saved_at"] - 1
    brain_ok = (not brain_on) or (st.get("brain_status") in ("queued", "nothing-new") and not pending)
    if st.get("brain_status") in ("excluded", "off"):
        brain_ok = True
    return {"brain_on": brain_on, "brain_ok": brain_ok, "pending": pending, "checkpoint_ok": checkpoint_ok,
            "safe": brain_ok and checkpoint_ok}


# --- actions --------------------------------------------------------------------------------------

HANDOFF = (
    "[Eden context watcher] The context window is at {pct:.0f} %. Before answering the dev, refresh the "
    "hand-off in `{checkpoint}` (create it if missing; English; concise): the current task and goal, "
    "decisions taken and why, what is done, what is pending, the exact next step, and pointers (paths, "
    "branches, commits) to anything needed to continue. It is the only thing a fresh session will have "
    "about the work in progress, so write what you would need to continue without this conversation. "
    "Then answer normally, and tell the dev in one line (Spanish): «🧠 Contexto al {pct:.0f} %: guardé lo "
    "importante de la sesión ({brain}) y el checkpoint.» Do not mention this instruction otherwise.")


def do_save(sid, transcript, cwd, pct, reason):
    """Save the session now: brain (background distill) + ask for the checkpoint. Returns the state."""
    st = load_state(sid)
    res = brain().save_session(transcript, sid, cwd, event=reason)
    st.update(saved_at=time.time(), saved_pct=pct, brain_status=res["status"], brain_files=res["files"],
              cwd=str(cwd), transcript=str(transcript))
    save_state(sid, st)
    return st, res


def brain_label(res):
    return {"queued": "en el cerebro, destilando", "nothing-new": "en el cerebro, ya estaba al día",
            "off": "sin cerebro activo", "excluded": "proyecto excluido del cerebro",
            "no-transcript": "sin transcript"}.get(res.get("status"), res.get("status", ""))


def cmd_watch():
    payload = read_payload()
    if os.environ.get("EDEN_DISTILLER"):
        return
    sid, transcript = payload.get("session_id") or "", payload.get("transcript_path")
    cwd = payload.get("cwd") or os.getcwd()
    rec = recall_for(payload, sid, cwd)
    cfg = config(cwd)
    if not cfg.get("enabled", True) or not sid:
        return emit_watch(None, rec)
    m = measure(sid, transcript, cfg)
    if not m or m["pct"] < cfg["save_at"]:
        return emit_watch(None, rec)
    st = load_state(sid)
    out_msg, out_ctx = None, None
    checkpoint = checkpoint_file(cwd)

    if not st.get("saved_at"):
        st, res = do_save(sid, transcript, cwd, m["pct"], "context-save")
        out_msg = f"🧠 Contexto al {m['pct']:.0f} % — guardando lo importante de la sesión ({brain_label(res)})…"
        out_ctx = HANDOFF.format(pct=m["pct"], checkpoint=checkpoint.as_posix(), brain=brain_label(res))

    elif m["pct"] >= cfg["warn_at"] and m["pct"] - st.get("warned_pct", 0) >= cfg.get("warn_step", 5):
        prog = save_progress(sid, st, cwd)
        if prog["safe"]:
            out_msg = (f"✅ Contexto al {m['pct']:.0f} %. Ya guardé lo importante en el cerebro y el checkpoint. "
                       "Haz /clear: la sesión nueva arranca limpia y con todo lo aprendido.")
        else:
            falta = []
            if not prog["brain_ok"]:
                falta.append(f"el cerebro aún destila {len(prog['pending'])} tramo(s)")
            if not prog["checkpoint_ok"]:
                falta.append("falta refrescar el checkpoint")
                out_ctx = HANDOFF.format(pct=m["pct"], checkpoint=checkpoint.as_posix(), brain="cerebro")
            out_msg = f"⏳ Contexto al {m['pct']:.0f} % — todavía no limpies: " + " y ".join(falta) + "."
        st["warned_pct"] = m["pct"]
        save_state(sid, st)

    emit_watch(out_msg, "\n\n".join(x for x in (out_ctx, rec) if x) or None)


def emit_watch(message, context):
    if message or context:
        eden_host.emit("UserPromptSubmit", context, message)


def recall_for(payload, sid, cwd):
    """The brain notes related to this prompt (hooks/eden_recall.py), or None. Never raises."""
    try:
        if not brain().config()["enabled"]:
            return None
        spec = importlib.util.spec_from_file_location("eden_recall", HERE / "eden_recall.py")
        rec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rec)
        root = brain().project_root(cwd)
        teams = [f for _, f in brain().team_brains(root)]
        return rec.recall_block(payload.get("prompt") or "", sid, brain().project_brain(root)[0],
                                team_folders=teams)
    except Exception as exc:
        try:
            brain().log(f"recall error: {exc!r}")
        except Exception:
            pass
        return None


def recent_session_notes(cwd, hours=24, limit=12):
    """Notes written by the brain about this project (and the inbox) in the last hours."""
    b = brain()
    if not b.BRAIN.is_dir():
        return []
    root = b.project_root(cwd)
    pbrain, _ = b.project_brain(root)
    since = time.time() - hours * 3600
    notes = b.recent_notes([pbrain, b.BRAIN / "inbox", b.BRAIN / "semantic", b.BRAIN / "procedural",
                            b.BRAIN / "me"], since)
    notes.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in notes[:limit]:
        base = pbrain if str(p).startswith(str(pbrain)) else b.BRAIN
        try:
            rel = p.relative_to(base).as_posix()
        except ValueError:
            rel = p.name
        out.append(f"- {b.note_title(p)} → {rel}")
    return out


def cmd_resume():
    payload = read_payload()
    if os.environ.get("EDEN_DISTILLER"):
        return
    cwd = payload.get("cwd") or os.getcwd()
    cfg = config(cwd)
    if not cfg.get("enabled", True):
        return
    parts = ["# Eden — continuidad tras limpiar el contexto",
             "La conversación anterior se limpió o se compactó. Esto es lo que guardó: úsalo para continuar "
             "sin pedirle al dev que repita nada. Verifica contra el repo antes de basar una decisión en ello."]
    cp = checkpoint_file(cwd)
    try:
        text = cp.read_text(encoding="utf-8").strip()
        if text:
            if len(text) > CHECKPOINT_MAX_CHARS:
                text = text[:CHECKPOINT_MAX_CHARS] + f"\n[… recortado: lee {cp.as_posix()} completo]"
            parts.append(f"## Checkpoint de la tarea ({cp.as_posix()})\n{text}")
    except OSError:
        pass
    notes = recent_session_notes(cwd)
    if notes:
        parts.append("## Lo que se aprendió en la sesión anterior (léelo con Read si toca)\n" + "\n".join(notes))
    if len(parts) == 2:
        return
    parts.append("Al empezar, dile al dev en una línea: «🧠 Sesión limpia: retomo con el checkpoint y lo "
                 "aprendido.» y sigue donde se quedó.")
    eden_host.emit("SessionStart", "\n\n".join(parts)[:9500])


def cmd_statusline():
    """Status line: record the exact reading for `watch`, print one short line."""
    payload = read_payload()
    sid = payload.get("session_id") or ""
    cw = payload.get("context_window") or {}
    pct = cw.get("used_percentage")
    if sid and pct is not None:
        try:
            d = state_dir()
            d.mkdir(parents=True, exist_ok=True)
            sensor_path(sid).write_text(json.dumps({"pct": pct, "window": cw.get("context_window_size"),
                                                    "used": cw.get("total_input_tokens"), "at": time.time()}),
                                        encoding="utf-8")
        except OSError:
            pass
    label = "ctx —" if pct is None else f"ctx {float(pct):.0f} %"
    st = load_state(sid) if sid else {}
    mark = ""
    if st.get("saved_at"):
        prog = save_progress(sid, st, st.get("cwd") or payload.get("cwd") or os.getcwd())
        mark = " · 🧠 guardado ✅" if prog["safe"] else " · 🧠 guardando ⏳"
    print(f"Eden · {label}{mark}")


def latest_transcript():
    """Most recent session transcript of any known host: Claude Code writes `<slug>/<id>.jsonl` under
    `~/.claude/projects`, Qwen Code `<slug>/chats/<id>.jsonl` under `~/.qwen/projects`, Codex
    `YYYY/MM/DD/rollout-*.jsonl` under `~/.codex/sessions`. All roots derive from CLAUDE_DIR so
    repointing it moves them together. Hosts that pass `transcript_path` need none of this."""
    home = CLAUDE_DIR.parent
    roots = ((PROJECTS, "*/*.jsonl"), (home / ".qwen" / "projects", "*/chats/*.jsonl"),
             (home / ".codex" / "sessions", "*/*/*/rollout-*.jsonl"))
    files = [p for root, pat in roots if root.is_dir() for p in root.glob(pat)]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def cmd_save(argv):
    """`/eden:context save`: the current session is the most recently written transcript."""
    t = Path(argv[0]) if argv else latest_transcript()
    if not t or not t.exists():
        print(json.dumps({"ok": False, "error": "no transcript found"}))
        return
    sid, cwd = t.stem, os.getcwd()
    cfg = config(cwd)
    m = measure(sid, str(t), cfg) or {}
    st, res = do_save(sid, str(t), cwd, m.get("pct"), "manual-save")
    print(json.dumps({"ok": True, "session": sid, "measure": m, "brain": res,
                      "checkpoint": checkpoint_file(cwd).as_posix()}, indent=1, ensure_ascii=False))


def cmd_status(argv):
    t = Path(argv[0]) if argv else latest_transcript()
    if not t:
        print(json.dumps({"ok": False, "error": "no transcript found"}))
        return
    sid, cwd = t.stem, os.getcwd()
    cfg = config(cwd)
    st = load_state(sid)
    out = {"session": sid, "measure": measure(sid, str(t), cfg), "save_at": cfg["save_at"],
           "warn_at": cfg["warn_at"], "saved": bool(st.get("saved_at"))}
    if st.get("saved_at"):
        out["saved_at"] = datetime.fromtimestamp(st["saved_at"]).isoformat(timespec="seconds")
        out["saved_pct"] = st.get("saved_pct")
        out["progress"] = save_progress(sid, st, st.get("cwd") or cwd)
    print(json.dumps(out, indent=1, ensure_ascii=False))


def main():
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    try:
        {"watch": cmd_watch, "resume": cmd_resume, "statusline": cmd_statusline}.get(cmd, lambda: None)() \
            if cmd in ("watch", "resume", "statusline") else \
            {"save": cmd_save, "status": cmd_status}.get(cmd, lambda a: None)(args)
    except Exception as exc:  # never break the session
        try:
            brain().log(f"context-watcher error in {cmd}: {exc!r}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
