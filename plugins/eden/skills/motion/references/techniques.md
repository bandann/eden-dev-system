# Técnicas — recetas base (escalones 1 a 4)

Los nombres de clase y tokens usan `{prefix}` del proyecto. Adapta todo al patrón del proyecto.

## Escalón 1 — CSS

**Entrada de un elemento que aparece (`display`/popover) sin JS:**

```css
.{prefix}-panel {
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity var(--{prefix}-duration-base) var(--{prefix}-ease-out),
    transform var(--{prefix}-duration-base) var(--{prefix}-ease-out),
    display var(--{prefix}-duration-base) allow-discrete,
    overlay var(--{prefix}-duration-base) allow-discrete;
}
.{prefix}-panel:not(:popover-open) { opacity: 0; transform: translateY(-8px); }
@starting-style {
  .{prefix}-panel:popover-open { opacity: 0; transform: translateY(-8px); }
}
@media (prefers-reduced-motion: reduce) {
  .{prefix}-panel { transition: opacity var(--{prefix}-duration-fast) linear; transform: none; }
}
```

**Acordeón sin animar `height`:** grid de `0fr` a `1fr` (la fila interior con `overflow: hidden`).

```css
.{prefix}-acc__body { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--{prefix}-duration-base) var(--{prefix}-ease-out); }
.{prefix}-acc[open] .{prefix}-acc__body { grid-template-rows: 1fr; }
.{prefix}-acc__inner { overflow: hidden; }
@media (prefers-reduced-motion: reduce) { .{prefix}-acc__body { transition: none; } }
```

**Rebote o resorte sin JS:** `linear()` con puntos (generado una vez, guardado como token).

## Escalón 2 — CSS ligado al scroll y View Transitions

**Aparición al entrar en pantalla**, solo donde hay soporte; sin soporte el elemento ya está visible:

```css
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .{prefix}-reveal {
      animation: {prefix}-reveal linear both;
      animation-timeline: view();
      animation-range: entry 10% cover 30%;
    }
  }
}
@keyframes {prefix}-reveal { from { opacity: 0; transform: translateY(24px); } }
```

**Barra de progreso de lectura:** `animation-timeline: scroll(root)` sobre `transform: scaleX()`.

**Transición entre estados (misma página):**

```js
function swap(update) {
  if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) return update();
  document.startViewTransition(update);
}
```

Entre páginas (MPA): `@view-transition { navigation: auto; }` y `view-transition-name` único por elemento
compartido; dentro de `@media (prefers-reduced-motion: no-preference)`.

## Escalón 3 — Web Animations API + IntersectionObserver

```js
class RevealOnView extends HTMLElement {
  connectedCallback() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    this.io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      this.io.disconnect();
      this.style.willChange = 'transform, opacity';
      const a = this.animate(
        [{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'none' }],
        { duration: readMs('--{prefix}-duration-slow', 600), easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'both' });
      a.finished.then(() => { this.style.willChange = ''; });
    }, { rootMargin: '0px 0px -10% 0px' });
    this.io.observe(this);
  }
  disconnectedCallback() { this.io?.disconnect(); }
}
customElements.define('{prefix}-reveal', RevealOnView);

// Tokens de tiempo: el CSS minificado puede dar ".5s" en vez de "500ms".
function readMs(prop, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(prop).trim();
  if (!v) return fallback;
  return v.endsWith('ms') ? parseFloat(v) : parseFloat(v) * 1000;
}
```

## Escalón 4 — GSAP (si el plan lo aprobó)

```js
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
gsap.registerPlugin(ScrollTrigger);

class PinnedStory extends HTMLElement {
  connectedCallback() {
    this.mm = gsap.matchMedia();
    this.mm.add('(prefers-reduced-motion: no-preference) and (min-width: 990px)', () => {
      const tl = gsap.timeline({ scrollTrigger: { trigger: this, start: 'top top', end: '+=150%', scrub: true, pin: true } });
      tl.from(this.querySelectorAll('[data-step]'), { yPercent: 20, opacity: 0, stagger: 0.2 });
      // matchMedia revierte todo (incluido el ScrollTrigger) cuando la condición deja de cumplirse
    });
  }
  disconnectedCallback() { this.mm?.revert(); }
}
```

- Solo los plugins que se usan; carga diferida o `import()` al entrar en pantalla.
- `ScrollTrigger.refresh()` después de cambios de layout (imágenes cargadas, fuentes), no en cada scroll.
- En Shopify, revertir en `shopify:section:unload` para no duplicar en el editor.
