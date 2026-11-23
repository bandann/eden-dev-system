// Eden's Chrome driver: launches an installed Chrome/Edge/Chromium headless and speaks the DevTools
// protocol over Node's built-in WebSocket (Node 22+). No npm packages. Shared by the explain-video
// renderer (scripts/video/render.mjs) and the motion measurer (scripts/motion/measure.mjs).
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const withTimeout = (p, ms, msg) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(msg)), ms))]);

export function findBrowser() {
  const env = process.env.EDEN_VIDEO_BROWSER;
  const local = process.env.LOCALAPPDATA || "";
  const cands = [
    env,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    local && join(local, "Google/Chrome/Application/chrome.exe"),
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/usr/bin/microsoft-edge",
  ].filter(Boolean);
  return cands.find((p) => existsSync(p));
}

export class Browser {
  async launch() {
    const exe = findBrowser();
    if (!exe) throw new Error("no Chrome, Edge or Chromium found (set EDEN_VIDEO_BROWSER)");
    this.profile = mkdtempSync(join(tmpdir(), "eden-video-"));
    this.proc = spawn(exe, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${this.profile}`,
      "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--mute-audio",
      "--disable-extensions", "--disable-background-networking", "--force-color-profile=srgb",
      "--allow-file-access-from-files", "about:blank"], { stdio: ["ignore", "ignore", "pipe"], windowsHide: true });
    const wsUrl = await new Promise((res, rej) => {
      let buf = "";
      const t = setTimeout(() => rej(new Error("browser did not start: " + buf.slice(-300))), 20000);
      this.proc.stderr.on("data", (d) => {
        buf += d.toString();
        const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
        if (m) { clearTimeout(t); res(m[1]); }
      });
      this.proc.on("exit", (c) => { clearTimeout(t); rej(new Error("browser exited " + c + ": " + buf.slice(-300))); });
    });
    this.ws = new WebSocket(wsUrl);
    await new Promise((res, rej) => { this.ws.onopen = res; this.ws.onerror = () => rej(new Error("CDP connect failed")); });
    this.id = 0; this.pending = new Map(); this.waiters = [];
    this.ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { res, rej } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
      } else if (msg.method) {
        this.waiters = this.waiters.filter((w) => !(w.method === msg.method && w.session === msg.sessionId && (w.res(msg.params), true)));
      }
    };
    return this;
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    return new Promise((res, rej) => this.pending.set(id, { res, rej }));
  }
  once(method, session, timeout = 30000) {
    return new Promise((res) => {
      const w = { method, session, res };
      this.waiters.push(w);
      setTimeout(() => { this.waiters = this.waiters.filter((x) => x !== w); res(null); }, timeout);
    });
  }
  async page(width, height, mobile = false) {
    const { targetId } = await this.send("Target.createTarget", { url: "about:blank" });
    const { sessionId } = await this.send("Target.attachToTarget", { targetId, flatten: true });
    const s = sessionId;
    await this.send("Page.enable", {}, s);
    await this.send("Runtime.enable", {}, s);
    await this.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile }, s);
    if (mobile) await this.send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 }, s);
    return {
      s,
      send: (method, params = {}) => this.send(method, params, s),
      goto: async (url, wait = 1500) => {
        const loaded = this.once("Page.loadEventFired", s, 45000);
        await this.send("Page.navigate", { url }, s);
        await loaded;
        await sleep(wait);
      },
      eval: async (expr) => {
        const r = await this.send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }, s);
        if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
        return r.result.value;
      },
      shot: async (opts) => Buffer.from((await this.send("Page.captureScreenshot", opts, s)).data, "base64"),
      resize: (w, h) => this.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile }, s),
    };
  }
  async close() {
    // Browser.close often gets no reply (the browser is gone first): never wait on it for long.
    const exited = new Promise((r) => (this.proc.exitCode !== null ? r() : this.proc.once("exit", r)));
    try { await withTimeout(this.send("Browser.close"), 1500, "close"); } catch { /* already gone */ }
    try { this.ws.close(); } catch { /* ignore */ }
    await Promise.race([exited, sleep(3000)]);
    try { this.proc.kill(); } catch { /* ignore */ }
    try { rmSync(this.profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }); } catch { /* a lock may linger */ }
  }
}
