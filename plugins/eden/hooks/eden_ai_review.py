"""Eden AI pre-commit review — an opt-in second pair of eyes on every commit, with any AI provider.

Runs from the git pre-commit hook (eden_guard.py --git-hook pre-commit), after the secret scan passed,
so the diff it sends never carries a secret that the scan can see. Off unless the project turns it on in
.claude/project-config.json:

    "review": {"precommit": {"enabled": true, "block_on": "high", "max_diff_chars": 60000, "timeout_seconds": 120}}

It sends the staged diff and the project's instructions file (CLAUDE.md / AGENTS.md / GEMINI.md / QWEN.md)
to the provider set with `/eden:setup ai` (scripts/eden_ai.py — CLIs run read-only), asks for findings as
JSON, and blocks the commit only for findings at or above `block_on` (critical > high > medium > low).
Everything else is printed and the commit goes on.

Fails open, loudly: no provider, a timeout, an unreadable answer or a diff over `max_diff_chars` never
block a commit — they print why the review did not run. A staged tree that already passed is not sent
again (.git/eden-precommit.json). EDEN_AI_REVIEW_OFF=1 skips it for one commit. It costs tokens on every
commit, which is why it is opt-in.
"""
import json
import os
import re
import sys
from pathlib import Path

SEVERITY = {"low": 1, "medium": 2, "high": 3, "critical": 4}
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "QWEN.md")
DEFAULTS = {"enabled": False, "block_on": "high", "max_diff_chars": 60000, "timeout_seconds": 120}

PROMPT = """You review one git commit before it is made. Report only real problems a careful senior reviewer
would block or flag: bugs, regressions, security issues, data loss, broken project conventions stated in
the instructions below. No style nitpicks, no praise, no summaries. If the diff is fine, return no findings.

Answer with ONE JSON object and nothing else:
{{"findings": [{{"severity": "critical|high|medium|low", "file": "path", "line": 0, "issue": "what is wrong",
"fix": "what to do"}}]}}

Severity: critical = will break production or leak data; high = a real bug or security hole; medium = a
likely problem or a clear convention breach; low = minor.

## Project instructions (excerpt)
{rules}

## Staged diff
{diff}
"""


def config(cwd):
    try:
        data = json.loads((Path(cwd) / ".claude" / "project-config.json").read_text(encoding="utf-8"))
        user = ((data.get("review") or {}).get("precommit")) or {}
    except (OSError, ValueError, AttributeError):
        user = {}
    return {**DEFAULTS, **(user if isinstance(user, dict) else {})}


def instructions(cwd, limit=8000):
    for name in INSTRUCTION_FILES:
        try:
            return (Path(cwd) / name).read_text(encoding="utf-8", errors="replace")[:limit]
        except OSError:
            continue
    return "(none)"


def parse_findings(text):
    """Findings from a model answer: the first JSON object that has a `findings` list. None if unreadable."""
    text = text or ""
    for m in re.finditer(r"\{", text):
        depth = 0
        for i in range(m.start(), len(text)):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            if depth == 0:
                try:
                    obj = json.loads(text[m.start():i + 1])
                except ValueError:
                    break
                if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
                    return [f for f in obj["findings"] if isinstance(f, dict)]
                break
    return None


def _cache(cwd):
    from eden_review import git
    gd = git(cwd, "rev-parse", "--absolute-git-dir")
    return Path(gd) / "eden-precommit.json" if gd else None


def review(cwd, run=None):
    """(blocking message or None, notes for stderr). `run(prompt, timeout)` is injectable for tests."""
    cfg = config(cwd)
    if not cfg.get("enabled") or os.environ.get("EDEN_AI_REVIEW_OFF"):
        return None, []
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from eden_review import git
    diff = git(cwd, "diff", "--cached", "--unified=3")
    if not diff.strip():
        return None, []
    tree = git(cwd, "write-tree")
    cache_file = _cache(cwd)
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file and cache_file.exists() else {}
    except (OSError, ValueError):
        cache = {}
    if tree and cache.get("passed") == tree:
        return None, ["🤖 Revisión de IA: este mismo contenido ya pasó la revisión."]
    if len(diff) > int(cfg["max_diff_chars"]):
        return None, [f"🤖 Revisión de IA: no corrió — el diff ({len(diff)} caracteres) supera max_diff_chars "
                      f"({cfg['max_diff_chars']}). El commit sigue."]
    prompt = PROMPT.format(rules=instructions(cwd), diff=diff)
    try:
        if run is None:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
            import eden_ai
            os.environ["EDEN_DISTILLER"] = "1"  # the provider's own Eden hooks must not fire inside this call
            res = eden_ai.run(prompt, timeout=int(cfg["timeout_seconds"]))
            answer = res.stdout if res.returncode == 0 else ""
            err = "" if res.returncode == 0 else (res.stderr or "")[-300:]
        else:
            answer, err = run(prompt, int(cfg["timeout_seconds"])), ""
    except Exception as exc:  # no provider, missing key, timeout…: never block a commit for it
        return None, [f"🤖 Revisión de IA: no corrió ({exc.__class__.__name__}: {str(exc)[:160]}). El commit sigue; "
                      "revisa el proveedor con `/eden:setup ai test`."]
    findings = parse_findings(answer)
    if findings is None:
        return None, ["🤖 Revisión de IA: la respuesta no se pudo leer" + (f" ({err.strip()})" if err.strip() else "")
                      + ". El commit sigue."]
    floor = SEVERITY.get(str(cfg["block_on"]).lower(), 3)
    blocking = [f for f in findings if SEVERITY.get(str(f.get("severity", "")).lower(), 0) >= floor]

    def fmt(f):
        where = f"{f.get('file', '?')}:{f.get('line', '?')}"
        return f"  - [{f.get('severity', '?')}] {where} — {f.get('issue', '')}" + (f" → {f['fix']}" if f.get("fix") else "")

    notes = [fmt(f) for f in findings if f not in blocking]
    if not blocking:
        if cache_file and tree:
            cache_file.write_text(json.dumps({"passed": tree}), encoding="utf-8")
        return None, (["🤖 Revisión de IA: sin bloqueantes."] + notes) if notes else ["🤖 Revisión de IA: sin hallazgos."]
    msg = [f"🤖 Revisión de IA: el commit se bloqueó por {len(blocking)} hallazgo(s) de severidad ≥ {cfg['block_on']}:"]
    msg += [fmt(f) for f in blocking] + notes
    msg.append("Arréglalo y vuelve a commitear. Si el dev decide que es un falso positivo: EDEN_AI_REVIEW_OFF=1 "
               "para este commit, o sube `review.precommit.block_on` en .claude/project-config.json.")
    return "\n".join(msg), []
