"""Eden AI — provider-agnostic model access for Eden's headless calls.

The only place Eden calls a model from code (today) is the brain distiller
(hooks/eden_brain.py). This module resolves WHICH model to call and HOW, so the
dev can pick any provider in ~/.claude/eden-config.json:

    "ai": {
      "provider": "claude",       // a CLI (claude | codex | gemini | qwen), an API preset
                                  // (anthropic | openai | openrouter | google | moonshot | zai |
                                  //  minimax | deepseek | dashscope | xai | ollama), an alias
                                  // (kimi, glm, grok, chatgpt, qwen-api) or a key of your own
      "model": "",                // optional; else providers[p].model, else the preset's default
      "providers": {              // optional overrides, and custom providers
        "mi-cli": {"cmd": ["mi-cli", "run", "--model", "{model}", "-"], "add_dir_flag": "--add-dir"},
        "mi-api": {"api": "openai", "base_url": "https://llm.example.com/v1",
                   "api_key_env": "MI_API_KEY", "model": "mi-modelo"}
      },
      "timeout_seconds": 900
    }

Two kinds of provider, one contract (prompt in, answer text out):

  CLI  (`cmd`): the prompt is piped to the child's stdin; the answer is its stdout.
       `{model}` inside any argv item is replaced by the model name; `add_dir_flag`
       (claude today) is repeated once per extra dir. Built-ins run read-only when
       the CLI allows it (claude: --allowedTools/--safe-mode; codex: --sandbox
       read-only); gemini/qwen have no such guard — the distill prompt forbids writes
       and apply_output() never runs their code. A CLI can read files.

  API  (`api`: "anthropic" | "openai"): one HTTPS request to `base_url` — the
       Anthropic Messages API (POST {base}/v1/messages) or the OpenAI Chat
       Completions API (POST {base}/chat/completions), which between them cover
       every vendor's compatible endpoint. The key is read from the environment
       variable named in `api_key_env` — never from the config file, never logged.
       Only https is allowed, except to localhost (ollama, LM Studio, vLLM…).
       An API call has NO tools: it cannot read files, so callers must inline what
       the model needs (see can_read()).

The learning.model fallback (default "sonnet") applies to the claude CLI only, so
a non-Claude provider never receives a Claude model name.

Default is provider "claude" with the exact arguments the distiller always used,
so an unmodified install behaves exactly as before.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
# urllib.request / urllib.error (≈25 ms with http.client and email) load only when an API is called:
# hooks import this module on every session and must stay fast.

CLAUDE_DIR = Path.home() / ".claude"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
ANTHROPIC_VERSION = "2023-06-01"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

# CLI providers. `cmd` may contain {model}; `add_dir_flag` repeats per dir.
CLI = {
    "claude": {
        "cmd": ["claude", "-p", "--model", "{model}", "--allowedTools", "Read,Glob,Grep",
                "--disallowedTools", "Write,Edit,NotebookEdit,Bash,PowerShell,WebFetch,WebSearch",
                "--safe-mode", "--no-session-persistence"],
        "add_dir_flag": "--add-dir",
        "model": "sonnet",
    },
    "codex": {
        "cmd": ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "-m", "{model}", "-"],
        "model": "",
    },
    "gemini": {"cmd": ["gemini", "-p"], "model": ""},
    "qwen": {"cmd": ["qwen", "-p"], "model": ""},
}

# API presets. An empty model means "set ai.model": vendors rename their models
# too often for the kit to pin one it cannot verify.
API = {
    "anthropic": {"api": "anthropic", "base_url": "https://api.anthropic.com",
                  "api_key_env": "ANTHROPIC_API_KEY", "auth": "x-api-key", "model": "claude-sonnet-5-5"},
    "openai": {"api": "openai", "base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_API_KEY"},
    "openrouter": {"api": "openai", "base_url": "https://openrouter.ai/api/v1",
                   "api_key_env": "OPENROUTER_API_KEY"},
    "google": {"api": "openai", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
               "api_key_env": "GEMINI_API_KEY"},
    "moonshot": {"api": "anthropic", "base_url": "https://api.moonshot.ai/anthropic",
                 "api_key_env": "MOONSHOT_API_KEY", "auth": "both"},
    "zai": {"api": "anthropic", "base_url": "https://api.z.ai/api/anthropic",
            "api_key_env": "ZAI_API_KEY", "auth": "both"},
    "minimax": {"api": "anthropic", "base_url": "https://api.minimax.io/anthropic",
                "api_key_env": "MINIMAX_API_KEY", "auth": "both"},
    "deepseek": {"api": "anthropic", "base_url": "https://api.deepseek.com/anthropic",
                 "api_key_env": "DEEPSEEK_API_KEY", "auth": "both"},
    "dashscope": {"api": "anthropic", "base_url": "https://dashscope-intl.aliyuncs.com/apps/anthropic",
                  "api_key_env": "DASHSCOPE_API_KEY", "auth": "both"},
    "xai": {"api": "openai", "base_url": "https://api.x.ai/v1", "api_key_env": "XAI_API_KEY"},
    "ollama": {"api": "openai", "base_url": "http://localhost:11434/v1", "api_key_env": ""},
}

ALIASES = {"kimi": "moonshot", "glm": "zai", "grok": "xai", "chatgpt": "openai", "qwen-api": "dashscope"}
BUILTIN = {**CLI, **API}
KNOWN = sorted(BUILTIN)


# CLIs that desktop apps bundle outside the PATH, from the host table (verified: the Codex app on
# Windows ships %LOCALAPPDATA%/OpenAI/Codex/bin/<build>/codex.exe and puts nothing on the PATH).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
import eden_hosts  # the one table of what each AI tool is (hooks/eden_hosts.py)

APP_CLI_GLOBS = {c: h["app_globs"] for h in eden_hosts.HOSTS.values() for c in h["clis"] if h["app_globs"]}


def find_cli(name):
    """Executable for a CLI name: the PATH first, then where its desktop app installs it. None if absent."""
    exe = shutil.which(name)
    if exe:
        return exe
    for env, pattern in APP_CLI_GLOBS.get(Path(name).stem.lower(), []):
        base = Path(os.environ.get(env, "")) if env != "HOME" else Path.home()
        if not str(base) or not base.is_dir():
            continue
        hits = sorted(base.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
        if hits:
            return str(hits[0])
    return None


class AIError(Exception):
    """Why a call could not even be attempted: config | missing_cli | missing_key."""

    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


def _clean(d):
    return {k: v for k, v in (d or {}).items() if not str(k).startswith("_")}


def _read_ai_section():
    try:
        data = json.loads((CLAUDE_DIR / "eden-config.json").read_text(encoding="utf-8"))
        return _clean(data.get("ai"))
    except (OSError, ValueError, AttributeError):
        return {}


def ai_config(cfg=None):
    """Merged ai section: defaults ← ~/.claude/eden-config.json 'ai' ← cfg['ai'].

    `cfg` is the caller's full config (the brain passes its learning section), whose
    `model` is kept apart as `learning_model`: it only feeds the claude CLI."""
    ai = dict(_read_ai_section())
    learning_model = ""
    if isinstance(cfg, dict):
        ai.update(_clean(cfg.get("ai")))
        learning_model = cfg.get("model") or ""
    ai["provider"] = ALIASES.get(ai.get("provider") or "claude", ai.get("provider") or "claude")
    ai.setdefault("model", "")
    ai["providers"] = _clean(ai.get("providers"))
    ai.setdefault("timeout_seconds", 900)
    ai["learning_model"] = learning_model
    return ai


def provider_config(ai, provider=None):
    """Built-in defaults ← user overrides for that provider. Custom keys need 'cmd' or 'api'."""
    provider = ALIASES.get(provider, provider) if provider else ai.get("provider") or "claude"
    user = ai.get("providers", {}).get(provider)
    if not isinstance(user, dict):
        if provider not in BUILTIN:
            raise AIError("config", f"proveedor de IA '{provider}' desconocido: defínelo en "
                                    "eden-config.json → ai.providers con 'cmd' (un CLI) o 'api' (una API)")
        user = {}
    merged = dict(BUILTIN.get(provider, {}))
    merged.update(_clean(user))
    merged["name"] = provider
    if merged.get("api"):
        if merged["api"] not in ("anthropic", "openai"):
            raise AIError("config", f"proveedor '{provider}': 'api' debe ser anthropic u openai")
        if not merged.get("base_url"):
            raise AIError("config", f"proveedor '{provider}' sin 'base_url'")
    elif not merged.get("cmd"):
        raise AIError("config", f"proveedor de IA '{provider}' sin 'cmd' ni 'api'")
    return merged


def is_api(pc):
    return bool(pc.get("api"))


def can_read(ai, provider=None):
    """True when the provider can open files itself (a CLI with read tools). An API
    call — or a CLI declared with "tools": false — needs its inputs inline."""
    pc = provider_config(ai, provider)
    return not is_api(pc) and pc.get("tools", True) is not False


def model_for(ai, pc, model=None):
    """explicit > ai.model > providers[p].model > learning.model (claude CLI only) > preset."""
    user_model = (ai.get("providers", {}).get(pc["name"]) or {}).get("model")
    learning = ai.get("learning_model") if pc["name"] == "claude" else ""
    return model or ai.get("model") or user_model or learning or BUILTIN.get(pc["name"], {}).get("model") or ""


def resolve(ai, provider=None, model=None, add_dirs=()):
    """Full argv for a CLI call: substitute {model}, resolve the executable on PATH,
    repeat the add-dir flag per directory. Raises AIError('missing_cli')."""
    pc = provider_config(ai, provider)
    if is_api(pc):
        raise AIError("config", f"'{pc['name']}' es una API, no un CLI")
    model = model_for(ai, pc, model)
    cmd = list(pc["cmd"])
    if not model:  # no model chosen: drop `-m {model}` / `--model {model}` so the CLI uses its own default
        cmd = [c for i, c in enumerate(cmd) if c != "{model}" and not (i + 1 < len(cmd) and cmd[i + 1] == "{model}")]
    args = [a.replace("{model}", model) for a in cmd]
    exe = find_cli(args[0])
    if not exe:
        raise AIError("missing_cli", f"el CLI '{args[0]}' del proveedor de IA no está en el PATH")
    args[0] = exe
    flag = pc.get("add_dir_flag")
    if flag:
        for d in add_dirs:
            args += [flag, str(d)]
    return args


def check_url(base_url):
    u = urlparse(base_url)
    if u.scheme == "https" and u.hostname:
        return
    if u.scheme == "http" and u.hostname in LOCAL_HOSTS:
        return
    raise AIError("config", f"base_url no permitida: '{base_url}' (solo https, o http a localhost)")


def api_request(ai, provider=None, model=None, prompt=""):
    """(url, headers, body) for an API provider. Raises AIError for config/missing key.
    Split out from run() so the request shape is testable without a network."""
    pc = provider_config(ai, provider)
    if not is_api(pc):
        raise AIError("config", f"'{pc['name']}' es un CLI, no una API")
    base = pc["base_url"].rstrip("/")
    check_url(base)
    model = model_for(ai, pc, model)
    if not model:
        raise AIError("config", f"el proveedor '{pc['name']}' necesita un modelo: pon ai.model en eden-config.json")
    key_env = pc.get("api_key_env") or ""
    key = os.environ.get(key_env, "") if key_env else ""
    if key_env and not key:
        raise AIError("missing_key", f"falta la variable de entorno {key_env} con la clave de '{pc['name']}'")
    headers = {"content-type": "application/json", "user-agent": "eden-kit"}
    headers.update({str(k): str(v) for k, v in _clean(pc.get("headers")).items()})
    messages = [{"role": "user", "content": prompt}]
    if pc["api"] == "anthropic":
        url = base + "/v1/messages"
        headers["anthropic-version"] = ANTHROPIC_VERSION
        auth = pc.get("auth", "x-api-key")
        if key and auth in ("x-api-key", "both"):
            headers["x-api-key"] = key
        if key and auth in ("bearer", "both"):
            headers["authorization"] = f"Bearer {key}"
        body = {"model": model, "max_tokens": int(pc.get("max_tokens") or 8192), "messages": messages}
    else:
        url = base + "/chat/completions"
        if key:
            headers["authorization"] = f"Bearer {key}"
        body = {"model": model, "messages": messages}
        if pc.get("max_tokens"):
            body["max_tokens"] = int(pc["max_tokens"])
    return url, headers, body


def parse_reply(api, data):
    """Answer text from an Anthropic or OpenAI-style JSON reply (reasoning blocks dropped)."""
    if api == "anthropic":
        return "".join(b.get("text", "") for b in data.get("content") or [] if b.get("type") == "text")
    choices = data.get("choices") or [{}]
    content = (choices[0].get("message") or {}).get("content") or ""
    if isinstance(content, list):  # some servers return content parts
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return content


_OPENER = None


def _opener():
    """urllib opener that never follows redirects: urllib would replay the auth headers to wherever a 3xx
    points, and the key only goes to base_url. Built on first use (see the import note above)."""
    global _OPENER
    if _OPENER is None:
        import urllib.request

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None

        _OPENER = urllib.request.build_opener(_NoRedirect)
    return _OPENER


def _run_api(ai, prompt, model, timeout):
    import urllib.error
    import urllib.request
    pc = provider_config(ai)
    url, headers, body = api_request(ai, model=model, prompt=prompt)
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with _opener().open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        hint = " authentication" if exc.code in (401, 403) else ""
        return subprocess.CompletedProcess(url, 1, "", f"HTTP {exc.code}{hint} {pc['name']}: {detail}")
    except (socket.timeout, TimeoutError):
        raise subprocess.TimeoutExpired(url, timeout)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise subprocess.TimeoutExpired(url, timeout)
        return subprocess.CompletedProcess(url, 1, "", f"connection error {pc['name']}: {exc.reason}")
    except ValueError as exc:
        return subprocess.CompletedProcess(url, 1, "", f"invalid JSON from {pc['name']}: {exc}")
    return subprocess.CompletedProcess(url, 0, parse_reply(pc["api"], data), "")


def available(ai=None):
    """{provider: ready?} for the built-ins: a CLI is ready when it is on the PATH, an
    API when its key variable is set (ollama: always). For /eden:setup status."""
    out = {}
    for name, pc in BUILTIN.items():
        if is_api(pc):
            env = pc.get("api_key_env")
            out[name] = (not env) or bool(os.environ.get(env))
        else:
            out[name] = find_cli(pc["cmd"][0]) is not None
    return out


def run(prompt, *, model=None, add_dirs=(), cwd=None, timeout=None, cfg=None):
    """One prompt → one subprocess.CompletedProcess (stdout = the answer). Raises
    AIError for config / missing CLI / missing key; timeouts surface as
    subprocess.TimeoutExpired, for CLIs and APIs alike."""
    ai = ai_config(cfg)
    timeout = timeout or ai["timeout_seconds"]
    if is_api(provider_config(ai)):
        return _run_api(ai, prompt, model, timeout)
    args = resolve(ai, model=model, add_dirs=add_dirs)
    return subprocess.run(args, input=prompt, text=True, encoding="utf-8", capture_output=True,
                          cwd=cwd, timeout=timeout, creationflags=NO_WINDOW)


def describe(ai=None):
    """One line about the configured provider, for status reports. Never prints a key."""
    ai = ai or ai_config()
    try:
        pc = provider_config(ai)
    except AIError as exc:
        return f"{ai.get('provider')} — PROBLEMA: {exc}"
    model = model_for(ai, pc) or "(sin modelo)"
    if is_api(pc):
        env = pc.get("api_key_env")
        key = "sin clave (local)" if not env else (f"{env}: definida" if os.environ.get(env) else f"{env}: FALTA")
        return f"{pc['name']} (API {pc['api']}, {pc['base_url']}) · modelo {model} · {key}"
    exe = find_cli(pc["cmd"][0])
    return f"{pc['name']} (CLI {'disponible' if exe else 'NO está en el PATH'}) · modelo {model}"


# ---------------------------------------------------------------- model tiers
# Eden splits work by tier, not by model name (rules/eden-model-strategy-rules.md):
#   strong — the main session: understands, decides, plans, verifies, talks to the dev.
#   fast   — the agents: scan, measure, extract, write code, audit, within a closed brief.
# Agents declare Claude's names in their frontmatter (`model: sonnet`), which is the kit's source;
# AGENT_TIER reads those as tiers and agent_model() says what each host's agent file should carry.
# None = leave the field out, so the agent inherits the session's model (hosts without a field, or
# whose ids are per-account). Override in eden-config.json → ai.tiers.<host>.<tier>.

AGENT_TIER = {"fable": "plan", "plan": "plan", "opus": "strong", "sonnet": "fast", "haiku": "fast", "fast": "fast", "strong": "strong",
              "inherit": "inherit", "": "inherit"}
TIERS = {name: dict(h["tiers"]) for name, h in eden_hosts.HOSTS.items()}  # see hooks/eden_hosts.py
SESSION_MODEL_HINT = {name: h["session_hint"] for name, h in eden_hosts.HOSTS.items()}


def tier_of(agent_model):
    """Tier of an agent's frontmatter `model:` value (Claude names or tier names)."""
    return AGENT_TIER.get(str(agent_model or "").strip().lower(), "fast")


