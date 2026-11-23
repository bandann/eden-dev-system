#!/usr/bin/env node
// Eden motion measurer: opens a page in headless Chrome/Edge, plays an interaction (scroll, hover, click,
// key, wait) and measures what the animations cost. Zero npm packages (scripts/lib/cdp.mjs).
//
//   node measure.mjs <spec.json>
//
// spec: { url, width, height, mobile, throttle (CPU slowdown, e.g. 4), reducedMotion, wait (ms after
//         load), actions: [{type:"scroll", to:"bottom"|px, speed}, {type:"hover", selector, ms},
//         {type:"click", selector, ms}, {type:"key", key, ms}, {type:"wait", ms}] }
//
// It reads, it does not write to the page's server: no form is filled; `click` is only for opening menus,
// sliders or accordions that the dev named. Output: one JSON object on stdout.
import { readFileSync } from "node:fs";
import { Browser, sleep, withTimeout } from "../lib/cdp.mjs";

const PROBE = `(() => {
  const E = window.__eden = { lcp: null, lcpEl: null, cls: 0, shifts: [], longtasks: [], events: [], frames: [], recording: false, anims: {} };
  const desc = (el) => { if (!el || !el.tagName) return null; let d = el.tagName.toLowerCase();
    if (el.id) d += '#' + el.id; else if (el.classList && el.classList.length) d += '.' + [...el.classList].slice(0, 2).join('.'); return d; };
  E.desc = desc;
  const obs = (type, fn, extra) => { try { new PerformanceObserver((l) => l.getEntries().forEach(fn)).observe({ type, buffered: true, ...extra }); } catch (e) {} };
  obs('largest-contentful-paint', (e) => { E.lcp = e.startTime; E.lcpEl = desc(e.element); });
  obs('layout-shift', (e) => { if (!e.hadRecentInput) { E.cls += e.value; E.shifts.push({ t: e.startTime, v: e.value, recording: E.recording,
    sources: (e.sources || []).slice(0, 3).map((s) => desc(s.node)).filter(Boolean) }); } });
  obs('longtask', (e) => E.longtasks.push({ t: e.startTime, d: e.duration, recording: E.recording }));
  obs('event', (e) => { if (E.recording) E.events.push({ n: e.name, d: e.duration }); }, { durationThreshold: 16 });
  const loop = (t) => { if (E.recording) E.frames.push(t); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  // which properties are being animated right now (CSS transitions/animations and Web Animations)
  E.sample = () => { if (!document.getAnimations) return; for (const a of document.getAnimations()) {
    const tgt = a.effect && a.effect.target; let props = [];
    try { props = [...new Set(a.effect.getKeyframes().flatMap((k) => Object.keys(k)))]
      .filter((p) => !['offset', 'easing', 'composite', 'computedOffset'].includes(p)); } catch (e) {}
    if (a.transitionProperty) props = [a.transitionProperty];
    const key = (desc(tgt) || '?') + '|' + props.join(',');
    E.anims[key] = { target: desc(tgt), props, kind: a.constructor.name, state: a.playState }; } };
  setInterval(() => { if (E.recording) E.sample(); }, 120);
})();`;

const COMPOSITED = new Set(["transform", "opacity", "translate", "scale", "rotate", "filter", "clip-path", "clipPath",
  "backdrop-filter", "backdropFilter", "offset-distance", "offsetDistance"]);
const LAYOUT = /^(width|height|top|left|right|bottom|margin|padding|inset|font-size|fontSize|border-width|borderWidth|line-height|lineHeight|max-|min-|grid-template|gap|flex)/;

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };

async function centerOf(p, selector) {
  const r = await p.eval(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); if (!e) return null;
    e.scrollIntoView({ block: 'center' }); const b = e.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
  if (!r) throw new Error(`selector not found: ${selector}`);
  await sleep(250);
  return r;
}

