// Eden w2shopify — read-only design extraction of a rendered web page, run with Playwright's
// browser_evaluate at one viewport. It measures what the browser actually renders (computed styles and
// boxes), not the source CSS, so it works the same on React, Webflow, WordPress, Wix or hand-written HTML.
// It never modifies the page, never sends anything anywhere, and returns compact JSON: sections with
// their container, typography, buttons, media and repeated grids, plus the page's palette, type scale,
// spacing, fonts (with where they are served from, for licensing) and technology hints.
() => {
  // the layout viewport (innerWidth can include scrollbars or an emulation's outer size)
  const VW = document.documentElement.clientWidth || window.innerWidth;
  const VH = document.documentElement.clientHeight || window.innerHeight;
  const MAX_SECTIONS = 40, MAX_ITEMS = 24, TXT = 140;
  const px = (v) => Math.round((parseFloat(v) || 0) * 10) / 10;
  const clip = (t) => { t = (t || '').replace(/\s+/g, ' ').trim(); return t.length > TXT ? t.slice(0, TXT) + '…' : t; };
  const hex = (c) => {
    const m = (c || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return c && c !== 'transparent' ? c : null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    if (p.length > 3 && p[3] === 0) return null;
    const h = '#' + p.slice(0, 3).map((n) => Math.round(n).toString(16).padStart(2, '0')).join('');
    return p.length > 3 && p[3] < 1 ? `${h}/${Math.round(p[3] * 100)}%` : h;
  };
  const cs = (el) => getComputedStyle(el);
  const visible = (el) => {
    const s = cs(el), r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0 && r.width > 1 && r.height > 1;
  };
  const rect = (el) => {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) };
  };
  const typo = (s) => ({
    family: (s.fontFamily || '').split(',')[0].replace(/["']/g, '').trim(),
    size: px(s.fontSize), weight: Number(s.fontWeight) || s.fontWeight,
    lineHeight: s.lineHeight === 'normal' ? 'normal' : px(s.lineHeight),
    letterSpacing: s.letterSpacing === 'normal' ? 0 : px(s.letterSpacing),
    transform: s.textTransform !== 'none' ? s.textTransform : undefined,
    style: s.fontStyle !== 'normal' ? s.fontStyle : undefined,
    color: hex(s.color), align: s.textAlign,
  });
  const boxOf = (s) => ({
    padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].map(px),
    gap: s.gap && s.gap !== 'normal' ? s.gap : undefined,
    display: s.display,
    flex: s.display.includes('flex') ? { direction: s.flexDirection, justify: s.justifyContent, align: s.alignItems, wrap: s.flexWrap } : undefined,
    grid: s.display.includes('grid') ? { columns: s.gridTemplateColumns.split(' ').filter(Boolean).length, template: s.gridTemplateColumns.slice(0, 120) } : undefined,
    background: hex(s.backgroundColor) || undefined,
    backgroundImage: s.backgroundImage !== 'none' ? (s.backgroundImage.startsWith('url') ? 'image' : s.backgroundImage.slice(0, 80)) : undefined,
    radius: s.borderRadius !== '0px' ? s.borderRadius : undefined,
    border: parseFloat(s.borderTopWidth) > 0 ? `${s.borderTopWidth} ${s.borderTopStyle} ${hex(s.borderTopColor)}` : undefined,
    shadow: s.boxShadow !== 'none' ? s.boxShadow.slice(0, 80) : undefined,
  });
  const ownText = (el) => [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ').trim();

  // ---------- sections: top-level visual bands, wrappers unwrapped, nested duplicates removed
  const seeds = new Set();
  document.querySelectorAll('header, [role=banner], nav, main > *, [role=main] > *, footer, [role=contentinfo], body > *, section').forEach((e) => seeds.add(e));
  const SEMANTIC = ['HEADER', 'FOOTER', 'SECTION', 'NAV', 'ASIDE', 'ARTICLE', 'FORM'];
  const wide = (el) => { const r = el.getBoundingClientRect(); return r.width >= VW * 0.6 && r.height >= 40; };
  const blockKids = (el) => [...el.children].filter((c) => visible(c) && wide(c));
  const expand = (el, depth = 0) => {
    const kids = blockKids(el);
    const r = el.getBoundingClientRect();
    // a lone full-height child is a wrapper — but a semantic band keeps its own box (background, border, sticky)
    if (depth < 6 && kids.length === 1 && kids[0].getBoundingClientRect().height >= r.height * 0.9
        && !SEMANTIC.includes(el.tagName)) return expand(kids[0], depth + 1);
    if (depth < 6 && kids.length >= 2 && (r.height > VH * 1.6 || ['MAIN', 'BODY', 'DIV', 'ARTICLE'].includes(el.tagName) && kids.length >= 3))
      return kids.flatMap((k) => expand(k, depth + 1));
    return [el];
  };
  let bands = [];
  seeds.forEach((e) => { if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'LINK', 'TEMPLATE'].includes(e.tagName)) return; if (visible(e) && wide(e)) bands.push(...expand(e)); });
  // Nesting: a band holding 2+ other bands is a wrapper (keep what is inside); a band holding exactly one
  // (a <nav> inside the <header>) is the section itself (drop the inner one).
  bands = [...new Set(bands)];
  const inner = (e) => bands.filter((o) => o !== e && e.contains(o));
  bands = bands.filter((e) => inner(e).length < 2);
  bands = bands.filter((e) => !bands.some((o) => o !== e && o.contains(e)));
  bands.sort((a, b) => rect(a).y - rect(b).y);
  bands = bands.slice(0, MAX_SECTIONS);

  const hintOf = (el, i, s, heads, imgs) => {
    const t = el.tagName, role = el.getAttribute('role');
    if (t === 'HEADER' || role === 'banner' || (i === 0 && el.querySelector('nav'))) return 'header';
    if (t === 'FOOTER' || role === 'contentinfo') return 'footer';
    if (t === 'NAV') return 'navigation';
    if (el.querySelector('form input:not([type=hidden])')) return el.querySelector('input[type=email]') ? 'newsletter' : 'form';
    if (heads.some((h) => h.tag === 'h1') || (i <= 2 && imgs.some((m) => m.rendered.w >= VW * 0.5))) return 'hero';
    if (el.querySelectorAll('details, [aria-expanded]').length >= 3) return 'accordion/faq';
    return 'content';
  };

  // repeated children (cards, logos, columns): the container with ≥3 same-size visible children
  const repeated = (root) => {
    let best = null;
    root.querySelectorAll('*').forEach((el) => {
      // the largest group of same-tag children: a heading above three cards is not a fourth card
      const groups = {};
      [...el.children].filter(visible).forEach((k) => { (groups[k.tagName] = groups[k.tagName] || []).push(k); });
      const kids = Object.values(groups).sort((a, b) => b.length - a.length)[0] || [];
      if (kids.length < 3) return;
      const rs = kids.map((k) => k.getBoundingClientRect());
      const w0 = rs[0].width;
      if (!rs.every((r) => Math.abs(r.width - w0) <= Math.max(4, w0 * 0.08)) || w0 < 40) return;
      if (!best || kids.length > best.count) {
        const rowY = Math.round(rs[0].top);
        const cols = rs.filter((r) => Math.abs(Math.round(r.top) - rowY) <= 4).length;
        const s = cs(el);
        best = { count: kids.length, columns: cols, itemWidth: Math.round(w0), gap: s.gap !== 'normal' ? s.gap : undefined,
                 item: { tag: kids[0].tagName.toLowerCase(), ...boxOf(cs(kids[0])) } };
      }
    });
    return best;
  };

  const sections = bands.map((el, i) => {
    const s = cs(el), r = rect(el);
    // content container: the outermost descendant with a max-width (the site's wrapper), else the widest
    // descendant narrower than the band. Its padding is the gutter at this viewport.
    let container = null;
    const asContainer = (d) => { const dr = d.getBoundingClientRect(), ds = cs(d);
      return { w: Math.round(dr.width), x: Math.round(dr.left), maxWidth: ds.maxWidth, gutter: [px(ds.paddingLeft), px(ds.paddingRight)] }; };
    for (const d of el.querySelectorAll('*')) {
      const dr = d.getBoundingClientRect();
      if (visible(d) && cs(d).maxWidth !== 'none' && dr.width >= r.w * 0.4 && dr.height >= Math.min(r.h * 0.3, 20)) { container = asContainer(d); break; }
    }
    if (!container) el.querySelectorAll('*').forEach((d) => {
      const dr = d.getBoundingClientRect();
      if (!visible(d) || dr.width >= r.w - 2 || dr.width < r.w * 0.4 || dr.height < r.h * 0.3) return;
      if (!container || dr.width > container.w) container = asContainer(d);
    });
    const heads = [];
    el.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]').forEach((h) => {
      if (visible(h) && heads.length < MAX_ITEMS) heads.push({ tag: h.tagName.toLowerCase(), text: clip(h.innerText), ...typo(cs(h)), rect: rect(h) });
    });
    const texts = [], seen = new Set();
    el.querySelectorAll('p, li, span, small, blockquote, figcaption, label').forEach((p) => {
      if (texts.length >= MAX_ITEMS || !visible(p) || !ownText(p) || p.closest('a,button,h1,h2,h3,h4,h5,h6')) return;
      const t = typo(cs(p)), key = `${t.family}|${t.size}|${t.weight}|${t.color}`;
      if (seen.has(key)) return;
      seen.add(key);
      texts.push({ tag: p.tagName.toLowerCase(), text: clip(p.innerText), ...t });
    });
    const buttons = [];
    el.querySelectorAll('a, button, [role=button], input[type=submit]').forEach((b) => {
      if (buttons.length >= MAX_ITEMS || !visible(b)) return;
      const bs = cs(b), bg = hex(bs.backgroundColor), bordered = parseFloat(bs.borderTopWidth) > 0;
      if (!bg && !bordered) return;  // a plain text link, not a button
      buttons.push({ text: clip(b.innerText || b.value || b.getAttribute('aria-label')), ...typo(bs), ...boxOf(bs), rect: rect(b),
                     link: b.href ? (new URL(b.href, location.href).host === location.host ? 'internal' : 'external') : undefined });
    });
    const imgs = [];
    el.querySelectorAll('img, picture source, video, [style*="background-image"]').forEach((m) => {
      if (imgs.length >= MAX_ITEMS || (m.tagName !== 'SOURCE' && !visible(m))) return;
      if (m.tagName === 'IMG') {
        const ms = cs(m), rr = rect(m);
        imgs.push({ kind: 'img', src: m.currentSrc || m.src, alt: m.getAttribute('alt'), natural: { w: m.naturalWidth, h: m.naturalHeight },
                    rendered: { w: rr.w, h: rr.h }, ratio: rr.h ? Math.round((rr.w / rr.h) * 100) / 100 : null, fit: ms.objectFit,
                    lazy: m.loading === 'lazy' });
      } else if (m.tagName === 'VIDEO') {
        const rr = rect(m);
        imgs.push({ kind: 'video', src: m.currentSrc || m.src, rendered: { w: rr.w, h: rr.h }, autoplay: m.autoplay, muted: m.muted });
      } else if (m.tagName !== 'SOURCE') {
        const url = (cs(m).backgroundImage.match(/url\("?([^")]+)/) || [])[1];
        if (url) { const rr = rect(m); imgs.push({ kind: 'background', src: url, rendered: { w: rr.w, h: rr.h }, size: cs(m).backgroundSize }); }
      }
    });
    return {
      index: i, hint: hintOf(el, i, s, heads, imgs), tag: el.tagName.toLowerCase(),
      id: el.id || undefined, classes: (typeof el.className === 'string' ? el.className : '').split(/\s+/).filter(Boolean).slice(0, 4),
      rect: r, box: boxOf(s), container, headings: heads, texts, buttons, media: imgs, repeated: repeated(el),
      icons: el.querySelectorAll('svg').length, forms: el.querySelectorAll('input:not([type=hidden]), select, textarea').length,
      sticky: ['sticky', 'fixed'].includes(s.position) ? s.position : undefined,
    };
  });

  // ---------- page-wide: palette, type scale, spacing
  const tally = (m, k, n = 1) => { if (k != null && k !== '') m.set(k, (m.get(k) || 0) + n); };
  const colors = { text: new Map(), background: new Map(), border: new Map() }, sizes = new Map(), spaces = new Map();
  let walked = 0;
  for (const el of document.body.querySelectorAll('*')) {
    if (walked++ > 6000) break;
    if (!visible(el)) continue;
    const s = cs(el);
    if (ownText(el)) { tally(colors.text, hex(s.color)); tally(sizes, px(s.fontSize)); }
    tally(colors.background, hex(s.backgroundColor));
    if (parseFloat(s.borderTopWidth) > 0) tally(colors.border, hex(s.borderTopColor));
    [s.paddingTop, s.paddingBottom, s.rowGap, s.columnGap].forEach((v) => { const n = px(v); if (n >= 4) tally(spaces, n); });
  }
  const top = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([value, count]) => ({ value, count }));

  // ---------- fonts and where they come from (licensing is the dev's to check)
  const fontSources = new Set();
  try {
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch (e) { if (sheet.href) fontSources.add(new URL(sheet.href).host + ' (stylesheet, not readable)'); continue; }
      for (const r of rules || []) if (r.type === 5) { const m = (r.cssText.match(/url\("?([^")]+)/) || [])[1]; if (m) fontSources.add(new URL(m, sheet.href || location.href).host); }
    }
  } catch (e) {}
  const families = new Set();
  document.fonts.forEach((f) => { if (f.status === 'loaded') families.add(f.family.replace(/["']/g, '')); });

  // ---------- technology hints (informative only)
  const has = (sel) => !!document.querySelector(sel);
  const gen = (document.querySelector('meta[name=generator]') || {}).content || '';
  const tech = [
    window.Shopify && 'shopify', has('[data-wf-site]') && 'webflow', /wordpress/i.test(gen) || has('link[href*="wp-content"]') ? 'wordpress' : null,
    window.__NEXT_DATA__ && 'next.js', window.__NUXT__ && 'nuxt', has('[data-reactroot], #__next, #root') && 'react',
    /wix/i.test(gen) && 'wix', /squarespace/i.test(gen) && 'squarespace', window.Webflow && 'webflow',
    has('script[src*="tailwind"], [class*="md:"]') && 'tailwind',
  ].filter(Boolean);

  return {
    url: location.href, title: document.title, lang: document.documentElement.lang || undefined,
    viewport: { w: VW, h: VH }, pageHeight: Math.round(document.documentElement.scrollHeight),
    generator: gen || undefined, tech: [...new Set(tech)],
    body: { ...typo(cs(document.body)), background: hex(cs(document.body).backgroundColor) },
    fonts: { loaded: [...families].slice(0, 12), servedFrom: [...fontSources].slice(0, 8) },
    palette: { text: top(colors.text, 10), background: top(colors.background, 10), border: top(colors.border, 6) },
    typeScale: top(sizes, 12).sort((a, b) => b.value - a.value),
    spacing: top(spaces, 12).sort((a, b) => a.value - b.value),
    sections,
  };
}
