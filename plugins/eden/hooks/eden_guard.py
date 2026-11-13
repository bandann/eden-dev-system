"""Eden guard — blocks a git commit / push run by Claude when it would carry a secret or an AI signature.

PreToolUse hook (Bash|PowerShell). Reads the hook payload on stdin; for any command that is not a
git commit or push it exits at once. For a commit it scans what is about to enter the commit; for a
push, the commits that are about to leave. On a finding it denies the tool call and says where.

Uses gitleaks when installed (staged scope / outgoing commits) plus its own high-signal patterns, so it
also works without it. Never prints a secret: values are redacted. A line marked `eden-allow-secret`
is skipped (false positives, approved by the dev).

AI signature: a `Co-Authored-By:` trailer naming Claude/Anthropic or a "Generated with Claude Code" line,
in the commit message (inline, heredoc, `-F file`) or in an outgoing commit on push. A human co-author
passes. The dev is the author of every commit (rules/eden-git-rules.md).
"""
import sys

# Fast path, before anything heavy loads or the secret patterns compile: this hook runs on EVERY shell
# call, and a payload that never mentions git cannot be a git commit or push.
_RAW = None
if __name__ == "__main__" and "--git-hook" not in sys.argv:
    _RAW = sys.stdin.read()
    if "git" not in _RAW:
        sys.exit(0)

import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eden_host  # one hook contract for every host (see hooks/eden_host.py)

GIT_ACTION = re.compile(r"(?:^|[;&|(\s])git\s+(?:-C\s+\S+\s+)?(commit|push)\b")
# `git add -A` / `git add .` stage untracked files too; `git commit -a` only tracked ones.
ADD_ALL = re.compile(r"git\s+add\s+(-A|--all|\.(?:\s|$|&|;))")
COMMIT_ALL = re.compile(r"git\s+commit\b[^;&|]*\s-[a-zA-Z]*a")
ALLOW = "eden-allow-secret"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # no console window for git/gitleaks on Windows

PATTERNS = [
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("Shopify token", re.compile(r"\bshp(at|ca|pa|ss)_[a-fA-F0-9]{32}\b")),
    ("Stripe live key", re.compile(r"\b(sk|rk)_live_[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9_\-]{32,}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----")),
    ("Credential in URL", re.compile(r"\b[a-z][a-z0-9+.\-]*://[^/\s:@'\"]+:[^/\s@'\"]{6,}@[^\s'\"]+", re.I)),
    ("Hardcoded secret", re.compile(
        r"""(?i)(?<![A-Za-z0-9])(?:\w*?_)?(pass(word|wd)?|secret|api[_-]?key|access[_-]?key|auth[_-]?token|client[_-]?secret|private[_-]?key)\b"""
        r"""["']?\s*[:=]\s*["']([^"'\s]{12,})["']""")),
]
PLACEHOLDER = re.compile(r"(?i)(x{4,}|\*{4,}|your[_-]|example|changeme|dummy|placeholder|sample|test[_-]?key|"
                         r"<[^>]+>|\$\{|\{\{|%\(|process\.env|getenv|env\(|os\.environ)")
SECRET_FILES = re.compile(r"(^|/)(\.env(\.[^/]*)?|[^/]*\.(pem|key|p12|pfx|keystore|jks)|id_(rsa|dsa|ecdsa|ed25519))$")
# The PR-style line counts only as the signature itself (its markdown link, or alone on its line / in its
# own -m), never when a message merely quotes the phrase while describing it.
# Any AI assistant Eden can run in (or that signs commits on its own), not only Claude.
AI_NAMES = (r"claude|anthropic|codex|openai|chatgpt|gemini|antigravity|qwen|kimi|moonshot|grok|xai|"
            r"deepseek|glm|zhipu|z\.ai|minimax|cursor|copilot|opencode|crush|aider|devin|windsurf|cline")
AI_TOOLS = r"claude code|codex|gemini cli|antigravity|qwen code|kimi code|grok build|opencode|crush|cursor|aider"
AI_SIGNATURE = re.compile(rf"""(?im)(co-authored-by:[^\n'"]*\b(?:{AI_NAMES})\b[^\n'"]*"""
                          rf"""|generated with \[(?:{AI_TOOLS})\]\(https?://[^\s)]*\)"""
                          rf"""|(?:^|(?<=["']))[^\w\n"']*generated (?:with|by) (?:{AI_TOOLS})(?=[^\w\n]*$))""")
