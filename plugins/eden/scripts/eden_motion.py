#!/usr/bin/env python3
"""Eden motion: find what makes animations expensive, and measure them in a real browser.

    eden_motion.py lint <path…> [--changed BASE]   static check of CSS / SCSS / Liquid / HTML / JS / TS / JSX /
                                                    Vue / Svelte / PHP against rules/eden-motion-rules.md
    eden_motion.py measure <url> [--scroll] [--hover SEL] [--click SEL] [--key K] [--wait MS]
                       [--mobile] [--throttle N] [--reduced] [--out FILE]
                                                    play the interaction in headless Chrome/Edge and measure
                                                    fps, slow frames, long tasks, layout work, CLS, INP and
                                                    which properties animate (scripts/motion/measure.mjs)
    eden_motion.py compare <before.json> <after.json>   the before → after table of two measurements

`lint --changed BASE` reports only lines added since BASE (git diff), for turnoff-task. Every finding
says file:line, the rule, why it costs and the fix. A static finding is a suspicion; `measure` confirms.
Stdlib only; prints JSON (compare prints Markdown).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEASURE = HERE / "motion" / "measure.mjs"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
EXTS = {".css", ".scss", ".sass", ".less", ".liquid", ".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx",
        ".jsx", ".vue", ".svelte", ".php", ".twig", ".astro"}
SKIP_DIRS = {"node_modules", "vendor", ".git", "dist", "build", ".next", ".nuxt", "coverage", "wp-admin",
             "wp-includes", ".shopify", "graphify-out"}
LAYOUT_PROPS = r"(?:width|height|top|left|right|bottom|margin(?:-\w+)?|padding(?:-\w+)?|inset|font-size|line-height|border(?:-\w+)?-width|max-(?:width|height)|min-(?:width|height))"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def out(data, code=0):
    print(json.dumps(data, indent=1, ensure_ascii=False))
    sys.exit(code)


def opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


# --- static rules -----------------------------------------------------------------------------------
# (id, severity, regex, applies-to, why, fix)
RULES = [
    ("transition-all", "high", re.compile(r"transition(?:-property)?\s*:\s*all\b|transition\s*:\s*[\d.]+m?s\b(?![^;{}]*\b(?:transform|opacity|color|background|border|filter|box-shadow|clip-path|visibility|display|overlay|grid))", re.I),
     "css", "animates every property that changes, layout included", "list the properties: `transition: transform …, opacity …`"),
    ("transition-layout", "high", re.compile(rf"transition(?:-property)?\s*:[^;{{}}]*\b{LAYOUT_PROPS}\b", re.I),
     "css", "a layout property in a transition recalculates layout every frame", "animate `transform` (translate/scale) instead; for accordions use `grid-template-rows: 0fr → 1fr`"),
    ("keyframes-layout", "high", None, "css", "a layout property inside @keyframes recalculates layout every frame",
     "move it to `transform`/`opacity` in the keyframes"),
    ("will-change-global", "medium", re.compile(r"(?:^|[,}\s])(?:\*|html|body|:root)\s*(?:,[^{]*)?\{[^}]*will-change", re.I | re.S),
     "css", "will-change on everything creates a layer per element (memory)", "set will-change only on the element and only while it animates"),
    ("will-change-static", "low", re.compile(r"will-change\s*:\s*(?!auto)[\w-]", re.I),
     "css", "a permanent will-change keeps a GPU layer forever", "add it when the animation starts and remove it on finish (or rely on the browser)"),
    ("scroll-listener", "high", re.compile(r"addEventListener\(\s*['\"](?:scroll|wheel|touchmove)['\"]", re.I),
     "js", "work on every scroll event runs on the main thread", "use `animation-timeline: scroll()/view()` or IntersectionObserver; if unavoidable, `{ passive: true }` + requestAnimationFrame"),
    ("listener-not-passive", "medium", re.compile(r"addEventListener\(\s*['\"](?:scroll|wheel|touchstart|touchmove)['\"][^)]*\)(?![^\n]*passive)", re.I),
     "js", "a non-passive scroll/touch listener can block scrolling", "pass `{ passive: true }`"),
    ("interval-animation", "medium", re.compile(r"setInterval\([\s\S]{0,240}?(?:\.style\.|classList|transform|scroll(?:To|By))", re.I),
     "js", "setInterval animates out of sync with frames and keeps running off screen", "use CSS, element.animate() or requestAnimationFrame, and pause off screen"),
    ("layout-read-in-loop", "medium", re.compile(r"(?:requestAnimationFrame|addEventListener\(\s*['\"](?:scroll|resize)['\"])[\s\S]{0,400}?(?:getBoundingClientRect|offset(?:Top|Left|Height|Width)|scroll(?:Top|Height)|clientHeight)[\s\S]{0,200}?\.style\.", re.I),
     "js", "reading layout and then writing styles in the same frame forces synchronous layout (thrashing)", "read everything first, then write; or let IntersectionObserver measure"),
    ("style-layout-write", "medium", re.compile(rf"\.style\.(?:left|top|right|bottom|width|height|margin\w*|padding\w*)\s*=", re.I),
     "js", "writing a layout property from JS animates layout", "write `transform` (or a CSS custom property used by transform)"),
    ("autoplay-video", "medium", re.compile(r"<video\b[^>]*\bautoplay\b(?![^>]*\bcontrols\b)", re.I),
     "markup", "media that moves by itself for more than 5 s needs a visible pause (WCAG 2.2.2)", "add a pause control, pause off screen and with reduced motion"),
    ("slider-autoplay", "low", re.compile(r"autoplay\s*:\s*(?:true|\{)", re.I),
     "js", "an autoplaying slider needs a visible pause, hover/focus pause and no autoplay with reduced motion", "check the pause button and prefers-reduced-motion"),
    ("gsap-no-cleanup", "medium", None, "js", "GSAP timelines/ScrollTriggers without revert leak and duplicate (Shopify editor, SPA routes)",
     "create them inside gsap.context()/gsap.matchMedia() and revert in disconnectedCallback / cleanup"),
    ("no-reduced-motion", "high", None, "any", "the file animates but never handles prefers-reduced-motion",
     "add `@media (prefers-reduced-motion: reduce)` (CSS) or a `matchMedia('(prefers-reduced-motion: reduce)')` check (JS)"),
    ("hidden-until-js", "medium", re.compile(r"(?:class|data-\w+)=[\"'][^\"']*\b(?:aos|fade-in|reveal|animate__\w+|wow)\b[^\"']*[\"'][^>]*>|data-aos=", re.I),
     "markup", "content hidden until a script animates it delays LCP and stays invisible if the script fails", "keep content visible by default; hide only when the animation will run (see patterns-sections.md)"),
]
CSSY = {".css", ".scss", ".sass", ".less", ".liquid", ".html", ".htm", ".vue", ".svelte", ".astro", ".php", ".twig"}
JSY = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".liquid", ".html", ".htm", ".astro", ".php"}
MARKUPY = {".liquid", ".html", ".htm", ".vue", ".svelte", ".astro", ".php", ".twig", ".jsx", ".tsx"}
ANIMATES = re.compile(r"@keyframes|\banimation\s*:|\banimation-name\s*:|\btransition\s*:|\.animate\(|gsap\.|ScrollTrigger|animation-timeline|startViewTransition", re.I)
REDUCED = re.compile(r"prefers-reduced-motion", re.I)
KEYFRAMES = re.compile(r"@keyframes\s+[\w-]+\s*\{((?:[^{}]*\{[^{}]*\})*)[^{}]*\}", re.I)


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def files_under(paths):
    for p in map(Path, paths):
        if p.is_file() and p.suffix.lower() in EXTS:
            yield p
        elif p.is_dir():
            for dp, dns, fns in os.walk(p):
                dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
                for fn in fns:
                    f = Path(dp) / fn
                    if f.suffix.lower() in EXTS and not fn.endswith(".min.js") and not fn.endswith(".min.css"):
                        yield f


def lint_text(text, suffix):
    found = []
    kinds = {"css": suffix in CSSY, "js": suffix in JSY, "markup": suffix in MARKUPY, "any": True}
    for rid, sev, rx, kind, why, fix in RULES:
        if rx is None or not kinds.get(kind):
            continue
        for m in rx.finditer(text):
            found.append((rid, sev, line_of(text, m.start()), why, fix))
    if kinds["css"]:
        for m in KEYFRAMES.finditer(text):
            body = m.group(1)
            lm = re.search(rf"(?<![-\w]){LAYOUT_PROPS}\s*:", body, re.I)
            if lm:
                r = next(r for r in RULES if r[0] == "keyframes-layout")
                found.append((r[0], r[1], line_of(text, m.start() + lm.start()), r[4], r[5]))
    if kinds["js"] and re.search(r"\bgsap\.(?:to|from|fromTo|timeline)\(|ScrollTrigger\.create", text) and not re.search(
            r"gsap\.(?:context|matchMedia)\(|\.revert\(\)|\.kill\(\)", text):
        r = next(r for r in RULES if r[0] == "gsap-no-cleanup")
        found.append((r[0], r[1], line_of(text, re.search(r"gsap\.|ScrollTrigger", text).start()), r[4], r[5]))
    if ANIMATES.search(text) and not REDUCED.search(text):
        r = next(r for r in RULES if r[0] == "no-reduced-motion")
        found.append((r[0], r[1], line_of(text, ANIMATES.search(text).start()), r[4], r[5]))
    return found


def changed_lines(base, files):
    """{file: set(line numbers)} added since base, from `git diff -U0`."""
    try:
        diff = subprocess.run(["git", "diff", "-U0", f"{base}...HEAD", "--"] + [str(f) for f in files] if files else
                              ["git", "diff", "-U0", f"{base}...HEAD"], capture_output=True, text=True, timeout=60,
                              creationflags=NO_WINDOW).stdout
        diff += subprocess.run(["git", "diff", "-U0"], capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    out_, cur = {}, None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            cur = None if ln.endswith("/dev/null") else Path(ln[6:] if ln.startswith("+++ b/") else ln[4:]).resolve()
        m = re.match(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", ln)
        if m and cur:
            start, n = int(m.group(1)), int(m.group(2) or 1)
            out_.setdefault(cur, set()).update(range(start, start + n))
    return out_


def cmd_lint(argv):
    paths = [a for a in argv if not a.startswith("--") and a != opt(argv, "--changed")] or ["."]
    base = opt(argv, "--changed")
    files = list(files_under(paths))
    scope = changed_lines(base, []) if base else None
    findings, scanned = [], 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned += 1
        for rid, sev, line, why, fix in lint_text(text, f.suffix.lower()):
            if scope is not None:
                lines = scope.get(f.resolve())
                if not lines or (rid != "no-reduced-motion" and line not in lines):
                    continue
            findings.append({"file": f.as_posix(), "line": line, "rule": rid, "severity": sev, "why": why, "fix": fix})
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda x: (order[x["severity"]], x["file"], x["line"]))
    counts = {s: sum(1 for x in findings if x["severity"] == s) for s in order}
    out({"ok": counts["high"] == 0, "scanned": scanned, "counts": counts, "findings": findings,
         "note": "static findings are suspicions: confirm with `eden_motion.py measure` on the real page"})


# --- measuring --------------------------------------------------------------------------------------

def node():
    exe = shutil.which("node")
    if not exe:
        out({"ok": False, "error": "Node 22+ is needed for measuring"}, 1)
    return exe


def cmd_measure(argv):
    url = argv[0] if argv and not argv[0].startswith("--") else None
    if not url:
        out({"ok": False, "error": "usage: measure <url> [--scroll] [--hover SEL] [--click SEL] …"}, 1)
    if Path(url).exists():
        url = Path(url).resolve().as_uri()
    actions = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--scroll":
            actions.append({"type": "scroll", "to": "bottom"})
        elif a in ("--hover", "--click") and i + 1 < len(argv):
            actions.append({"type": a[2:], "selector": argv[i + 1]})
            i += 1
        elif a == "--key" and i + 1 < len(argv):
            actions.append({"type": "key", "key": argv[i + 1]})
            i += 1
        elif a == "--wait" and i + 1 < len(argv):
            actions.append({"type": "wait", "ms": int(argv[i + 1])})
            i += 1
        i += 1
    spec = {"url": url, "mobile": "--mobile" in argv, "reducedMotion": "--reduced" in argv,
            "throttle": float(opt(argv, "--throttle", 1)), "actions": actions or [{"type": "scroll", "to": "bottom"}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(spec, fh)
        tmp = fh.name
    try:
        r = subprocess.run([node(), str(MEASURE), tmp], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600, creationflags=NO_WINDOW)
    finally:
        os.unlink(tmp)
    try:
        res = json.loads(r.stdout)
    except ValueError:
        res = {"ok": False, "error": (r.stdout + r.stderr)[-500:]}
    if opt(argv, "--out") and res.get("ok"):
        Path(opt(argv, "--out")).write_text(json.dumps(res, indent=1), encoding="utf-8")
    out(res, 0 if res.get("ok") else 1)


ROWS = [("fps", "interaction", "fps", True), ("slow frames", "interaction", "jank_frames", False),
        ("p95 frame (ms)", "interaction", "p95_frame_ms", False), ("long tasks", "interaction", "long_tasks", False),
        ("layouts", "work", "layouts", False), ("layout ms", "work", "layout_ms", False),
        ("style recalcs", "work", "style_recalcs", False), ("script ms", "work", "script_ms", False),
        ("CLS while animating", "interaction", "cls", False), ("slowest input (ms)", "interaction", "inp_ms", False),
        ("LCP (ms)", "load", "lcp_ms", False)]


def cmd_compare(argv):
    a, b = (json.loads(Path(x).read_text(encoding="utf-8")) for x in argv[:2])
    lines = [f"| Metric | Before | After | |", "|---|---|---|---|"]
    for label, sec, key, higher_better in ROWS:
        va, vb = (a.get(sec) or {}).get(key), (b.get(sec) or {}).get(key)
        if va is None and vb is None:
            continue
        mark = ""
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and va != vb:
            better = vb > va if higher_better else vb < va
            mark = "✅" if better else "⚠️"
        lines.append(f"| {label} | {va} | {vb} | {mark} |")
    lay = lambda r: sorted({p for x in r.get("animations", []) for p in x.get("layout", [])})
    lines.append(f"| layout properties animated | {', '.join(lay(a)) or '—'} | {', '.join(lay(b)) or '—'} | "
                 f"{'✅' if not lay(b) and lay(a) else ''} |")
    print("\n".join(lines))


def main(argv):
    cmd, rest = (argv[0] if argv else ""), argv[1:]
    if cmd == "lint":
        cmd_lint(rest)
    elif cmd == "measure":
        cmd_measure(rest)
    elif cmd == "compare" and len(rest) >= 2:
        cmd_compare(rest)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