def agent_model(host, agent_model_value, ai=None):
    """What `model:` an agent file should carry on `host`, or None to omit it (inherit)."""
    tier = tier_of(agent_model_value)
    if tier == "inherit":
        return "inherit" if host in ("claude", "qwen", "cursor") else None
    user = ((ai or _read_ai_section()).get("tiers") or {}).get(host) or {}
    if tier in user:
        return user[tier] or None
    return TIERS.get(host, {}).get(tier)


# ---------------------------------------------------------------- auto-detection
# Read-only: looks at the PATH, the environment, ~/.claude/settings.json "env" and a local ollama.
# With probe=True it also asks each keyed API for its model list (a GET to the vendor's own
# endpoint with the dev's own key — the same place a real call would go). Never returns a key.

EXTRA_KEY_ENVS = {  # other names vendors' docs and SDKs use for the same key
    "moonshot": ["KIMI_API_KEY"], "zai": ["ZHIPUAI_API_KEY", "GLM_API_KEY"], "google": ["GOOGLE_API_KEY"],
    "dashscope": ["QWEN_API_KEY"], "xai": ["GROK_API_KEY"],
}
# Claude Code pointed at a vendor's Anthropic-compatible endpoint (ANTHROPIC_BASE_URL) → that preset.
SESSION_HOSTS = {"anthropic.com": "anthropic", "moonshot.ai": "moonshot", "moonshot.cn": "moonshot",
                 "z.ai": "zai", "bigmodel.cn": "zai", "minimax.io": "minimax", "minimaxi.com": "minimax",
                 "deepseek.com": "deepseek", "aliyuncs.com": "dashscope"}
