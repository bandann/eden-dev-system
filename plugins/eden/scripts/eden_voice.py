#!/usr/bin/env python3
"""Eden voice-over for explain videos: one audio clip per beat, so every beat lasts exactly what is said.

Providers (`video.tts.provider` in ~/.claude/eden-config.json):

    auto        Kokoro if it is installed, else the system voice. Never a paid API on its own.
    system      the OS voice: Windows SAPI (PowerShell), macOS `say`, Linux `espeak-ng`/`espeak`. Offline, free.
    kokoro      Kokoro-82M (Apache-2.0), local and offline, much better quality. Runs in its own venv
                (~/.eden/tts/venv, Python 3.12): `eden_voice.py setup-kokoro` creates it — the dev decides.
                Voices: af_heart, am_michael, bf_emma, ef_dora (es), em_alex (es)…
    openai      OpenAI speech API, key from OPENAI_API_KEY (or `video.tts.key_env`). The narration text leaves
                the machine: only when the dev set this provider.
    elevenlabs  ElevenLabs, key from ELEVENLABS_API_KEY (or `key_env`); `voice` is the voice id. Same caveat.

Writes, inside the video folder:
    audio/beat-01.wav …     one clip per beat
    audio/voice.wav         the whole track, each clip at its beat's start
    audio/voice.json        provider, voice, and every beat's text hash and duration (render uses these)

Stdlib only (Kokoro brings its own packages). Keys are read from the environment, never written anywhere.
"""
import array
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

LEAD = 0.12      # silence before each beat's clip
TAIL = 0.28      # silence after it, before the next beat
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
KOKORO_LANG = {"en": "a", "en-us": "a", "en-gb": "b", "es": "e", "fr": "f", "it": "i", "pt": "p", "ja": "j", "zh": "z", "hi": "h"}
KOKORO_VOICE = {"a": "af_heart", "b": "bf_emma", "e": "ef_dora", "f": "ff_siwis", "i": "if_sara", "p": "pf_dora",
                "j": "jf_alpha", "z": "zf_xiaobei", "h": "hf_alpha"}


def plain(say):
    return re.sub(r"\s+", " ", (say or "").replace("*", "")).strip()


def text_hash(say):
    return hashlib.sha1(plain(say).encode("utf-8")).hexdigest()[:12]


def config():
    try:
        data = json.loads((Path.home() / ".claude" / "eden-config.json").read_text(encoding="utf-8"))
        return ((data.get("video") or {}).get("tts") or {})
    except (OSError, ValueError, AttributeError):
        return {}


TTS_HOME = Path.home() / ".eden" / "tts"
# Kokoro's dependencies, pinned to builds that load under Windows Smart App Control (newer `regex` and
# `spacy` wheels are blocked until they gain reputation) and that run on Python 3.12.
KOKORO_PINS = ["kokoro", "soundfile", "regex==2024.11.6", "spacy==3.7.5", "transformers==4.46.3"]


def kokoro_python(cfg=None):
    """The interpreter that has Kokoro: `video.tts.python`, else Eden's own venv (~/.eden/tts/venv), else
    this Python when it can import kokoro. None when there is none."""
    cfg = cfg if cfg is not None else config()
    if cfg.get("python") and Path(os.path.expanduser(cfg["python"])).exists():
        return str(Path(os.path.expanduser(cfg["python"])))
    venv = TTS_HOME / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if venv.exists():
        return str(venv)
    import importlib.util
    return sys.executable if importlib.util.find_spec("kokoro") else None


def kokoro_available(cfg=None):
    return kokoro_python(cfg) is not None


KOKORO_WORKER = r"""
import json, sys, numpy as np, soundfile as sf, warnings
warnings.filterwarnings("ignore")
from kokoro import KPipeline
job = json.load(open(sys.argv[1], encoding="utf-8"))
pipe = KPipeline(lang_code=job["lang"], repo_id="hexgrad/Kokoro-82M")
for it in job["items"]:
    parts = [np.asarray(a, dtype=np.float32).reshape(-1) for _, _, a in pipe(it["t"], voice=job["voice"], speed=job["speed"])]
    audio = np.concatenate(parts) if parts else np.zeros(1, np.float32)
    sf.write(it["o"], np.clip(audio, -1, 1), 24000, subtype="PCM_16")
print("ok")
"""


