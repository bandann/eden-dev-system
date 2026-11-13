"""Tests for the Eden guard (hooks/eden_guard.py): AI signature blocking on commit and push, plus the
secret check it already had, against throwaway git repos."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "eden_guard.py"
TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
sys.stdout.reconfigure(encoding="utf-8")  # `python -I` ignores PYTHONIOENCODING
fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def sh(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, creationflags=NO_WINDOW)


def guard(command, cwd):
    """Decision of the hook for this command: the deny reason, or '' when it lets the call through."""
    payload = json.dumps({"tool_input": {"command": command}, "cwd": str(cwd)})
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("EDEN_GUARD_OFF", None)
    res = subprocess.run([sys.executable, "-I", str(GUARD)], input=payload, capture_output=True, text=True,
                         encoding="utf-8", env=env, creationflags=NO_WINDOW)
    out = res.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out else ""


tmp = Path(tempfile.mkdtemp())
remote, repo = tmp / "remote.git", tmp / "repo"
sh(tmp, "init", "-q", "--bare", str(remote))
sh(tmp, "init", "-q", str(repo))
sh(repo, "config", "user.name", "Dev")
sh(repo, "config", "user.email", "dev@example.com")
sh(repo, "remote", "add", "origin", str(remote))
(repo / "a.txt").write_text("one\n", encoding="utf-8")
sh(repo, "add", "a.txt")
sh(repo, "commit", "-q", "-m", "chore: first")
sh(repo, "push", "-q", "origin", "HEAD")
(repo / "a.txt").write_text("two\n", encoding="utf-8")
sh(repo, "add", "a.txt")

# --- commit messages ------------------------------------------------------------------------------------
heredoc = f"git commit -m \"$(cat <<'EOF'\nfeat(x): add thing\n\n{TRAILER}\nEOF\n)\""
r = guard(heredoc, repo)
check("heredoc trailer → blocked", "firma de la IA" in r and "noreply@anthropic.com" in r)
check("block reason says how to fix", "--amend" in r and "co-autor humano" in r)
check("second -m trailer → blocked", guard(f'git commit -m "feat: x" -m "{TRAILER}"', repo) != "")
check("lower-case trailer → blocked",
      guard('git commit -m "feat: x\n\nco-authored-by: claude <noreply@anthropic.com>"', repo) != "")
check("PR-style line in a commit → blocked",
      guard('git commit -m "feat: x\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"', repo) != "")
check("PowerShell here-string → blocked", guard(f"git commit -m @'\nfeat: x\n\n{TRAILER}\n'@", repo) != "")
check("clean message → allowed", guard('git commit -m "feat(x): add thing"', repo) == "")
check("human co-author → allowed",
      guard('git commit -m "feat: x\n\nCo-Authored-By: Ana Pérez <ana@example.com>"', repo) == "")
check("message that only names the rule → allowed",
      guard('git commit -m "feat(guard): block the AI co-author trailer"', repo) == "")
check("message that quotes the PR phrase while describing it → allowed",
      guard("git commit -F - <<'EOF'\nfeat(guard): x\n\nBlocks the \"Generated with Claude Code\" line.\nEOF", repo) == "")
check("bare PR line on its own line → blocked",
      guard("git commit -F - <<'EOF'\nfeat: x\n\nGenerated with Claude Code\nEOF", repo) != "")
check("bare PR line as its own -m → blocked", guard('git commit -m "feat: x" -m "Generated with Claude Code"', repo) != "")
msg = tmp / "msg.txt"
msg.write_text(f"feat: x\n\n{TRAILER}\n", encoding="utf-8")
check("-F file with trailer → blocked", guard(f'git commit -F "{msg.as_posix()}"', repo) != "")
msg.write_text("feat: x\n", encoding="utf-8")
check("-F clean file → allowed", guard(f"git commit --file={msg.as_posix()}", repo) == "")
check("trailer in a file written by the same command → blocked",
      guard(f"cat > m.txt <<'EOF'\nfeat: x\n\n{TRAILER}\nEOF\ngit commit -F m.txt", repo) != "")
check("not a commit (only mentions one) → allowed", guard(f"echo 'git commit -m \"{TRAILER}\"'", repo) == "")

# --- secrets still blocked, and both reported together ----------------------------------------------------
key = "ghp_" + "A1b2C3d4" * 5
(repo / "conf.js").write_text(f'const t = "{key}";\n', encoding="utf-8")
sh(repo, "add", "conf.js")
both = guard(f'git commit -m "feat: x" -m "{TRAILER}"', repo)
check("secret + trailer → one block naming both", "secretos y la firma de la IA" in both and "GitHub token" in both)
check("secret alone still blocked", "GitHub token" in guard('git commit -m "feat: x"', repo))
sh(repo, "rm", "-q", "--cached", "conf.js")
(repo / "conf.js").unlink()

# --- push: outgoing commits ----------------------------------------------------------------------------
sh(repo, "commit", "-q", "-m", f"feat: signed\n\n{TRAILER}")
r = guard("git push origin HEAD", repo)
check("push with a signed outgoing commit → blocked", "firma de la IA" in r and "feat: signed" in r)
sh(repo, "commit", "-q", "--amend", "-m", "feat: signed")
check("push after amending the trailer away → allowed", guard("git push origin HEAD", repo) == "")
sh(repo, "push", "-q", "origin", "HEAD")
check("already pushed history is not re-checked", guard("git push origin HEAD", repo) == "")

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