async function act(p, a, viewportH) {
  if (a.type === "scroll") {
    const total = a.to === "bottom" || a.to == null
      ? await p.eval("Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - innerHeight")
      : Number(a.to);
    const step = viewportH * 0.8;
    // real input gestures (compositor scroll), a screen at a time
    for (let done = 0; done < total; done += step) {
      try {
        await withTimeout(p.send("Input.synthesizeScrollGesture", { x: 200, y: Math.round(viewportH / 2), yDistance: -Math.round(Math.min(step, total - done)),
          speed: a.speed || 1200, gestureSourceType: "mouse", repeatCount: 1 }), 15000, "scroll gesture");
      } catch { await p.eval(`window.scrollBy(0, ${Math.round(step)})`); await sleep(300); }
    }
    await sleep(600);
  } else if (a.type === "hover") {
    const c = await centerOf(p, a.selector);
    await p.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: c.x, y: c.y });
    await sleep(a.ms || 900);
  } else if (a.type === "click") {
    const c = await centerOf(p, a.selector);
    for (const type of ["mousePressed", "mouseReleased"]) await p.send("Input.dispatchMouseEvent", { type, x: c.x, y: c.y, button: "left", clickCount: 1 });
    await sleep(a.ms || 1200);
  } else if (a.type === "key") {
    for (const type of ["keyDown", "keyUp"]) await p.send("Input.dispatchKeyEvent", { type, key: a.key, code: a.key });
    await sleep(a.ms || 800);
  } else if (a.type === "wait") {
    await sleep(a.ms || 1000);
  } else {
    throw new Error(`unknown action ${a.type}`);
  }
}

const metricsMap = (m) => Object.fromEntries((m.metrics || []).map((x) => [x.name, x.value]));
const pct = (arr, q) => { if (!arr.length) return 0; const s = [...arr].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; };
const r1 = (n) => Math.round(n * 10) / 10;

async function measure(spec) {
  if (!/^(https?:|file:)/.test(spec.url || "")) throw new Error("url must be http(s) or a local file:// page");
  const W = spec.width || (spec.mobile ? 390 : 1440), H = spec.height || (spec.mobile ? 844 : 900);
  const b = await new Browser().launch();
  try {
    const p = await b.page(W, H, !!spec.mobile);
    await p.send("Performance.enable", { timeDomain: "timeTicks" });
    if (spec.throttle && spec.throttle > 1) await p.send("Emulation.setCPUThrottlingRate", { rate: spec.throttle });
    if (spec.reducedMotion) await p.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
    await p.send("Page.addScriptToEvaluateOnNewDocument", { source: PROBE });
    await p.goto(spec.url, spec.wait ?? 2000);
    const before = metricsMap(await p.send("Performance.getMetrics"));
    await p.eval("(window.__eden.recording = true, window.__eden.sample(), true)");
    const t0 = Date.now();
    for (const a of spec.actions || [{ type: "scroll", to: "bottom" }]) await act(p, a, H);
    const elapsed = Date.now() - t0;
    await p.eval("(window.__eden.sample(), window.__eden.recording = false, true)");
    const after = metricsMap(await p.send("Performance.getMetrics"));
    const E = await p.eval(`(() => { const E = window.__eden; return { lcp: E.lcp, lcpEl: E.lcpEl, cls: E.cls, shifts: E.shifts,
      longtasks: E.longtasks, events: E.events, frames: E.frames, anims: Object.values(E.anims) }; })()`);

    const deltas = E.frames.slice(1).map((t, i) => t - E.frames[i]);
    const budgetFrame = 1000 / 60;
    const jank = deltas.filter((d) => d > budgetFrame * 1.5).length;
    const dropped = deltas.reduce((n, d) => n + Math.max(0, Math.round(d / budgetFrame) - 1), 0);
    const span = E.frames.length > 1 ? E.frames[E.frames.length - 1] - E.frames[0] : 0;
    const fps = span ? (E.frames.length - 1) / (span / 1000) : 0;
    const lt = E.longtasks.filter((x) => x.recording);
    const anims = E.anims.map((a) => ({ ...a, noncomposited: a.props.filter((pr) => !COMPOSITED.has(pr)),
      layout: a.props.filter((pr) => LAYOUT.test(pr)) }));
    const d = (k) => (after[k] || 0) - (before[k] || 0);
    const res = {
      ok: true, url: spec.url, viewport: `${W}x${H}${spec.mobile ? " mobile" : ""}`, throttle: spec.throttle || 1,
      reducedMotion: !!spec.reducedMotion,
      load: { lcp_ms: E.lcp == null ? null : Math.round(E.lcp), lcp_element: E.lcpEl,
        cls: Math.round(E.shifts.filter((s) => !s.recording).reduce((a, s) => a + s.v, 0) * 1000) / 1000 },
      interaction: { seconds: r1(elapsed / 1000), frames: E.frames.length, fps: r1(fps), p95_frame_ms: r1(pct(deltas, 0.95)),
        jank_frames: jank, dropped_frames: dropped, long_tasks: lt.length, long_task_ms: Math.round(lt.reduce((a, x) => a + x.d, 0)),
        cls: Math.round(E.shifts.filter((s) => s.recording).reduce((a, s) => a + s.v, 0) * 1000) / 1000,
        shift_sources: [...new Set(E.shifts.filter((s) => s.recording).flatMap((s) => s.sources))].slice(0, 6),
        inp_ms: E.events.length ? Math.round(Math.max(...E.events.map((e) => e.d))) : null },
      work: { layouts: Math.round(d("LayoutCount")), style_recalcs: Math.round(d("RecalcStyleCount")),
        layout_ms: Math.round(d("LayoutDuration") * 1000), style_ms: Math.round(d("RecalcStyleDuration") * 1000),
        script_ms: Math.round(d("ScriptDuration") * 1000), task_ms: Math.round(d("TaskDuration") * 1000) },
      animations: anims.slice(0, 40),
    };
    res.budget = budget(res, spec);
    return res;
  } finally {
    await b.close();
  }
}

