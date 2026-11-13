"""Merge the Eden hooks into a Claude Code settings.json, idempotently.

Usage: python -I install_hooks.py <settings.json> <hooks_dir> [--remove]
Existing hooks are kept; Eden's own entries (identified by their script names) are replaced, never
duplicated. A timestamped backup is written next to the file before any change.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = ("eden_brain.py", "eden_guard.py", "eden_secret_guard.py")
# (event, script, subcommand, timeout seconds, matcher, name) — names match hooks/hooks.json
HOOKS = [
    ("SessionStart", "eden_brain.py", "start", 15, None, "eden-brain-recall"),
    ("SessionEnd", "eden_brain.py", "learn", 30, None, "eden-brain-learn-on-exit"),
    ("PreCompact", "eden_brain.py", "learn", 30, None, "eden-brain-learn-before-compact"),
    # Before a git commit / push run by Claude; both scripts exit at once for any other command.
    ("PreToolUse", "eden_guard.py", "", 60, "Bash|PowerShell", "eden-commit-guard"),
    ("PreToolUse", "eden_brain.py", "learn", 15, "Bash|PowerShell", "eden-brain-learn-on-commit"),
    ("PreToolUse", "eden_secret_guard.py", "", 10, "Read|NotebookRead|Grep|Bash|PowerShell", "eden-secrets-readonly"),
]


def main():
    settings, hooks_dir = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    if hooks_dir.is_file():  # older installers passed the script path
        hooks_dir = hooks_dir.parent
    remove = "--remove" in sys.argv
    data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    original = json.dumps(data, sort_keys=True)
    hooks = data.setdefault("hooks", {})

    for event in dict.fromkeys(h[0] for h in HOOKS):
        kept = []
        for g in hooks.get(event, []):
            entries = [h for h in g.get("hooks", []) if not any(s in h.get("command", "") for s in SCRIPTS)]
            if entries:
                kept.append({**g, "hooks": entries})
        if not remove:
            for ev, script, sub, timeout, matcher, name in HOOKS:
                if ev != event:
                    continue
                cmd = f'python -I "{(hooks_dir / script).as_posix()}"' + (f" {sub}" if sub else "")
                group = {"hooks": [{"type": "command", "command": cmd, "timeout": timeout, "statusMessage": name}]}
                if matcher:
                    group = {"matcher": matcher, **group}
                kept.append(group)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)

    if json.dumps(data, sort_keys=True) != original:
        if settings.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(settings, settings.with_name(f"{settings.name}.eden-backup-{stamp}"))
        settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("removed" if remove else "installed", ", ".join(h[-1] for h in HOOKS))


if __name__ == "__main__":
    main()
