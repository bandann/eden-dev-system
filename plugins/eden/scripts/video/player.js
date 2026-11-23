/* Eden explain-video player — beats and persistent actors.
 *
 * The renderer calls `await edenLoad(spec, baseUrl)` once, then `edenSeek(t)` per frame. Everything is a
 * pure function of t. A spec is a list of beats; each beat has what is said (`say`) and the actors on
 * screen. An actor with the same `key` in consecutive beats persists and tweens to its new position,
 * size and content ("keep elements between scenes"); a new key enters, a missing key leaves.
 * Captions show at most `captionWords` (4) words at a time, timed inside the beat.
 */
(function () {
  "use strict";
  const TWEEN = 0.6, ENTER = 0.55, EXIT = 0.3;
  const stage = document.getElementById("stage");
  const caption = document.getElementById("caption");
  const bar = document.querySelector("#progress span");
  let W = 1080, H = 1920, beats = [], segments = [], total = 0, capWords = 4, showCaptions = true;

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const back = (x) => { x = clamp(x); const c = 1.4; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const lerp = (a, b, p) => a + (b - a) * p;
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const fmt = (n, d) => (d ? n.toFixed(d) : Math.round(n).toLocaleString("en-US"));

  // *word* → accent
  function rich(node, text) {
    node.textContent = "";
    String(text || "").split(/(\*[^*]+\*)/).forEach((part) => {
      if (!part) return;
      if (part.startsWith("*") && part.endsWith("*")) node.append(el("em", null, part.slice(1, -1)));
      else node.append(document.createTextNode(part));
    });
  }

  // Simple line icons (24×24), drawn with a stroke animation on entry.
  const ICONS = {
    check: "M5 12.5l4.5 4.5L19 7.5",
    code: "M8.5 7L3.5 12l5 5M15.5 7l5 5-5 5M13.5 4.5l-3 15",
    bug: "M8 9h8v6a4 4 0 0 1-8 0zM12 9v10M8 12H4M20 12h-4M8 16l-3 2M16 16l3 2M9 9a3 3 0 0 1 6 0",
    mobile: "M7.5 2.5h9a1.5 1.5 0 0 1 1.5 1.5v16a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 20V4a1.5 1.5 0 0 1 1.5-1.5zM10.5 18.5h3",
    desktop: "M3 4.5h18v11H3zM9 19.5h6M12 15.5v4",
    page: "M6 2.5h8l4 4v15H6zM14 2.5v4h4M9 11h6M9 14.5h6M9 18h4",
    link: "M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1",
    image: "M3.5 5h17v14h-17zM3.5 15.5l5-4.5 4 3.5 3-2.5 5 4M15.5 9.5a1 1 0 1 0 0 .01",
    cart: "M3 4h2.5l2.2 11h10.6l2-8H6.6M9.5 19.5a1 1 0 1 0 0 .01M17 19.5a1 1 0 1 0 0 .01",
    clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7.5V12l3 2",
    sparkle: "M12 3v5M12 16v5M3 12h5M16 12h5M6 6l3 3M15 15l3 3M18 6l-3 3M9 15l-3 3",
    layers: "M12 3l9 5-9 5-9-5zM3 13l9 5 9-5",
    search: "M10.5 4a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM15.5 15.5L20 20",
    bolt: "M13 2.5L5 13.5h6l-1 8 8-11h-6z",
    arrow: "M4 12h15M13 6l6 6-6 6",
    eye: "M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
    shield: "M12 2.5l8 3v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10v-6zM8.5 12l2.5 2.5 4.5-5",
    gauge: "M4 17a8 8 0 1 1 16 0M12 17l4-5",
  };
  const svgIcon = (name) => {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    const p = document.createElementNS(ns, "path");
    p.setAttribute("d", ICONS[name] || ICONS.sparkle);
    p.setAttribute("pathLength", "1");
    p.style.strokeDasharray = "1";
    svg.append(p);
    return { svg, path: p };
  };

  function loadImage(src, base) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => (img.decode ? img.decode().catch(() => null) : Promise.resolve()).then(() => resolve(img));
      img.onerror = () => resolve(null);
      img.src = new URL(src, base).href;
    });
  }

  // --- actor kinds: build(a) → {node, render(state, prevState, contentAge, assets)} -----------------
  const KINDS = {
    text(a) {
      const n = el("div", "k-text");
      return { node: n, render(s) { n.style.fontSize = (s.size || 96) + "px"; if (n._t !== s.text) { rich(n, s.text); n._t = s.text; } } };
    },
    badge(a) {
      const n = el("div", null); const b = el("span", "k-badge"); n.style.textAlign = "center"; n.append(b);
      return { node: n, render(s) { b.textContent = s.text || ""; } };
    },
    icon(a) {
      const n = el("div", "k-icon" + (a.muted ? " muted" : ""));
      let cur = null;
      return { node: n, render(s, prev, age) {
        if (!cur || cur.name !== s.name) { n.textContent = ""; cur = { name: s.name, ...svgIcon(s.name) }; n.append(cur.svg); }
        n.style.height = n.style.width;
        cur.path.style.strokeDashoffset = String(1 - ease(age / 0.9));
      } };
    },
    card(a) {
      const n = el("div", "k-card");
      const h = el("h4"); const title = el("span"); h.append(el("i"), title);
      const body = el("div");
      n.append(h, body);
      return { node: n, render(s, prev, age) {
        title.textContent = s.title || "";
        if (body._k !== JSON.stringify([s.text, s.lines])) {
          body.textContent = ""; body._k = JSON.stringify([s.text, s.lines]);
          if (s.text) body.append(el("p", null, s.text));
          for (let i = 0; i < (s.lines ?? (s.text ? 0 : 3)); i++) { const l = el("div", "ln"); l.style.width = [92, 76, 58, 84][i % 4] + "%"; body.append(l); }
        }
        [...body.querySelectorAll(".ln")].forEach((l, i) => { l.style.transformOrigin = "left"; l.style.transform = `scaleX(${ease((age - 0.25 - i * 0.12) / 0.5)})`; });
      } };
    },
    shot(a, assets) {
      const n = el("div", "k-shot " + (a.device || "browser"));
      const view = el("div", "view"); n.append(view);
      const base = el("div"); base.style.position = "relative"; view.append(base);
      let built = null;
      return { node: n, render(s, prev, age) {
        const cls = "k-shot actor " + (s.device || "browser");
        if (n.className !== cls) n.className = cls;
        const key = JSON.stringify([s.src, s.before, s.marks]);
        if (built !== key) {
          built = key; base.textContent = "";
          const imgA = assets[s.before || s.src], imgB = s.before ? assets[s.src] : null;
          if (imgA) base.append(imgA.cloneNode());
          if (imgB) {
            const after = el("div", "after"); after.append(imgB.cloneNode()); base.append(after);
            base.append(el("div", "divider"), el("div", "tag tag-before", s.beforeLabel || "Before"), el("div", "tag tag-after", s.afterLabel || "After"));
          }
          (s.marks || []).forEach((m) => { const k = el("div", "k-mark"); k.style.left = m.x + "%"; k.style.top = m.y + "%"; k.style.width = m.w + "%"; k.style.height = m.h + "%"; k._at = m.at || 0.6; base.append(k); });
        }
        // compare wipe: reveal "after" from right to left, settle at 50 %
        const after = base.querySelector(".after"), div = base.querySelector(".divider");
        if (after) {
          const pos = 100 - 100 * ease((age - 0.3) / 1.4) + 50 * ease((age - 1.9) / 0.6);
          after.style.clipPath = `inset(0 0 0 ${pos}%)`; div.style.left = pos + "%";
        }
        base.querySelectorAll(".k-mark").forEach((m) => { const p = back((age - m._at) / 0.45); m.style.opacity = clamp(p); m.style.transform = `scale(${0.85 + 0.15 * p})`; });
        // pan a tall capture slowly when the frame is shorter than the image
        const img = base.querySelector("img");
        if (img && s.pan !== false) {
          const over = Math.max(0, img.offsetHeight - view.clientHeight);
          base.style.transform = `translateY(${-over * ease((age - 0.8) / Math.max(2.5, s.panSeconds || 4))}px)`;
        }
      } };
    },
    counter(a) {
      const n = el("div", "k-counter"); const num = el("div", "num"); const lab = el("div", "lab"); n.append(num, lab);
      return { node: n, render(s, prev, age) {
        const from = s.from ?? (prev && prev.value != null ? prev.value : 0);
        const v = lerp(from, s.value || 0, ease(age / 1.1));
        num.textContent = (s.prefix || "") + fmt(v, s.decimals) + (s.suffix || "");
        lab.textContent = s.label || "";
      } };
    },
    bars(a) {
      const n = el("div", "k-bars");
      return { node: n, render(s, prev, age) {
        const items = s.items || [];
        if (n.children.length !== items.length) {
          n.textContent = "";
          items.forEach(() => { const b = el("div", "bar"); b.append(el("div", "v"), el("div", "fill"), el("div", "l")); n.append(b); });
        }
        const max = Math.max(...items.map((i) => i.value), 1);
        items.forEach((it, i) => {
          const b = n.children[i], p = ease((age - 0.2 - i * 0.15) / 0.8);
          b.className = "bar" + (it.hi ? " hi" : "");
          b.querySelector(".fill").style.height = `calc(${(70 * p * it.value) / max}% )`;
          b.querySelector(".v").textContent = fmt(it.value * p, it.decimals) + (it.suffix || "");
          b.querySelector(".l").textContent = it.label || "";
        });
      } };
    },
    prompt(a) {
      const n = el("div", "k-prompt"); const star = el("span", "star", "✦"); const txt = el("span"); n.append(star, txt);
      return { node: n, render(s, prev, age) {
        const plain = String(s.text || "");
        const shown = Math.floor(plain.replace(/\*/g, "").length * clamp((age - 0.2) / Math.max(0.6, (s.typeSeconds || plain.length / 45))));
        // rebuild the visible part with highlights
        txt.textContent = "";
        let left = shown;
        plain.split(/(\*[^*]+\*)/).forEach((part) => {
          if (!part || left <= 0) return;
          const hl = part.startsWith("*") && part.endsWith("*");
          const raw = hl ? part.slice(1, -1) : part;
          const piece = raw.slice(0, left); left -= raw.length;
          txt.append(hl ? el("span", "hl", piece) : document.createTextNode(piece));
        });
        txt.append(el("span", "cursor"));
      } };
    },
    code(a) {
      const n = el("div", "k-code"); const file = el("div", "file"); const pre = el("pre"); n.append(file, pre);
      return { node: n, render(s, prev, age) {
        file.textContent = s.file || "";
        const lines = (s.lines || []).map((l) => (typeof l === "string" ? { t: " ", s: l } : l));
        const chars = lines.reduce((x, l) => x + l.s.length + 1, 0) || 1;
        let left = Math.floor(chars * clamp((age - 0.2) / Math.max(0.7, chars / 70)));
        const done = left >= chars;
        pre.textContent = "";
        for (const l of lines) {
          if (left <= 0) break;
          const sp = el("span", l.t === "+" ? "add" : l.t === "-" ? "del" : null, (l.t === "+" ? "+ " : l.t === "-" ? "- " : "  ") + l.s.slice(0, left));
          const full = left > l.s.length;
          if (!full && !done) sp.append(el("span", "cursor"));
          pre.append(sp);
          if (full) pre.append(document.createTextNode("\n"));
          left -= l.s.length + 1;
        }
      } };
    },
    list(a) {
      const n = el("div", "k-list");
      return { node: n, render(s, prev, age) {
        const items = s.items || [];
        if (n._k !== JSON.stringify(items)) {
          n._k = JSON.stringify(items); n.textContent = "";
          items.forEach((t) => { const it = el("div", "it"); const ic = svgIcon("check"); it.append(ic.svg, el("span", null, t)); it._p = ic.path; n.append(it); });
        }
        [...n.children].forEach((it, i) => {
          const p = ease((age - 0.15 - i * 0.3) / 0.4);
          it.style.opacity = p; it.style.transform = `translateX(${(1 - p) * -30}px)`;
          it._p.style.strokeDashoffset = String(1 - ease((age - 0.3 - i * 0.3) / 0.35));
        });
      } };
    },
  };

  // --- timeline: segments of consecutive beats per key --------------------------------------------
  function buildSegments(assets) {
    const segs = [], open = {};
    beats.forEach((b, bi) => {
      const keys = new Set();
      (b.actors || []).forEach((a, ai) => {
        const key = a.key || `${bi}:${ai}`;
        keys.add(key);
        let seg = open[key];
        if (!seg || seg.kind !== a.kind) {
          const k = (KINDS[a.kind] || KINDS.text)(a, assets);
          k.node.classList.add("actor");
          stage.append(k.node);
          seg = { key, kind: a.kind, view: k, states: {}, first: bi, last: bi };
          segs.push(seg);
          open[key] = seg;
        }
        seg.states[bi] = { ...a };
        seg.last = bi;
      });
      Object.keys(open).forEach((k) => { if (!keys.has(k)) delete open[k]; });
    });
    return segs;
  }

  function stateAt(seg, bi) {
    for (let i = bi; i >= seg.first; i--) if (seg.states[i]) return seg.states[i];
    return seg.states[seg.first];
  }

  function contentChanged(a, b) {
    if (!a || !b) return true;
    const strip = (s) => { const { x, y, w, h, scale, opacity, rotate, key, ...rest } = s; return JSON.stringify(rest); };
    return strip(a) !== strip(b);
  }

  function place(seg, t) {
    const n = seg.view.node;
    const start = beats[seg.first].start, end = beats[seg.last].start + beats[seg.last].duration;
    if (t < start || t > end + EXIT) { n.style.opacity = 0; n.style.visibility = "hidden"; return; }
    n.style.visibility = "visible";
    const bi = beatIndex(t);
    const cur = stateAt(seg, Math.min(bi, seg.last));
    const prevState = bi > seg.first ? stateAt(seg, bi - 1) : null;
    const since = t - beats[Math.min(bi, seg.last)].start;
    const p = prevState ? ease(since / TWEEN) : 1;
    const from = prevState || cur;
    const x = lerp(from.x ?? 50, cur.x ?? 50, p), y = lerp(from.y ?? 50, cur.y ?? 50, p);
    const w = lerp(from.w ?? 70, cur.w ?? 70, p);
    const sc = lerp(from.scale ?? 1, cur.scale ?? 1, p);
    let op = lerp(from.opacity ?? 1, cur.opacity ?? 1, p);
    // entry
    const age0 = t - start, e = ease(age0 / ENTER);
    op *= e;
    const rise = (1 - e) * 50;
    // exit
    if (t > end) op *= 1 - clamp((t - end) / EXIT);
    n.style.width = (w / 100) * W + "px";
    if (cur.h != null) n.style.height = (lerp(from.h ?? cur.h, cur.h, p) / 100) * H + "px";
    n.style.left = (x / 100) * W + "px";
    n.style.top = (y / 100) * H + "px";
    n.style.opacity = op;
    n.style.transform = `translate(-50%, -50%) translateY(${rise}px) scale(${sc * (0.94 + 0.06 * e)}) rotate(${cur.rotate || 0}deg)`;
    // content age: since the beat where this actor's content last changed
    let cb = Math.min(bi, seg.last);
    while (cb > seg.first && !contentChanged(stateAt(seg, cb), stateAt(seg, cb - 1))) cb--;
    seg.view.render(cur, cb > seg.first ? stateAt(seg, cb - 1) : null, t - beats[cb].start);
  }

  function beatIndex(t) {
    for (let i = beats.length - 1; i >= 0; i--) if (t >= beats[i].start) return i;
    return 0;
  }

  // --- captions: ≤ capWords words at a time, timed by length inside the beat ----------------------
  function chunks(b) {
    if (b._chunks) return b._chunks;
    const words = String(b.say || "").replace(/\*/g, "").split(/\s+/).filter(Boolean);
    const hl = new Set((b.hl || []).map((w) => w.toLowerCase()));
    String(b.say || "").replace(/\*([^*]+)\*/g, (_, w) => { w.split(/\s+/).forEach((x) => hl.add(x.toLowerCase().replace(/[^\p{L}\p{N}]/gu, ""))); return _; });
    const out = [];
    for (let i = 0; i < words.length;) {
      let n = Math.min(capWords, words.length - i);
      // end a chunk at punctuation when it comes early
      for (let k = 1; k < n; k++) if (/[,.;:!?]$/.test(words[i + k - 1])) { n = k; break; }
      out.push(words.slice(i, i + n));
      i += n;
    }
    const weight = out.map((c) => c.join(" ").length + 4);
    const sum = weight.reduce((a, b2) => a + b2, 0) || 1;
    let acc = 0;
    const usable = b.duration - 0.15;
    b._chunks = out.map((c, i) => {
      const s = (acc / sum) * usable; acc += weight[i];
      return { words: c, start: s, end: (acc / sum) * usable, hl };
    });
    return b._chunks;
  }

  function renderCaption(t) {
    if (!showCaptions) { caption.style.opacity = 0; return; }
    const b = beats[beatIndex(t)], l = t - b.start;
    const c = chunks(b).find((x) => l >= x.start && l < x.end);
    if (!c) { caption.style.opacity = 0; return; }
    const key = b.index + ":" + c.start;
    if (caption._k !== key) {
      caption._k = key; caption.textContent = "";
      c.words.forEach((w) => caption.append(el("span", "w" + (c.hl.has(w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "")) ? " hl" : ""), w)));
    }
    const p = back((l - c.start) / 0.16);
    caption.style.opacity = clamp(p * 1.4);
    caption.style.transform = `scale(${0.82 + 0.18 * p})`;
  }

  window.edenLoad = async function (spec, base) {
    const vertical = (spec.format || "vertical") !== "horizontal";
    W = vertical ? 1080 : 1920; H = vertical ? 1920 : 1080;
    document.documentElement.style.width = document.body.style.width = W + "px";
    document.documentElement.style.height = document.body.style.height = H + "px";
    if (spec.accent) document.documentElement.style.setProperty("--accent", spec.accent);
    if (spec.theme) Object.entries(spec.theme).forEach(([k, v]) => document.documentElement.style.setProperty("--" + k, v));
    capWords = spec.captionWords || 4;
    showCaptions = spec.captions !== false;
    caption.style.top = (vertical ? 63 : 78) + "%";
    caption.style.fontSize = (vertical ? 92 : 70) + "px";
    stage.textContent = "";
    const srcs = new Set();
    (spec.beats || []).forEach((b) => (b.actors || []).forEach((a) => ["src", "before"].forEach((k) => a[k] && srcs.add(a[k]))));
    const assets = {};
    await Promise.all([...srcs].map(async (s) => { assets[s] = await loadImage(s, base); }));
    let start = 0;
    beats = (spec.beats || []).map((b, i) => { const x = { ...b, index: i, start }; start += b.duration; return x; });
    total = start;
    segments = buildSegments(assets);
    return { duration: total, width: W, height: H, missing: [...srcs].filter((k) => !assets[k]) };
  };

  window.edenSeek = function (t) {
    segments.forEach((s) => place(s, t));
    renderCaption(t);
    bar.style.width = 100 * clamp(t / (total || 1)) + "%";
    return true;
  };
})();
