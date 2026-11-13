"""Eden stack detection — which stack (and flavour) a project is, from the repo alone.

Usage: python -I eden_stack.py detect [path]
Prints JSON: {stack, flavor, evidence, declared, candidates[], ambiguous}. It never guesses: a declared
stack (.claude/project-config.json → project.stack, or <!-- eden-stack: x --> in CLAUDE.md) is reported
as such, and a repo where two different stacks fit (a monorepo) is flagged as ambiguous for the dev to
decide. The order of RULES is the one documented in rules/eden-stack-rules.md: keep them in sync.
Stdlib only.
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

SUBPROJECT_DIRS = ("apps", "packages", "services", "backend", "frontend", "api", "web", "mobile", "app",
                   "client", "server")
# The project's instructions file, per AI tool (rules/eden-stack-rules.md); the first with a marker wins.
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "QWEN.md")
SKIP = {"node_modules", "vendor", ".git", ".next", "dist", "build", ".expo", "ios", "android"}


def read_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def npm_deps(root):
    pkg = read_json(root / "package.json")
    deps = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(pkg.get(k) or {})
    return set(deps), pkg


def composer_deps(root):
    c = read_json(root / "composer.json")
    return set((c.get("require") or {}) | (c.get("require-dev") or {}))


def has(root, *globs):
    return any(next(root.glob(g), None) for g in globs)


def theme_style(root):
    try:
        return "Theme Name:" in (root / "style.css").read_text(encoding="utf-8", errors="ignore")[:2000]
    except OSError:
        return False


def detect_dir(root):
    """First matching rule for one directory: (stack, flavor, evidence) or None."""
    deps, _ = npm_deps(root)
    cdeps = composer_deps(root)
    rules = [
        (lambda: has(root, "shopify.app.toml", "shopify.app.*.toml"), "shopify-app", None, "shopify.app.toml"),
        (lambda: (root / "sections").is_dir() and (root / "snippets").is_dir()
         and (root / "config" / "settings_schema.json").is_file(), "shopify", None,
         "sections/ + snippets/ + config/settings_schema.json"),
        (lambda: (root / "wp-content").is_dir() or (root / "wp-config.php").is_file() or theme_style(root),
         "wordpress", None, "wp-content/ · wp-config.php · style.css Theme Name"),
        (lambda: "laravel/framework" in cdeps or (root / "artisan").is_file(), "php", "laravel",
         "composer.json laravel/framework · artisan"),
        (lambda: bool(deps & {"expo", "react-native"}), "mobile", "react-native", "dependency expo / react-native"),
        (lambda: any(d.startswith("@ionic/") for d in deps) or "@capacitor/core" in deps
         or has(root, "ionic.config.json", "capacitor.config.*"), "mobile", "ionic",
         "@ionic/* · @capacitor/core · ionic.config.json · capacitor.config.*"),
        (lambda: "next" in deps or has(root, "next.config.*"), "react", "next", "dependency next · next.config.*"),
        (lambda: "@nestjs/core" in deps or (root / "nest-cli.json").is_file(), "node", "nest",
         "dependency @nestjs/core · nest-cli.json"),
        (lambda: "express" in deps, "node", "express", "dependency express"),
        (lambda: "react" in deps, "react", "spa", "dependency react"),
        (lambda: (root / "composer.json").is_file() or has(root, "*.php"), "php", "php", "composer.json · *.php"),
        (lambda: (root / "package.json").is_file() and not has(root, "astro.config.*"), "node", "node",
         "package.json"),
        (lambda: has(root, "astro.config.*"), "astro", None, "astro.config.* (no Eden module)"),
    ]
    for test, stack, flavor, evidence in rules:
        if test():
            return stack, flavor, evidence
    return None


def subprojects(root):
    """Directories one or two levels down that look like their own project (monorepo workspaces)."""
    found = []
    for name in SUBPROJECT_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        cands = [base] + [c for c in base.iterdir() if c.is_dir() and c.name not in SKIP]
        for c in cands:
            if (c / "package.json").is_file() or (c / "composer.json").is_file() or has(c, "shopify.app.toml"):
                found.append(c)
    return sorted(set(found))


def declared(root):
    cfg = read_json(root / ".claude" / "project-config.json")
    stack = (cfg.get("project") or {}).get("stack")
    if stack:
        flavor = (cfg.get(stack.replace("-", "_")) or cfg.get(stack) or {}).get("flavor")
        return {"stack": stack, "flavor": flavor, "source": ".claude/project-config.json"}
    for name in INSTRUCTION_FILES:  # the project's instructions file, whichever AI tool it is for
        try:
            md = (root / name).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r"<!--\s*(?:eden|fl)-stack:\s*([\w-]+)", md)
        if m:
            return {"stack": m.group(1), "flavor": None, "source": name}
    return None


def detect(path):
    root = Path(path or ".").resolve()
    found = detect_dir(root)
    candidates = []
    if found:
        candidates.append({"path": ".", "stack": found[0], "flavor": found[1], "evidence": found[2]})
    for sub in subprojects(root):
        r = detect_dir(sub)
        if r:
            candidates.append({"path": sub.relative_to(root).as_posix(), "stack": r[0], "flavor": r[1],
                               "evidence": r[2]})
    # a root that is only a workspace manifest (package.json without a framework) defers to its apps
    if found and found[:2] == ("node", "node") and len(candidates) > 1:
        candidates = candidates[1:]
    stacks = {(c["stack"], c["flavor"]) for c in candidates}
    primary = candidates[0] if candidates else None
    return {
        "path": root.as_posix(),
        "declared": declared(root),
        "stack": primary["stack"] if primary else None,
        "flavor": primary["flavor"] if primary else None,
        "evidence": primary["evidence"] if primary else None,
        "candidates": candidates,
        "ambiguous": len({s for s, _ in stacks}) > 1,
    }


def main(argv):
    if not argv or argv[0] != "detect":
        print(__doc__)
        return 2
    print(json.dumps(detect(argv[1] if len(argv) > 1 else "."), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