COMMIT_FILE = re.compile(r"""git\s+commit\b[^;&|]*?\s(?:-F|--file)(?:=|\s+)("[^"]+"|'[^']+'|[^\s;&|]+)""")
SECRET_FILE_OK = re.compile(r"\.env\.(example|sample|template|dist)$|\.pub$")


CD = re.compile(r"""(?:^|[;&|(]\s*)(?:cd|Set-Location|Push-Location|pushd)\s+(?:-Path\s+)?("[^"]+"|'[^']+'|[^\s;&|)]+)""")
GIT_C = re.compile(r"""git\s+-C\s+("[^"]+"|'[^']+'|\S+)\s+(?:commit|push)\b""")


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", re.S | re.M)
HERESTRING = re.compile(r"@(['\"])\r?\n.*?^\1@", re.S | re.M)  # PowerShell @'…'@ / @"…"@
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")


def without_heredocs(command):
    """Heredoc and here-string bodies are text (a checkpoint, a commit message file), not commands."""
    return HERESTRING.sub("", HEREDOC.sub("", command))


def git_action(command):
    """The git commit/push this command really runs, or None. Text that merely mentions `git commit`
    — inside a heredoc, a here-string or a quoted string — does not count."""
    m = GIT_ACTION.search(QUOTED.sub("''", without_heredocs(command)))
    return m.group(1) if m else None


def effective_cwd(command, cwd):
    """The directory the git command really runs in: the hook's cwd is the session's, but Claude
    usually writes `cd repo && git commit`. Follows the last cd before the git call, or `git -C`."""
    command = without_heredocs(command)
    m = GIT_ACTION.search(command)
    head = command[:m.start()] if m else command
    base = Path(cwd)
    for target in CD.findall(head):
        t = target.strip("\"'")
        if re.match(r"^/[a-zA-Z]/", t):  # Git Bash path /c/Users → C:/Users
            t = f"{t[1]}:{t[2:]}"
        t = os.path.expandvars(os.path.expanduser(t))
        base = (base / t) if not Path(t).is_absolute() else Path(t)
    gc = GIT_C.search(command)
    if gc:
        t = gc.group(1).strip("\"'")
        base = Path(t) if Path(t).is_absolute() else base / t
    return str(base)


def git(cwd, *args):
    try:
        res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20, creationflags=NO_WINDOW)
        return res.stdout if res.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def redact(value):
    value = value.strip()
    return value[:4] + "…" + f"({len(value)} chars)" if len(value) > 8 else "…"


def scan_diff(diff):
    """Findings in the added lines of a unified diff: (file, line_no, kind, redacted)."""
    findings, path, line_no = [], None, 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else raw[4:]
            continue
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
        if m:
            line_no = int(m.group(1)) - 1
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line_no += 1
            text = raw[1:]
            if ALLOW in text:
                continue
            for kind, rx in PATTERNS:
                hit = rx.search(text)
                if not hit:
                    continue
                value = hit.group(hit.lastindex or 0) if kind == "Hardcoded secret" else hit.group(0)
                # Placeholders only excuse generic `password = "..."` matches: a recognisable token or a
                # URL with credentials is a secret even when the host is example.com.
                if kind == "Hardcoded secret" and (PLACEHOLDER.search(value) or PLACEHOLDER.search(text)):
                    continue
                findings.append((path, line_no, kind, redact(value)))
                break
        elif not raw.startswith("-"):
            line_no += 1
    return findings


def untracked_as_diff(cwd):
    """Untracked, non-ignored files rendered as additions, for `git add -A` style commits."""
    out = []
    for name in git(cwd, "ls-files", "--others", "--exclude-standard").splitlines():
        p = Path(cwd) / name
        try:
            if p.stat().st_size > 1_000_000:
                continue
            body = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        out.append(f"+++ b/{name}\n@@ -0,0 +1 @@\n" + "\n".join("+" + ln for ln in body.splitlines()))
    return "\n".join(out)


def secret_files(names):
    return [n for n in names if SECRET_FILES.search(n) and not SECRET_FILE_OK.search(n)]


