import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "scripts" / "eden_ai.py"
spec = importlib.util.spec_from_file_location("eden_ai", SRC)
ai = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai)
ai.CLAUDE_DIR = Path(tempfile.mkdtemp())  # never read the dev's real eden-config.json

fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def raises(kind, fn):
    try:
        fn()
    except ai.AIError as exc:
        return exc.kind == kind
    return False


def echo_cmd(marker):
    return [sys.executable, "-c",
            "import sys; sys.stdout.write('ok:' + sys.stdin.read())" + ("  # " + marker)]


# --- config and model resolution
base = ai.ai_config({"model": "sonnet"})
check("default provider", base["provider"] == "claude")
check("learning.model feeds the claude CLI", ai.model_for(base, ai.provider_config(base)) == "sonnet")
ds = ai.ai_config({"model": "sonnet", "ai": {"provider": "deepseek"}})
check("learning.model never reaches another provider", ai.model_for(ds, ai.provider_config(ds)) == "")
check("ai.model wins", ai.model_for(ai.ai_config({"model": "sonnet", "ai": {"provider": "deepseek", "model": "m"}}),
                                    ai.provider_config(ds)) == "m")
check("alias kimi -> moonshot", ai.ai_config({"ai": {"provider": "kimi"}})["provider"] == "moonshot")
check("alias glm/grok/chatgpt", [ai.ai_config({"ai": {"provider": p}})["provider"] for p in ("glm", "grok", "chatgpt")]
      == ["zai", "xai", "openai"])
check("presets cover the asked vendors", {"openai", "google", "moonshot", "zai", "minimax", "deepseek",
                                          "dashscope", "xai", "qwen", "claude"} <= set(ai.KNOWN))

# claude args (skipped if claude is not installed)
try:
    args = ai.resolve(base, model="haiku", add_dirs=["/tmp/global", "/tmp/proj"])
except ai.AIError:
    args = None
    print("SKIP claude CLI not installed on this machine")
if args is not None:
    check("claude model substituted", args[args.index("--model") + 1] == "haiku")
    check("claude read-only guards", "--safe-mode" in args and "--allowedTools" in args)
    check("claude add-dir repeated per dir",
          [args[i + 1] for i, a in enumerate(args) if a == "--add-dir"] == ["/tmp/global", "/tmp/proj"])

# custom CLI round trip
custom = {"ai": {"provider": "mi-cli", "providers": {"mi-cli": {"cmd": echo_cmd("custom")}}, "timeout_seconds": 60}}
res = ai.run("hola", cfg=custom)
check("custom CLI pipes prompt to stdin", res.returncode == 0 and res.stdout == "ok:hola")
tmpl = {"ai": {"provider": "x", "providers": {"x": {"cmd": echo_cmd("m") + ["--model", "{model}"]}}}}
check("model placeholder in custom cmd", ai.resolve(ai.ai_config(tmpl), model="m1")[-1] == "m1")

# errors
check("unknown provider raises config", raises("config", lambda: ai.resolve(ai.ai_config({"ai": {"provider": "no-existe"}}))))
check("missing CLI raises missing_cli", raises("missing_cli", lambda: ai.resolve(ai.ai_config(
    {"ai": {"provider": "y", "providers": {"y": {"cmd": ["eden-no-such-cli-xyz"]}}}}))))
check("bad api kind raises config", raises("config", lambda: ai.provider_config(ai.ai_config(
    {"ai": {"provider": "z", "providers": {"z": {"api": "soap", "base_url": "https://x"}}}}))))

# can_read: CLIs read files, APIs and tools:false CLIs do not
check("claude can read", ai.can_read(base))
check("API cannot read", not ai.can_read(ds))
check("tools:false CLI cannot read", not ai.can_read(ai.ai_config(
    {"ai": {"provider": "t", "providers": {"t": {"cmd": ["x"], "tools": False}}}})))

# --- API request shape (no network)
os.environ.pop("DEEPSEEK_API_KEY", None)
dsm = ai.ai_config({"ai": {"provider": "deepseek", "model": "m"}})
check("missing key raises missing_key", raises("missing_key", lambda: ai.api_request(dsm, prompt="p")))
check("API without model raises config", raises("config", lambda: ai.api_request(ds, prompt="p")))
os.environ["DEEPSEEK_API_KEY"] = "sk-test-123"
url, headers, body = ai.api_request(dsm, prompt="p")
check("anthropic-format url", url == "https://api.deepseek.com/anthropic/v1/messages")
check("anthropic-format auth both", headers.get("x-api-key") == "sk-test-123"
      and headers.get("authorization") == "Bearer sk-test-123" and "anthropic-version" in headers)