SESSION_MODEL_VARS = ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_SMALL_FAST_MODEL",
                      "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_MODEL")
FAST_HINTS = ("flash", "haiku", "mini", "lite", "turbo", "fast", "small", "air", "nano")
NOT_CHAT = ("embed", "vision", "tts", "audio", "image", "whisper", "moderation", "realtime", "rerank",
            "dall-e", "search", "transcribe", "ocr")
CLI_RANK = {"claude": 100, "codex": 70, "qwen": 65, "gemini": 60}


def _env_sources():
    """os.environ over ~/.claude/settings.json "env" (Claude Code passes that block to its hooks)."""
    merged = {}
    try:
        env = json.loads((CLAUDE_DIR / "settings.json").read_text(encoding="utf-8")).get("env") or {}
        merged.update({k: str(v) for k, v in env.items() if isinstance(k, str)})
    except (OSError, ValueError, AttributeError):
        pass
    merged.update(os.environ)
    return merged


def pick_fast_model(names):
    """The cheapest-looking chat model of a list (names only), or '' if nothing qualifies."""
    chat = [n for n in names if n and not any(x in n.lower() for x in NOT_CHAT)]
    fast = [n for n in chat if any(h in n.lower() for h in FAST_HINTS)]
    return sorted(fast or [], key=lambda n: (len(n), n))[0] if fast else ""