def gitleaks(cwd, args):
    """Run gitleaks if present; returns findings as (file, line, rule, redacted)."""
    exe = shutil.which("gitleaks")
    if not exe:
        return None
    report = Path(cwd) / ".git" / "eden-gitleaks.json"
    try:
        subprocess.run([exe, *args, "--redact", "--no-banner", "--exit-code", "0",
                        "--report-format", "json", "--report-path", str(report)],
                       cwd=cwd, capture_output=True, timeout=60, creationflags=NO_WINDOW)
        data = json.loads(report.read_text(encoding="utf-8") or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    finally:
        try:
            report.unlink()
        except OSError:
            pass
    return [(d.get("File"), d.get("StartLine"), d.get("RuleID"), "REDACTED") for d in data
            if ALLOW not in (d.get("Line") or "")]


def signatures_in_commit(command, cwd):
    """AI signature lines in the message of the commit this command runs (inline, heredoc or -F file)."""
    hits = [m.group(1).strip() for m in AI_SIGNATURE.finditer(command)]
    fm = COMMIT_FILE.search(command)
    name = fm.group(1).strip("\"'") if fm else "-"
    if name != "-":
        f = Path(os.path.expanduser(name))
        try:
            text = (f if f.is_absolute() else Path(cwd) / f).read_text(encoding="utf-8", errors="ignore")
            hits += [m.group(1).strip() for m in AI_SIGNATURE.finditer(text)]
        except OSError:
            pass  # written by this same command: its heredoc text was already scanned above
    return list(dict.fromkeys(hits))


def signatures_outgoing(cwd):
    """'hash subject' of the commits about to be pushed whose message carries an AI signature."""
    out = []
    for rec in git(cwd, "log", "--format=%h%x1f%s%x1f%B%x1e", "HEAD", "--not", "--remotes").split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) == 3 and AI_SIGNATURE.search(parts[2]):
            out.append(f"{parts[0]} {parts[1]}")
    return out


def deny(action, findings, files, scope_note, signatures=()):
    """Agent mode: block the tool call, in the calling host's format (hooks/eden_host.py)."""
    eden_host.deny(report(action, findings, files, scope_note, signatures))


def report(action, findings, files, scope_note, signatures=()):
    reasons = (["secretos"] if findings or files else []) + (["la firma de la IA"] if signatures else [])
    lines = [f"🛡️ Eden guard bloqueó el `git {action}`: hay {' y '.join(reasons)} en {scope_note}."]
    for f, ln, kind, val in findings[:15]:
        lines.append(f"  - {f}:{ln} — {kind} ({val})")
    for f in files[:10]:
        lines.append(f"  - {f} — archivo de credenciales que no debe entrar en git")
    for sig in signatures[:10]:
        lines.append(f"  - firma: {sig}")
    if signatures:
        lines.append(
            "Firma de la IA: el dev es el autor de todos los commits. Quita la línea `Co-Authored-By: Claude …` "
            "o \"Generated with Claude Code\" del mensaje y vuelve a commitear; si el commit aún no se subió, "
            "corrígelo con `git commit --amend` (nunca force-push a una rama ya compartida). "
            "Un co-autor humano sí está permitido.")
    if findings or files:
        lines.append(
            "Qué hacer: saca el valor a una variable de entorno o al gestor de la plataforma, añade el archivo "
            "a .gitignore y, si el secreto ya estuvo en algún commit o push, RÓTALO (borrarlo no basta). "
            "Si es un falso positivo y el dev lo confirma, marca la línea con `eden-allow-secret`.")
    lines.append("Explícale esto al dev en español antes de reintentar; no lo esquives.")
    return "\n".join(lines)


def review():
    """hooks/eden_review.py, loaded only when a push is checked."""
    import eden_review
    return eden_review


def unique_findings(findings):
    seen, unique = set(), []
    for f in findings:
        if (f[0], f[1]) not in seen:
            seen.add((f[0], f[1]))
            unique.append(f)
    return unique