check("anthropic-format body", body["model"] == "m" and body["max_tokens"] > 0
      and body["messages"] == [{"role": "user", "content": "p"}])
check("describe never prints the key", "sk-test-123" not in ai.describe(dsm) and "definida" in ai.describe(dsm))
os.environ["OPENAI_API_KEY"] = "sk-o"
url, headers, body = ai.api_request(ai.ai_config({"ai": {"provider": "chatgpt", "model": "g"}}), prompt="p")
check("openai-format url + bearer", url == "https://api.openai.com/v1/chat/completions"
      and headers["authorization"] == "Bearer sk-o" and "x-api-key" not in headers and "max_tokens" not in body)
os.environ["ANTHROPIC_API_KEY"] = "sk-a"
url, headers, body = ai.api_request(ai.ai_config({"ai": {"provider": "anthropic"}}), prompt="p")
check("anthropic official: x-api-key only, default model", "authorization" not in headers and body["model"])
check("http to a remote host refused", raises("config", lambda: ai.check_url("http://evil.example.com/v1")))
check("https and http-localhost allowed", ai.check_url("https://x.example.com") is None
      and ai.check_url("http://localhost:11434/v1") is None)
check("ollama needs no key", ai.api_request(ai.ai_config({"ai": {"provider": "ollama", "model": "q"}}),
                                            prompt="p")[0] == "http://localhost:11434/v1/chat/completions")