// The budget of rules/eden-motion-rules.md, as checks. A throttled CPU gets a little slack on fps.
function budget(r, spec) {
  const out = [];
  const add = (id, ok, detail, level = "fail") => out.push({ id, status: ok ? "pass" : level, detail });
  const minFps = (spec.throttle || 1) > 1 ? 50 : 55;
  if (r.interaction.frames > 10) add("fps", r.interaction.fps >= minFps, `${r.interaction.fps} fps (≥ ${minFps})`);
  if (r.interaction.frames > 10) add("jank", r.interaction.jank_frames <= Math.max(2, r.interaction.frames * 0.05),
    `${r.interaction.jank_frames} slow frames of ${r.interaction.frames}`, "warn");
  add("long-tasks", r.interaction.long_tasks === 0, `${r.interaction.long_tasks} long tasks (${r.interaction.long_task_ms} ms) during the interaction`);
  add("cls-interaction", r.interaction.cls === 0, `CLS ${r.interaction.cls} while animating`);
  add("cls-load", r.load.cls <= 0.1, `CLS ${r.load.cls} at load`, r.load.cls > 0.25 ? "fail" : "warn");
  if (r.interaction.inp_ms != null) add("inp", r.interaction.inp_ms <= 200, `slowest input ${r.interaction.inp_ms} ms (≤ 200)`);
  if (r.interaction.frames > 10) add("layout-work", r.work.layouts <= r.interaction.frames * 0.2,
    `${r.work.layouts} layouts in ${r.interaction.frames} frames (${r.work.layout_ms} ms)`, "warn");
  const lay = r.animations.filter((a) => a.layout.length);
  add("layout-properties", lay.length === 0, lay.length ? lay.map((a) => `${a.target}: ${a.layout.join(",")}`).slice(0, 5).join(" · ") : "only composited properties");
  if (spec.reducedMotion) {
    const moving = r.animations.filter((a) => a.props.some((pr) => /transform|translate|scale|rotate/.test(pr)));
    add("reduced-motion", moving.length === 0, moving.length ? `${moving.length} animation(s) still move with reduced motion` : "no movement with reduced motion");
  }
  return out;
}

const file = process.argv[2];
if (!file || file === "--help") {
  console.log("usage: node measure.mjs <spec.json>");
  process.exit(2);
}
measure(JSON.parse(readFileSync(file, "utf8")))
  .then((r) => { console.log(JSON.stringify(r, null, 1)); process.exit(0); },
    (e) => { console.log(JSON.stringify({ ok: false, error: String(e.message || e) })); process.exit(1); });