def git_hook(kind, args):
    """Git-hook mode (`--git-hook pre-commit|commit-msg|pre-push`): the same checks for ANY commit or
    push — whichever AI tool or person runs it, hooks or not. Exit 1 blocks; the reason goes to stderr.
    Installed per repo by `/eden:setup githooks`. EDEN_GUARD_OFF=1 or `git … --no-verify` skip it."""
    if os.environ.get("EDEN_GUARD_OFF"):
        return 0
    cwd = os.getcwd()
    if kind == "pre-commit":
        diff = git(cwd, "diff", "--cached", "--unified=0")
        names = git(cwd, "diff", "--cached", "--name-only").splitlines()
        findings = scan_diff(diff) + (gitleaks(cwd, ["protect", "--staged", "--source", "."]) or [])
        action, scope, signatures = "commit", "lo que va a entrar en el commit", []
    elif kind == "commit-msg":
        try:
            text = Path(args[0]).read_text(encoding="utf-8", errors="ignore")
        except (IndexError, OSError):
            return 0
        text = "\n".join(ln for ln in text.splitlines() if not ln.startswith("#"))  # git's own comments
        signatures = list(dict.fromkeys(m.group(1).strip() for m in AI_SIGNATURE.finditer(text)))
        action, scope, findings, names = "commit", "el mensaje del commit", [], []
    elif kind == "pre-push":
        findings, names, signatures, pushed = [], [], [], []
        for line in sys.stdin.read().splitlines():  # <local ref> <local sha> <remote ref> <remote sha>
            parts = line.split()
            if len(parts) < 2 or set(parts[1]) == {"0"}:
                continue  # a branch deletion pushes no content
            if parts[0].startswith("refs/heads/"):
                pushed.append((parts[0][len("refs/heads/"):], parts[1]))
            rng = [parts[1], "--not", "--remotes"]
            findings += scan_diff(git(cwd, "log", "-p", "--unified=0", "--format=", *rng))
            names += git(cwd, "log", "--name-only", "--format=", *rng).splitlines()
            for rec in git(cwd, "log", "--format=%h%x1f%s%x1f%B%x1e", *rng).split("\x1e"):
                p = rec.strip("\n").split("\x1f")
                if len(p) == 3 and AI_SIGNATURE.search(p[2]):
                    signatures.append(f"{p[0]} {p[1]}")
        action, scope = "push", "los commits que todavía no están en ningún remoto"
    else:
        return 0
    unique = unique_findings(findings)
    files = secret_files(sorted(set(n.strip() for n in names if n.strip())))
    if not (unique or files or signatures):
        if kind == "pre-commit":  # opt-in AI review of the staged diff (hooks/eden_ai_review.py)
            import eden_ai_review
            msg, notes = eden_ai_review.review(cwd)
            for n in notes:
                eden_host._stderr(n)
            if msg:
                eden_host._stderr(msg)
                return 1
        if kind == "pre-push":  # the push must carry exactly what was reviewed (hooks/eden_review.py)
            for branch, sha in pushed:
                msg = review().check_push(cwd, branch, sha)
                if msg:
                    eden_host._stderr(msg)
                    return 1
        return 0
    eden_host._stderr(report(action, unique, files, scope, list(dict.fromkeys(signatures))))
    return 1


def main():
    if "--git-hook" in sys.argv[:-1]:
        i = sys.argv.index("--git-hook")
        sys.exit(git_hook(sys.argv[i + 1], sys.argv[i + 2:]))
    payload = eden_host.read_payload(io.StringIO(_RAW) if _RAW is not None else None)
    command = (payload.get("tool_input") or {}).get("command") or ""
    action = git_action(command)
    if not action or os.environ.get("EDEN_GUARD_OFF"):
        return
    cwd = effective_cwd(command, payload.get("cwd") or os.getcwd())
    if not git(cwd, "rev-parse", "--git-dir"):
        return

    if action == "commit":
        add_all = bool(ADD_ALL.search(command))
        tracked_all = add_all or bool(COMMIT_ALL.search(command))
        ref = ("diff", "HEAD") if tracked_all else ("diff", "--cached")
        diff = git(cwd, *ref, "--unified=0")
        names = git(cwd, *ref, "--name-only").splitlines()
        if add_all:
            diff += "\n" + untracked_as_diff(cwd)
            names += git(cwd, "ls-files", "--others", "--exclude-standard").splitlines()
        findings = scan_diff(diff)
        if not tracked_all:
            findings += gitleaks(cwd, ["protect", "--staged", "--source", "."]) or []
        scope = "lo que va a entrar en el commit" + (" (incluye cambios aún sin añadir)" if tracked_all else "")
        signatures = signatures_in_commit(command, cwd)
    else:
        # Outgoing = reachable from HEAD and on no remote yet. Works for a new branch without upstream.
        rng = ["HEAD", "--not", "--remotes"]
        diff = git(cwd, "log", "-p", "--unified=0", "--format=", *rng)
        names = git(cwd, "log", "--name-only", "--format=", *rng).splitlines()
        findings = scan_diff(diff) + (gitleaks(cwd, ["detect", "--source", ".",
                                                     "--log-opts=HEAD --not --remotes"]) or [])
        scope = "los commits que todavía no están en ningún remoto"
        signatures = signatures_outgoing(cwd)

    seen, unique = set(), []
    for f in findings:
        key = (f[0], f[1])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    files = secret_files(sorted(set(n.strip() for n in names if n.strip())))
    if unique or files or signatures:
        deny(action, unique, files, scope, signatures)
    elif action == "push":  # the push must carry exactly what was reviewed (hooks/eden_review.py)
        msg = review().check_push(cwd, review().current_branch(cwd), "HEAD")
        if msg:
            eden_host.deny(msg)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken guard must never break the session; it just doesn't block
        pass
