"""Eden review stamp — the push carries exactly what was reviewed.

`turnoff-task` reviews the branch, then records the exact state it reviewed; the commit guard
(eden_guard.py, as a tool hook and as the git pre-push hook) refuses a push whose tree differs from that
state, and says which files changed after the review. Commits in between are free — one per logical
change is the rule — because only the final pushed tree is compared.

  python -I eden_review.py stamp      after the review (and its fixes): record the reviewed state
  python -I eden_review.py status     does the current HEAD match the stamp?
  python -I eden_review.py clear      the dev drops the stamp (their call, e.g. a reviewed hotfix)

The stamp lives in `.git/eden-review.json` (never committed, one per repo) and holds the tree of the
working state — tracked and untracked files, .gitignore respected — computed with a temporary index, so
the dev's staging area is never touched. Files that were untracked at review time and are not part of the
push do not count. A push whose tree matches consumes the stamp; with no stamp, nothing is enforced.
EDEN_REVIEW_OFF=1 disables the check.
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def git(cwd, *args, env=None):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60, env=env, creationflags=NO_WINDOW)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def stamp_path(cwd):
    gd = git(cwd, "rev-parse", "--absolute-git-dir")
    return Path(gd) / "eden-review.json" if gd else None


def working_tree(cwd):
    """Tree object of the whole working state (tracked + untracked, ignores respected), via a temp index."""
    fd, tmp = tempfile.mkstemp(prefix="eden-index-")
    os.close(fd)
    os.unlink(tmp)  # git creates it; an empty file would be read as a corrupt index
    env = dict(os.environ, GIT_INDEX_FILE=tmp)
    try:
        if git(cwd, "rev-parse", "--verify", "-q", "HEAD"):
            git(cwd, "read-tree", "HEAD", env=env)
        git(cwd, "add", "-A", env=env)
        return git(cwd, "write-tree", env=env)
    finally:
        Path(tmp).unlink(missing_ok=True)


def current_branch(cwd):
    return git(cwd, "rev-parse", "--abbrev-ref", "HEAD")


def load(cwd):
    p = stamp_path(cwd)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else None
    except (OSError, ValueError):
        return None


def stamp(cwd):
    tree = working_tree(cwd)
    if not tree:
        return None
    data = {"tree": tree, "branch": current_branch(cwd), "head": git(cwd, "rev-parse", "HEAD"),
            "untracked": git(cwd, "ls-files", "--others", "--exclude-standard").splitlines(),
            "at": datetime.now().isoformat(timespec="seconds")}
    stamp_path(cwd).write_text(json.dumps(data, indent=1), encoding="utf-8")
    return data


def clear(cwd):
    p = stamp_path(cwd)
    if p and p.exists():
        p.unlink()
        return True
    return False


def drift(cwd, st, commit):
    """Files whose content in `commit` differs from the reviewed state. Untracked-at-review files that
    the push leaves out are fine: they never travel."""
    tree = git(cwd, "rev-parse", f"{commit}^{{tree}}")
    if not tree or tree == st["tree"]:
        return []
    untracked = set(st.get("untracked") or [])
    out = []
    for line in git(cwd, "diff", "--name-status", "--no-renames", st["tree"], tree).splitlines():
        status, _, path = line.partition("\t")
        if status == "D" and path in untracked:
            continue
        out.append(f"{status} {path}")
    return out


def check_push(cwd, branch, commit):
    """(blocking message or None) for pushing `commit` from `branch`. Consumes a matching stamp."""
    if os.environ.get("EDEN_REVIEW_OFF"):
        return None
    st = load(cwd)
    if not st or st.get("branch") != branch:
        return None
    changed = drift(cwd, st, commit)
    if not changed:
        clear(cwd)
        return None
    lines = [f"🔎 Eden: lo que vas a subir en `{branch}` no es lo que se revisó ({st.get('at')}). "
             f"Cambió después de la revisión:"]
    lines += [f"  - {c}" for c in changed[:15]] + ([f"  … y {len(changed) - 15} más"] if len(changed) > 15 else [])
    lines.append("Vuelve a revisar lo que cambió (paso 3 de `turnoff-task`) y sella otra vez. Si el dev decide "
                 "subirlo así, que lo diga: entonces `python -I eden_review.py clear` (o EDEN_REVIEW_OFF=1 para "
                 "este push). Díselo al dev en español; no lo esquives.")
    return "\n".join(lines)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    cwd = os.getcwd()
    if not stamp_path(cwd):
        return print("Aquí no hay un repositorio git.")
    if cmd == "stamp":
        st = stamp(cwd)
        print(f"Sellado: `{st['branch']}` en {st['tree'][:12]} ({len(st['untracked'])} sin trackear no cuentan). "
              "El push tendrá que llevar exactamente esto." if st else "No se pudo calcular el árbol.")
    elif cmd == "clear":
        print("Sello quitado." if clear(cwd) else "No había sello.")
    else:
        st = load(cwd)
        if not st:
            return print("Sin sello: el push no se compara con ninguna revisión.")
        changed = drift(cwd, st, "HEAD")
        print(f"Sello de `{st['branch']}` ({st['at']}): "
              + ("HEAD coincide con lo revisado." if not changed else
                 f"HEAD difiere en {len(changed)} archivo(s): " + ", ".join(changed[:8])
                 + " — falta commitear lo revisado, o algo cambió después."))


if __name__ == "__main__":
    main()