# --- reply parsing
check("anthropic reply drops thinking", ai.parse_reply("anthropic", {"content": [
    {"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "A"}, {"type": "text", "text": "B"}]}) == "AB")
check("openai reply", ai.parse_reply("openai", {"choices": [{"message": {"content": "hi"}}]}) == "hi")
check("openai content parts", ai.parse_reply("openai", {"choices": [{"message": {"content": [{"text": "x"}]}}]}) == "x")


# --- live round trip against a local fake server, both formats + auth failure
class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        if self.path.startswith("/redirect"):
            self.send_response(302)
            self.send_header("location", "https://elsewhere.example.com/steal")
            self.end_headers()
            return
        if self.headers.get("authorization") == "Bearer bad":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error":"invalid key"}')
            return
        text = "echo:" + body["messages"][0]["content"]
        reply = ({"content": [{"type": "text", "text": text}]} if self.path.endswith("/v1/messages")
                 else {"choices": [{"message": {"content": text}}]})
        out = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base_url = f"http://127.0.0.1:{srv.server_port}"
os.environ["EDEN_FAKE_KEY"] = "good"
for kind, path in (("anthropic", ""), ("openai", "/v1")):
    cfg = {"ai": {"provider": "fake", "providers": {"fake": {"api": kind, "base_url": base_url + path,
                                                             "api_key_env": "EDEN_FAKE_KEY", "model": "m"}}}}
    res = ai.run("hola", cfg=cfg)
    check(f"{kind} API round trip", res.returncode == 0 and res.stdout == "echo:hola")
os.environ["EDEN_FAKE_KEY"] = "bad"
cfg["ai"]["providers"]["fake"]["auth"] = "bearer"
res = ai.run("hola", cfg=cfg)
check("401 reported as authentication", res.returncode == 1 and "authentication" in res.stderr
      and "bad" not in res.stderr.replace("invalid key", ""))
cfg["ai"]["providers"]["fake"]["base_url"] = base_url + "/redirect"
res = ai.run("hola", cfg=cfg)
check("redirects are not followed (key stays with base_url)", res.returncode == 1 and "HTTP 302" in res.stderr)
models_pc = {"api": "openai", "base_url": base_url + "/v1"}
Fake.do_GET = lambda self: (self.send_response(200), self.end_headers(), self.wfile.write(
    json.dumps({"data": [{"id": "big-model"}, {"id": "fast-flash"}]}).encode()))
check("list_models reads /models", ai.list_models(models_pc, "good") == ["big-model", "fast-flash"])
srv.shutdown()
check("list_models fails soft", ai.list_models(models_pc, "good", timeout=2) == [])
cfg["ai"]["providers"]["fake"]["base_url"] = "http://127.0.0.1:9"
res = ai.run("hola", cfg=cfg, timeout=5)
check("connection error is a failed result, not a crash", res.returncode == 1 and "connection error" in res.stderr)

# --- auto-detection (controlled machine: no CLIs, no ollama, known env, canned model lists)
check("fast model picked, non-chat skipped", ai.pick_fast_model(
    ["deepseek-reasoner", "embed-flash", "deepseek-chat-flash"]) == "deepseek-chat-flash")
check("no fast model -> empty", ai.pick_fast_model(["big", "bigger"]) == "")
real_which, real_ollama, real_list = ai.shutil.which, ai._ollama_models, ai.list_models
real_globs, ai.APP_CLI_GLOBS = ai.APP_CLI_GLOBS, {}  # the dev machine's app-bundled CLIs must not leak in
for v in [p.get("api_key_env") for p in ai.API.values()] + [v for vs in ai.EXTRA_KEY_ENVS.values() for v in vs] + [
        "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"] + list(ai.SESSION_MODEL_VARS):
    if v:
        os.environ.pop(v, None)
ai.shutil.which = lambda name: "/usr/bin/codex" if name == "codex" else None
ai._ollama_models = lambda timeout=1.5: ["llama3:70b", "qwen2.5-coder:7b-mini"]
ai.list_models = lambda pc, key, timeout=6: ["deepseek-reasoner", "deepseek-flash"] if "deepseek" in pc["base_url"] else []
os.environ.update({"DEEPSEEK_API_KEY": "sk-detect-secret", "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
                   "ANTHROPIC_AUTH_TOKEN": "tok-secret", "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-air"})
(ai.CLAUDE_DIR / "settings.json").write_text(json.dumps({"env": {"KIMI_API_KEY": "kimi-secret"}}), encoding="utf-8")
cands = ai.detect(probe=True)
by = {c["provider"]: c for c in cands}
check("session endpoint detected as its preset, with model", by.get("zai", {}).get("ready")
      and by["zai"]["model"] == "glm-air" and by["zai"]["ai"]["providers"]["zai"]["base_url"].startswith("https://open.bigmodel.cn")
      and by["zai"]["ai"]["providers"]["zai"]["api_key_env"] == "ANTHROPIC_AUTH_TOKEN")
check("session ranks first", ai.recommend(cands)["provider"] == "zai")
check("CLI detected", by.get("codex", {}).get("kind") == "cli")
check("API key detected, fast model probed", by.get("deepseek", {}).get("model") == "deepseek-flash")
check("alt key name from settings.json env", by.get("moonshot", {}).get("ai", {}).get("providers", {})
      .get("moonshot", {}).get("api_key_env") == "KIMI_API_KEY" and not by["moonshot"]["ready"])
check("ollama detected with its fast model", by.get("ollama", {}).get("model") == "qwen2.5-coder:7b-mini")
check("no key value ever in the result", not any(s in json.dumps(cands) for s in ("sk-detect-secret", "tok-secret", "kimi-secret")))
check("detected config validates", ai.provider_config(ai.ai_config({"ai": by["zai"]["ai"]})).get("base_url")
      == "https://open.bigmodel.cn/api/anthropic")
check("probe=False makes no network call", "ollama" not in {c["provider"] for c in ai.detect(probe=False)})
os.environ["ANTHROPIC_BASE_URL"] = "https://llm.internal.example.com"
check("unknown session host becomes a custom anthropic provider",
      ai.detect(probe=False)[0]["ai"]["providers"]["session"]["api"] == "anthropic")
for v in ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_DEFAULT_HAIKU_MODEL"):
    os.environ.pop(v)
(ai.CLAUDE_DIR / "settings.json").unlink()
ai.shutil.which, ai._ollama_models, ai.list_models = real_which, real_ollama, real_list
ai.APP_CLI_GLOBS = real_globs

# --- eden_setup: ai set / ai auto write only with --apply, keep the rest of the config, back it up
sspec = importlib.util.spec_from_file_location("eden_setup", SRC.parent / "eden_setup.py")
st = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(st)
st.CLAUDE = ai.CLAUDE_DIR
st.eden_ai = ai
st.say = lambda msg: None
(ai.CLAUDE_DIR / "eden-config.json").write_text(json.dumps({"company": "acme", "ai": {"provider": "claude", "_c": "x"}}),
                                                encoding="utf-8")
st.APPLY = False
st.write_ai({"provider": "deepseek", "model": "m"}, "t")
check("dry run writes nothing", json.loads((ai.CLAUDE_DIR / "eden-config.json").read_text())["ai"]["provider"] == "claude")
st.APPLY = True
st.write_ai({"provider": "zai", "model": "glm-air", "providers": {"zai": {"api_key_env": "ANTHROPIC_AUTH_TOKEN", "api": None}}}, "t")
saved = json.loads((ai.CLAUDE_DIR / "eden-config.json").read_text())
check("apply writes ai, keeps other keys and comments", saved["company"] == "acme" and saved["ai"]["_c"] == "x"
      and saved["ai"]["provider"] == "zai" and saved["ai"]["providers"]["zai"] == {"api_key_env": "ANTHROPIC_AUTH_TOKEN"})
check("apply backs up the old config", any((ai.CLAUDE_DIR / "backups").rglob("eden-config.json")))
st.write_ai({"provider": "no-such"}, "t")
check("invalid provider is not written", json.loads((ai.CLAUDE_DIR / "eden-config.json").read_text())["ai"]["provider"] == "zai")

# --- model tiers: agents' Claude names → each host's agent model field (None = inherit/omit)
check("sonnet is the fast tier, opus strong", ai.tier_of("sonnet") == "fast" and ai.tier_of("opus") == "strong"
      and ai.tier_of("") == "inherit" and ai.tier_of("weird") == "fast")
check("claude keeps its names", ai.agent_model("claude", "sonnet", {}) == "sonnet" and ai.agent_model("claude", "opus", {}) == "opus")
check("qwen fast / inherit", ai.agent_model("qwen", "sonnet", {}) == "fast" and ai.agent_model("qwen", "opus", {}) == "inherit")
check("cursor inherits", ai.agent_model("cursor", "sonnet", {}) == "inherit")
check("hosts with per-account ids omit the field", all(ai.agent_model(h, "sonnet", {}) is None
                                                       for h in ("codex", "gemini", "opencode", "kimi", "grok")))
check("ai.tiers overrides per host", ai.agent_model("opencode", "sonnet", {"tiers": {"opencode": {"fast": "deepseek/x"}}})
      == "deepseek/x" and ai.agent_model("claude", "sonnet", {"tiers": {"claude": {"fast": "haiku"}}}) == "haiku")
check("unknown host omits", ai.agent_model("somecli", "sonnet", {}) is None)
check("every agent declares a known tier", all(ai.tier_of(ln.split(":", 1)[1]) in ("fast", "strong")
      for f in (SRC.parent.parent / "agents").glob("*.md")
      for ln in f.read_text(encoding="utf-8").splitlines() if ln.startswith("model:")))

# --- CLIs bundled by desktop apps, and a CLI with no model chosen
appdir = Path(tempfile.mkdtemp())
(appdir / "OpenAI/Codex/bin/abc123").mkdir(parents=True)
(appdir / "OpenAI/Codex/bin/abc123/codex.exe").write_text("x")
real_which = ai.shutil.which
ai.shutil.which = lambda name: None
os.environ["LOCALAPPDATA"], old_lad = str(appdir), os.environ.get("LOCALAPPDATA", "")
check("codex found inside the desktop app", ai.find_cli("codex").replace("\\", "/").endswith("OpenAI/Codex/bin/abc123/codex.exe"))
check("unknown CLI still None", ai.find_cli("nope-cli") is None)
args = ai.resolve(ai.ai_config({"ai": {"provider": "codex", "model": ""}}))  # the config written above sets a model
check("no model → no empty -m flag", "-m" not in args and args[-1] == "-" and "read-only" in args)
check("model given → -m kept", ai.resolve(ai.ai_config({"ai": {"provider": "codex", "model": "g"}}))[-3:] == ["-m", "g", "-"])
ai.shutil.which = real_which
os.environ["LOCALAPPDATA"] = old_lad

# available(): booleans for every built-in
avail = ai.available()
check("available covers builtins", set(avail) == set(ai.BUILTIN) and all(isinstance(v, bool) for v in avail.values()))
check("ollama always ready", avail["ollama"])

print("OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