def _get_json(url, headers, timeout):
    import urllib.request
    req = urllib.request.Request(url, headers=headers, method="GET")
    with _opener().open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def list_models(pc, key, timeout=6):
    """Model ids an API offers (GET /models, or /v1/models in Anthropic format); [] on any failure."""
    base = pc["base_url"].rstrip("/")
    try:
        check_url(base)
        headers = {"user-agent": "eden-kit"}
        if pc["api"] == "anthropic":
            url = base + "/v1/models"
            headers["anthropic-version"] = ANTHROPIC_VERSION
            if key:
                headers["x-api-key"] = key
                if pc.get("auth", "x-api-key") in ("bearer", "both"):
                    headers["authorization"] = f"Bearer {key}"
        else:
            url = base + "/models"
            if key:
                headers["authorization"] = f"Bearer {key}"
        data = _get_json(url, headers, timeout)
    except (AIError, OSError, ValueError):  # urllib.error.URLError is an OSError
        return []
    items = data.get("data") or data.get("models") or []
    return [str(m.get("id") or m.get("name") or "") for m in items if isinstance(m, dict)]


def _ollama_models(timeout=1.5):
    try:
        data = _get_json("http://localhost:11434/api/tags", {"user-agent": "eden-kit"}, timeout)
        return [m.get("name", "") for m in data.get("models") or [] if m.get("name")]
    except (OSError, ValueError):  # urllib.error.URLError is an OSError
        return []


