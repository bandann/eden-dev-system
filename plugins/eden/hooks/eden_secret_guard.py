"""Eden secret guard (eden-secrets-readonly) — the agent never reads a file that holds secrets.

PreToolUse hook for file reads and shell commands, on every host (hooks/eden_host.py normalizes the
payload). The commit guard (eden_guard.py) keeps secrets out of git; this one keeps them out of the
model's context in the first place: a value that was read can end up in a reply, a note or a log.

Blocked: reading `.env` / `*.env` (not the templates `.env.example|sample|template|dist|defaults`),
private keys and keystores (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.ppk`,
`id_rsa`, `id_ed25519`, `id_ecdsa`, `id_dsa`), anything in `~/.ssh/` except public keys,
`known_hosts` and `config`, `~/.aws/credentials`, `.netrc` / `_netrc`, `.pgpass`, `.git-credentials`
and gcloud's `application_default_credentials.json`.

How: a Read / NotebookRead of such a path, a Grep whose path or glob targets one, or a shell command
segment where a reading verb (cat, type, more, less, head, tail, bat, grep, rg, findstr, Get-Content,
Select-String, cp, copy, base64, xxd…) or an input redirect touches one. Creating, deleting, listing,
sourcing or passing the file to a program (`docker run --env-file .env`) is not reading it.

Allowed on purpose: `security.allow_read` (fnmatch globs on the path or the file name) in
~/.claude/eden-config.json or the project's .claude/project-config.json, written by the dev.
EDEN_GUARD_OFF=1 disables it, like the commit guard. Never prints a secret: it never opens the file.
"""
import sys

# Fast path: nothing in the payload even looks like a secret file → exit before loading anything.
HINTS = (".env", ".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".ppk", "id_rsa", "id_ed25519",
         "id_ecdsa", "id_dsa", ".ssh", ".aws", "netrc", ".pgpass", ".git-credentials", "application_default_credentials")
_RAW = None
if __name__ == "__main__":
    _RAW = sys.stdin.read()
    if not any(h in _RAW.lower() for h in HINTS):
        sys.exit(0)

import fnmatch
import io
import json
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_host  # one hook contract for every host (see hooks/eden_host.py)

TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".defaults", ".tpl", ".schema")
KEY_EXTS = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".ppk")
KEY_NAMES = {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
CRED_FILES = {".netrc", "_netrc", ".pgpass", ".git-credentials", "application_default_credentials.json"}
SSH_OK = {"known_hosts", "known_hosts.old", "config", "authorized_keys"}
READ_VERBS = re.compile(
    r"(?i)(?:^|[\s;&|(])(cat|type|more|less|head|tail|bat|nl|od|xxd|hexdump|strings|base64|grep|egrep|rg|ag|"
    r"findstr|awk|sed|cut|sort|uniq|diff|cmp|cp|copy|scp|rsync|tee|openssl|gc|get-content|select-string|"
    r"copy-item|cpi|import-csv|format-hex|notepad|code|vim?|nano|emacs)(?=\s|$)")
SEGMENT = re.compile(r"\|\||&&|[;|\n]")
TOKEN = re.compile(r"""'[^']*'|"[^"]*"|[^\s;&|<>()]+""")


def sensitive(path):
    """Why `path` holds secrets, or None. Pure string check: the file is never opened."""
    p = str(path or "").strip().strip("'\"").replace("\\", "/")
    if not p:
        return None
    name = p.rsplit("/", 1)[-1].lower()
    low = p.lower()
    if name.endswith(TEMPLATE_SUFFIXES) or name.endswith(".pub"):
        return None
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return "variables de entorno (.env)"
    if name.endswith(KEY_EXTS) or name in KEY_NAMES:
        return "llave privada o almacén de llaves"
    if "/.ssh/" in f"/{low}" and name not in SSH_OK:
        return "archivo de ~/.ssh"
    if low.endswith("/.aws/credentials") or low == ".aws/credentials":
        return "credenciales de AWS"
    if name in CRED_FILES:
        return "archivo de credenciales"
    return None


def allowed(path, cwd):
    """The dev's own exceptions: security.allow_read in the global or the project config."""
    globs = []
    for f in (Path.home() / ".claude" / "eden-config.json", Path(cwd or ".") / ".claude" / "project-config.json"):
        try:
            globs += (json.loads(f.read_text(encoding="utf-8")).get("security") or {}).get("allow_read") or []
        except (OSError, ValueError, AttributeError):
            pass
    p = str(path).replace("\\", "/")
    return any(fnmatch.fnmatch(p, g) or fnmatch.fnmatch(p.rsplit("/", 1)[-1], g) for g in globs)


def shell_targets(command):
    """Sensitive paths a command reads: per segment, a reading verb or an input redirect plus such a path."""
    hits = []
    for seg in SEGMENT.split(command or ""):
        tokens = [t.strip("'\"") for t in TOKEN.findall(seg)]
        redirected = [m.group(1) for m in re.finditer(r"<\s*([^\s;&|<>]+)", seg)]
        if not READ_VERBS.search(seg) and not redirected:
            continue
        for t in tokens + redirected:
            why = sensitive(t)
            if why:
                hits.append((t, why))
    return hits


def targets(payload):
    """[(path, why)] this tool call would read."""
    tool = payload.get("tool_name") or ""
    tin = payload.get("tool_input") or {}
    if tool == "Read":
        paths = tin.get("paths") or [tin.get("file_path")]
        return [(p, sensitive(p)) for p in paths if sensitive(p)]
    if tool == "NotebookRead":
        p = tin.get("notebook_path") or tin.get("file_path")
        return [(p, sensitive(p))] if sensitive(p) else []
    if tool == "Grep":
        out = []
        for key in ("path", "glob"):
            v = tin.get(key)
            if v and sensitive(v):
                out.append((v, sensitive(v)))
        return out
    if tool in ("Bash", "PowerShell"):
        return shell_targets(tin.get("command") or "")
    return []


def main():
    if os.environ.get("EDEN_GUARD_OFF"):
        return
    payload = eden_host.read_payload(io.StringIO(_RAW) if _RAW is not None else None)
    cwd = payload.get("cwd") or os.getcwd()
    hits = [(p, why) for p, why in targets(payload) if not allowed(p, cwd)]
    if not hits:
        return
    lines = ["🔐 Eden: no se leen archivos con secretos — esta lectura se bloqueó:"]
    lines += [f"  - `{p}` — {why}" for p, why in dict(hits).items()]
    lines.append(
        "Lo que se lee entra al contexto y puede terminar en una respuesta, una nota o un log. Si necesitas "
        "saber qué variables hay, usa la plantilla (`.env.example`) o pregúntale al dev el NOMBRE de la "
        "variable, nunca su valor. Si el dev lo autoriza de forma explícita, puede añadir el patrón a "
        "`security.allow_read` en `.claude/project-config.json`. Díselo al dev en español; no lo esquives.")
    eden_host.deny("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # a broken guard must never break the session; it just doesn't block
        pass