def setup_kokoro(python_312=None):
    """Create ~/.eden/tts/venv with Python 3.12 and install Kokoro with the pinned builds. Only when the dev
    asks for it (it downloads ~1 GB with torch and the voice model)."""
    TTS_HOME.mkdir(parents=True, exist_ok=True)
    venv = TTS_HOME / "venv"
    if not venv.exists():
        base = python_312 or (["py", "-V:3.12"] if os.name == "nt" and shutil.which("py") else [shutil.which("python3.12") or "python3.12"])
        base = base if isinstance(base, list) else [base]
        subprocess.run(base + ["-m", "venv", str(venv)], check=True, timeout=600)
    py = kokoro_python({})
    subprocess.run([py, "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=True, timeout=900)
    subprocess.run([py, "-m", "pip", "install", "--quiet", *KOKORO_PINS], check=True, timeout=3600)
    return py


def resolve_provider(cfg):
    p = (cfg.get("provider") or "auto").lower()
    if p == "auto":
        return "kokoro" if kokoro_available(cfg) else "system"
    return p


# --- wav helpers ----------------------------------------------------------------------------------

def wav_info(path):
    with wave.open(str(path), "rb") as w:
        return w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes() / float(w.getframerate())


def write_pcm16(path, samples, rate):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes() if hasattr(samples, "tobytes") else bytes(samples))


def read_mono16(path):
    """(array('h'), rate). Mixes stereo down; only 16-bit PCM (what every provider here produces)."""
    with wave.open(str(path), "rb") as w:
        ch, sw, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError(f"{path}: {8 * sw}-bit audio, expected 16-bit PCM")
    a = array.array("h")
    a.frombytes(raw)
    if sys.byteorder == "big":
        a.byteswap()
    if ch == 2:
        a = array.array("h", ((a[i] + a[i + 1]) // 2 for i in range(0, len(a), 2)))
    return a, rate


def resample(a, src, dst):
    if src == dst:
        return a
    n = int(len(a) * dst / src)
    step = src / dst
    return array.array("h", (a[min(int(i * step), len(a) - 1)] for i in range(n)))


# --- providers ------------------------------------------------------------------------------------

def say_system(texts, outs, voice=None, rate=0):
    if os.name == "nt":
        items = [{"t": t, "o": str(o)} for t, o in zip(texts, outs)]
        job = Path(outs[0]).parent / ".tts-job.json"
        job.write_text(json.dumps(items), encoding="utf-8")
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            + (f"try {{ $s.SelectVoice('{voice}') }} catch {{}};" if voice and re.match(r"^[\w .()-]+$", voice) else "")
            + f"$s.Rate = {int(rate)};"
            "$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono);"
            f"$items = Get-Content -Raw -Encoding UTF8 '{job}' | ConvertFrom-Json;"
            "foreach ($i in $items) { $s.SetOutputToWaveFile($i.o, $fmt); $s.Speak($i.t) };"
            "$s.SetOutputToNull(); $s.Dispose()"
        )
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True,
                           text=True, timeout=600, creationflags=NO_WINDOW)
        job.unlink(missing_ok=True)
        if r.returncode:
            raise RuntimeError("Windows speech failed: " + (r.stderr or r.stdout)[-300:])
        return
    say = shutil.which("say")
    if say:
        for t, o in zip(texts, outs):
            args = [say, "-o", str(o), "--file-format=WAVE", "--data-format=LEI16@22050"] + (["-v", voice] if voice else [])
            subprocess.run(args + [t], check=True, timeout=120)
        return
    esp = shutil.which("espeak-ng") or shutil.which("espeak")
    if not esp:
        raise RuntimeError("no system voice found (Windows SAPI, macOS say, or espeak-ng)")
    for t, o in zip(texts, outs):
        subprocess.run([esp, "-w", str(o)] + (["-v", voice] if voice else []) + [t], check=True, timeout=120)


def say_kokoro(texts, outs, voice=None, lang="en", speed=1.0, cfg=None):
    """Runs in Kokoro's own interpreter (a separate venv), one process for all the beats."""
    py = kokoro_python(cfg)
    if not py:
        raise RuntimeError("Kokoro is not installed: `eden_voice.py setup-kokoro` (the dev decides), or use provider system")
    code = KOKORO_LANG.get((lang or "en").lower(), "a")
    job = Path(outs[0]).parent / ".kokoro-job.json"
    job.write_text(json.dumps({"lang": code, "voice": voice or KOKORO_VOICE.get(code, "af_heart"), "speed": float(speed),
                               "items": [{"t": t, "o": str(o)} for t, o in zip(texts, outs)]}), encoding="utf-8")
    try:
        r = subprocess.run([py, "-c", KOKORO_WORKER, str(job)], capture_output=True, text=True, timeout=3600,
                           creationflags=NO_WINDOW, encoding="utf-8", errors="replace")
    finally:
        job.unlink(missing_ok=True)
    if r.returncode or "ok" not in r.stdout:
        raise RuntimeError("Kokoro failed: " + (r.stderr or r.stdout)[-400:])


def _post(url, headers, body, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def say_openai(texts, outs, voice=None, cfg=None):
    cfg = cfg or {}
    key = os.environ.get(cfg.get("key_env") or "OPENAI_API_KEY")
    if not key:
        raise RuntimeError(f"missing environment variable {cfg.get('key_env') or 'OPENAI_API_KEY'}")
    base = (cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    for t, o in zip(texts, outs):
        data = _post(f"{base}/audio/speech", {"Authorization": f"Bearer {key}"},
                     {"model": cfg.get("model") or "gpt-4o-mini-tts", "voice": voice or "alloy", "input": t,
                      "response_format": "wav", **({"instructions": cfg["instructions"]} if cfg.get("instructions") else {})})
        Path(o).write_bytes(data)


def say_elevenlabs(texts, outs, voice=None, cfg=None):
    cfg = cfg or {}
    key = os.environ.get(cfg.get("key_env") or "ELEVENLABS_API_KEY")
    if not key or not voice:
        raise RuntimeError("ElevenLabs needs ELEVENLABS_API_KEY and `video.tts.voice` (a voice id)")
    if not re.match(r"^[A-Za-z0-9]+$", voice):
        raise RuntimeError("ElevenLabs voice must be a voice id")
    for t, o in zip(texts, outs):
        pcm = _post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000", {"xi-api-key": key},
                    {"text": t, "model_id": cfg.get("model") or "eleven_multilingual_v2"})
        a = array.array("h")
        a.frombytes(pcm[: len(pcm) // 2 * 2])
        write_pcm16(o, a, 24000)


# --- the job --------------------------------------------------------------------------------------

def synthesize(spec, folder, provider=None, voice=None, lang=None):
    """Make audio/beat-NN.wav for every beat whose text or voice changed, then the full track.
    Returns the manifest (also written to audio/voice.json)."""
    cfg = config()
    provider = (provider or resolve_provider(cfg)).lower()
    voice = voice or cfg.get("voice")
    lang = lang or spec.get("lang") or "en"
    folder = Path(folder)
    adir = folder / "audio"
    adir.mkdir(exist_ok=True)
    old = {}
    try:
        old = json.loads((adir / "voice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    same_voice = old.get("provider") == provider and old.get("voice") == voice
    beats = spec["beats"]
    todo_t, todo_o = [], []
    for i, b in enumerate(beats, 1):
        o = adir / f"beat-{i:02d}.wav"
        prev = (old.get("beats") or [None] * len(beats))[i - 1] if i - 1 < len(old.get("beats") or []) else None
        if same_voice and prev and prev.get("hash") == text_hash(b.get("say")) and o.exists():
            continue  # unchanged: keep the clip (re-narrating costs time, and money with an API)
        if plain(b.get("say")):
            todo_t.append(plain(b.get("say")))
            todo_o.append(o)
    if todo_t:
        if provider == "system":
            say_system(todo_t, todo_o, voice, cfg.get("rate", 0))
        elif provider == "kokoro":
            say_kokoro(todo_t, todo_o, voice, lang, cfg.get("speed", 1.0), cfg)
        elif provider == "openai":
            say_openai(todo_t, todo_o, voice, cfg)
        elif provider == "elevenlabs":
            say_elevenlabs(todo_t, todo_o, voice, cfg)
        else:
            raise RuntimeError(f"unknown TTS provider {provider!r} (auto, system, kokoro, openai, elevenlabs)")
    entries, rate = [], None
    for i, b in enumerate(beats, 1):
        o = adir / f"beat-{i:02d}.wav"
        if o.exists():
            ch, sw, r, dur = wav_info(o)
            rate = rate or r
        else:
            dur = 0.0
        entries.append({"file": o.name if o.exists() else None, "hash": text_hash(b.get("say")),
                        "speech": round(dur, 3), "duration": round(max(dur + LEAD + TAIL, 1.2), 3)})
    manifest = {"provider": provider, "voice": voice, "lang": lang, "rate": rate or 22050, "beats": entries}
    build_track(folder, manifest)
    (adir / "voice.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def build_track(folder, manifest):
    """audio/voice.wav: every clip at its beat's start (+LEAD), silence elsewhere, one sample rate."""
    adir = Path(folder) / "audio"
    rate = manifest["rate"]
    track = array.array("h")
    for e in manifest["beats"]:
        seg = array.array("h", [0]) * int(round(e["duration"] * rate))
        if e["file"]:
            clip, r = read_mono16(adir / e["file"])
            clip = resample(clip, r, rate)
            at = int(LEAD * rate)
            n = min(len(clip), len(seg) - at)
            seg[at:at + n] = clip[:n]
        track.extend(seg)
    if sys.byteorder == "big":
        track.byteswap()
    write_pcm16(adir / "voice.wav", track, rate)


def durations_for(spec, folder):
    """Beat durations from audio/voice.json when it matches the script's text; None if it does not."""
    try:
        m = json.loads((Path(folder) / "audio" / "voice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    beats = spec.get("beats") or []
    if len(m.get("beats") or []) != len(beats):
        return None
    if any(e["hash"] != text_hash(b.get("say")) for e, b in zip(m["beats"], beats)):
        return None
    return [e["duration"] for e in m["beats"]]


if __name__ == "__main__":
    if sys.argv[1:2] == ["setup-kokoro"]:
        print(json.dumps({"ok": True, "python": setup_kokoro()}))
    elif sys.argv[1:2] == ["status"]:
        c = config()
        print(json.dumps({"provider": resolve_provider(c), "configured": c.get("provider", "auto"),
                          "kokoro_python": kokoro_python(c)}, indent=1))
    else:
        print(__doc__)
