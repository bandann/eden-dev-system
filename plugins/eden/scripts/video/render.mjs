#!/usr/bin/env node
// Eden explain-video renderer. Zero npm dependencies: drives an installed Chrome/Edge/Chromium over the
// DevTools protocol (Node's built-in WebSocket) and pipes JPEG frames into ffmpeg.
//
//   node render.mjs shots  <shots.json>                       screenshots of real pages
//   node render.mjs render <video.json> [--out FILE] [--ffmpeg EXE --codec h264|vp9] [--fps 30]
//   node render.mjs still  <video.json> --at SECONDS [--out FILE.png]   one frame (poster or check)
//   node render.mjs tools                                      node, browser and ffmpeg it would use
//
// It never navigates anywhere the spec does not name, never fills forms or clicks, and writes only the
// files it is told to write. Called by scripts/eden_video.py, which resolves paths and tools.
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Browser, findBrowser, sleep, withTimeout } from "../lib/cdp.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const debug = (...a) => { if (process.env.EDEN_VIDEO_DEBUG) process.stderr.write("[video " + (performance.now() / 1000).toFixed(1) + "s] " + a.join(" ") + "\n"); };

function arg(name, def) {
  const i = process.argv.indexOf(name);
  return i > -1 && i + 1 < process.argv.length ? process.argv[i + 1] : def;
}

// --- shots: real pages, per viewport -------------------------------------------------------------
async function shots(file) {
  const spec = JSON.parse(readFileSync(file, "utf8"));
  const out = resolve(dirname(file), spec.out || "shots");
  mkdirSync(out, { recursive: true });
  const b = await new Browser().launch();
  const done = [];
  try {
    for (const sh of spec.shots) {
      if (!/^https?:\/\//.test(sh.url)) throw new Error(`shot ${sh.name}: only http(s) URLs`);
      const w = sh.width || 1440, h = sh.height || 900;
      const p = await b.page(w, h, !!sh.mobile);
      await p.goto(sh.url, sh.wait ?? 2000);
      const css = [
        ...(sh.hide || []).map((sel) => `${sel}{visibility:hidden!important}`),
        ...(sh.blur || []).map((sel) => `${sel}{filter:blur(14px)!important}`),
        "*,*::before,*::after{caret-color:transparent!important}",
      ].join("\n");
      await p.eval(`(()=>{const s=document.createElement('style');s.textContent=${JSON.stringify(css)};document.head.append(s);return true})()`);
      if (sh.scrollTo) {
        await p.eval(`(()=>{const e=document.querySelector(${JSON.stringify(sh.scrollTo)});if(e)e.scrollIntoView({block:'start'});window.scrollBy(0,-(${sh.offset || 0}));return !!e})()`);
        await sleep(600);
      }
      let opts = { format: "png" };
      if (sh.fullPage) {
        const hgt = await p.eval("Math.min(Math.max(document.documentElement.scrollHeight, document.body.scrollHeight), 8000)");
        await p.resize(w, hgt);
        await sleep(800);
      }
      const buf = await p.shot(opts);
      const dest = join(out, `${sh.name}.png`);
      writeFileSync(dest, buf);
      done.push({ name: sh.name, file: dest, url: sh.url, width: w });
    }
  } finally {
    await b.close();
  }
  console.log(JSON.stringify({ ok: true, shots: done }, null, 1));
}

// --- render: the player page, frame by frame, into ffmpeg ------------------------------------------
async function still(file) {
  const spec = JSON.parse(readFileSync(file, "utf8"));
  const at = Number(arg("--at", 0));
  const outFile = resolve(arg("--out", join(dirname(resolve(file)), "poster.png")));
  const b = await new Browser().launch();
  try {
    const [W, H] = (spec.format || "vertical") === "horizontal" ? [1920, 1080] : [1080, 1920];
    const p = await b.page(W, H);
    await p.goto(pathToFileURL(join(HERE, "player.html")).href, 300);
    const info = await p.eval(`edenLoad(${JSON.stringify(spec)}, ${JSON.stringify(pathToFileURL(dirname(resolve(file)) + "/").href)})`);
    if (info.missing.length) throw new Error("missing images: " + info.missing.join(", "));
    await p.eval(`edenSeek(${Math.min(at, info.duration - 0.01)})`);
    writeFileSync(outFile, await p.shot({ format: "png" }));
    console.log(JSON.stringify({ ok: true, out: outFile, at, duration: info.duration }));
  } finally {
    await b.close();
  }
}

async function render(file) {
  const spec = JSON.parse(readFileSync(file, "utf8"));
  const fps = Number(arg("--fps", spec.fps || 30));
  const found = findFfmpeg();
  const ffmpeg = arg("--ffmpeg") || found.exe;
  const codec = arg("--codec") || found.codec;
  if (!ffmpeg) throw new Error("no ffmpeg: install one (Windows: winget install Gyan.FFmpeg · macOS: brew install ffmpeg)");
  let outFile = resolve(arg("--out", join(dirname(resolve(file)), "video")));
  if (!/\.(mp4|webm)$/i.test(outFile)) outFile += codec === "vp9" ? ".webm" : ".mp4";
  const [W, H] = (spec.format || "vertical") === "horizontal" ? [1920, 1080] : [1080, 1920];
  const base = pathToFileURL(dirname(resolve(file)) + "/").href;
  const b = await new Browser().launch();
  let ff;
  try {
    debug("browser up");
    const p = await b.page(W, H);
    debug("page ready");
    await p.goto(pathToFileURL(join(HERE, "player.html")).href, 300);
    debug("player loaded");
    const info = await p.eval(`edenLoad(${JSON.stringify(spec)}, ${JSON.stringify(base)})`);
    if (info.missing.length) throw new Error("missing images: " + info.missing.join(", "));
    debug("spec loaded", JSON.stringify(info));
    const frames = Math.ceil(info.duration * fps);
    const enc = codec === "vp9"
      ? ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "30", "-deadline", "good", "-cpu-used", "5", "-row-mt", "1", "-g", String(fps * 2)]
      : ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart"];
    ff = spawn(ffmpeg, ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "pipe:0", ...enc, outFile],
      { stdio: ["pipe", "ignore", "pipe"], windowsHide: true });
    let ffErr = "";
    ff.stderr.on("data", (d) => { ffErr += d.toString(); });
    let ffExited = null;
    const ffDone = new Promise((res) => ff.on("close", (c) => { ffExited = c; res(c); }));
    ff.on("error", (e) => { ffErr += String(e); ffExited = -1; });
    ff.stdin.on("error", () => {}); // a dead ffmpeg is reported below, not as an unhandled EPIPE
    const started = Date.now();
    for (let i = 0; i < frames; i++) {
      if (ffExited !== null) throw new Error("ffmpeg stopped early: " + ffErr.slice(-400));
      await p.eval(`edenSeek(${(i / fps).toFixed(4)})`);
      if (i === 0) debug("first seek ok");
      const jpg = await withTimeout(p.shot({ format: "jpeg", quality: 90 }), 30000, "screenshot timed out");
      if (i === 0) debug("first frame", jpg.length, "bytes");
      if (!ff.stdin.write(jpg)) {
        await Promise.race([new Promise((r) => ff.stdin.once("drain", r)), ffDone]);
      }
      if (i % (fps * 5) === 0) process.stderr.write(`frame ${i}/${frames}\n`);
    }
    ff.stdin.end();
    const code = await ffDone;
    if (code !== 0) throw new Error("ffmpeg failed: " + ffErr.slice(-400));
    console.log(JSON.stringify({ ok: true, out: outFile, frames, fps, duration: info.duration,
      seconds_to_render: Math.round((Date.now() - started) / 1000) }, null, 1));
  } finally {
    try { ff && ff.stdin.end(); } catch { /* ignore */ }
    await b.close();
  }
}