def _codex_logged_in(exe):
    """`codex login status` says "Logged in …" (exit 0) without printing any credential."""
    try:
        r = subprocess.run([exe, "login", "status"], capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW)
        return r.returncode == 0 and "logged in" in (r.stdout + r.stderr).lower()
    except (OSError, subprocess.TimeoutExpired):
        return None


def detect(probe=True, claude_logged_in=None):
    """Every provider Eden could use on this machine, best first. Each candidate:
    {provider, kind, score, ready, model, why, needs, ai}: `ai` is the exact `ai` section that
    would select it (provider + model + any providers[p] override). Never includes a key value."""
    env, out = _env_sources(), []

    for name in CLI:
        exe = find_cli(CLI[name]["cmd"][0])
        if not exe:
            continue
        if name == "claude":
            logged = claude_logged_in() if claude_logged_in else None
        elif name == "codex" and probe:
            logged = _codex_logged_in(exe)
        else:
            logged = None
        why = "CLI instalado" + {True: ", con sesión", False: ", SIN sesión", None: " (sesión no verificada)"}[logged]
        login = {"claude": "`claude auth login`", "codex": "`codex login`"}.get(name, f"`{name}`")
        out.append({"provider": name, "kind": "cli", "score": CLI_RANK.get(name, 50) - (80 if logged is False else 0),
                    "ready": logged is not False, "model": model_for({"providers": {}}, provider_config({"providers": {}}, name)),
                    "why": why, "needs": [f"iniciar sesión: {login}"] if logged is False else [],
                    "ai": {"provider": name}})

    base = env.get("ANTHROPIC_BASE_URL", "")
    host = (urlparse(base).hostname or "") if base else ""
    preset = next((p for suffix, p in SESSION_HOSTS.items() if host == suffix or host.endswith("." + suffix)), None)
    if base and preset != "anthropic":
        key_var = next((v for v in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY") if env.get(v)), "")
        model = next((env[v] for v in SESSION_MODEL_VARS if env.get(v)), "")
        name = preset or "session"
        override = {"base_url": base.rstrip("/"), "api_key_env": key_var}
        if not preset:
            override.update(api="anthropic", auth="both")
        needs = ([] if key_var else ["la clave de la sesión (ANTHROPIC_AUTH_TOKEN)"]) + ([] if model else ["un modelo"])
        out.append({"provider": name, "kind": "session", "score": 90 if not needs else 35, "ready": not needs,
                    "model": model, "why": f"Claude Code apunta a {host} (ANTHROPIC_BASE_URL)", "needs": needs,
                    "ai": {"provider": name, "model": model, "providers": {name: override}}})

    seen = {c["provider"] for c in out}
    for name, pc in API.items():
        if name in seen or name == "ollama":
            continue
        var = next((v for v in [pc.get("api_key_env")] + EXTRA_KEY_ENVS.get(name, []) if v and env.get(v)), "")
        if not var:
            continue
        model = pc.get("model") or ""
        if probe and not model:
            model = pick_fast_model(list_models(pc, env[var]))
        ai_sec = {"provider": name, "model": model if not pc.get("model") else ""}
        if var != pc.get("api_key_env"):
            ai_sec["providers"] = {name: {"api_key_env": var}}
        out.append({"provider": name, "kind": "api", "score": 50 if model else 30, "ready": bool(model),
                    "model": model, "why": f"clave en {var}", "needs": [] if model else ["un modelo (ai.model)"],
                    "ai": ai_sec})

    local = _ollama_models() if probe else []
    if local:
        model = pick_fast_model(local) or local[0]
        out.append({"provider": "ollama", "kind": "local", "score": 40, "ready": True, "model": model,
                    "why": f"ollama corriendo en localhost ({len(local)} modelos)", "needs": [],
                    "ai": {"provider": "ollama", "model": model}})

    return sorted(out, key=lambda c: -c["score"])


def recommend(candidates):
    return next((c for c in candidates if c["ready"]), None)


def elapsed(started):
    return round(time.time() - started, 1)