// ffmpeg: EDEN_VIDEO_FFMPEG, then a full ffmpeg on PATH (mp4/h264), then the one Playwright ships
// (VP9 webm only). Node looks this up itself because some Python builds (MSIX-packaged on Windows) and
// their children do not see every folder under %LOCALAPPDATA%.
function findFfmpeg() {
  const env = process.env.EDEN_VIDEO_FFMPEG;
  if (env && existsSync(env)) return { exe: env, codec: "h264" };
  const names = process.platform === "win32" ? ["ffmpeg.exe"] : ["ffmpeg"];
  for (const dir of (process.env.PATH || "").split(process.platform === "win32" ? ";" : ":")) {
    for (const n of names) if (dir && existsSync(join(dir, n))) return { exe: join(dir, n), codec: "h264" };
  }
  const roots = [process.env.LOCALAPPDATA && join(process.env.LOCALAPPDATA, "ms-playwright"),
    process.env.HOME && join(process.env.HOME, ".cache", "ms-playwright"),
    process.env.HOME && join(process.env.HOME, "Library", "Caches", "ms-playwright")].filter(Boolean);
  const found = [];
  for (const r of roots) {
    if (!existsSync(r)) continue;
    for (const d of readdirSync(r).filter((x) => x.startsWith("ffmpeg-")).sort()) {
      for (const f of readdirSync(join(r, d)).filter((x) => x.startsWith("ffmpeg"))) found.push(join(r, d, f));
    }
  }
  return found.length ? { exe: found.pop(), codec: "vp9" } : { exe: null, codec: null };
}

async function tools() {
  const ff = findFfmpeg();
  console.log(JSON.stringify({ ok: true, node: process.version, browser: findBrowser() || null, ffmpeg: ff.exe,
    format: ff.codec === "vp9" ? "webm" : ff.codec ? "mp4" : null }));
}

const [cmd, file] = process.argv.slice(2);
if (cmd === "tools") { await tools(); process.exit(0); }
const run = { shots, render, still }[cmd];
if (!run || !file) {
  console.log("usage: node render.mjs shots <shots.json> | render <video.json> --out FILE --ffmpeg EXE --codec h264|vp9");
  process.exit(2);
}
// Exit explicitly: Chrome's helper processes inherit its stderr pipe and would keep Node waiting.
run(file).then(() => process.exit(0), (e) => { console.log(JSON.stringify({ ok: false, error: String(e.message || e) })); process.exit(1); });
