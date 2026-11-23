# Sliders y carruseles

## Base: `scroll-snap` nativo (escalón 1)

```css
.{prefix}-slider { display: grid; grid-auto-flow: column; grid-auto-columns: var(--{prefix}-slide-w, 85%);
  gap: var(--{prefix}-space-m); overflow-x: auto; overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory; scroll-padding-inline: var(--{prefix}-gutter); scrollbar-width: none; }
.{prefix}-slider > * { scroll-snap-align: start; }
@media (prefers-reduced-motion: no-preference) { .{prefix}-slider { scroll-behavior: smooth; } }
```

- Arrastre, inercia y táctil los da el navegador; los botones llaman a `scrollBy({ left: ancho })`.
- Diapositiva activa: `IntersectionObserver` con `root` = el slider (no `scroll`), para puntos y
  `aria-current`.
- Imágenes: la primera visible sin `lazy`; el resto `loading="lazy"`; todas con `width`/`height`.
- Accesibilidad: región con `aria-roledescription="carousel"` y `aria-label`; cada diapositiva
  `role="group"` con "n de total"; botones con nombre.

## Autoplay (si el diseño lo pide)

- **Botón de pausa visible**, pausa con hover y con foco dentro, pausa fuera de pantalla y con
  `visibilitychange`, y **sin autoplay con `prefers-reduced-motion`**. Intervalo ≥ 5 s.
- Timer con `setTimeout` reprogramado al terminar cada paso (no `setInterval` que se acumula).

## Efectos sobre el slide (parallax interno, escala, opacidad)

Escalón 2 con `animation-timeline: view(inline)` sobre cada diapositiva dentro del slider: sin JS por
cuadro. Sin soporte, el slider funciona igual y quieto.

## Cuándo una librería (escalón 4)

Embla (liviana, sin estilos) o Swiper si hace falta: bucle infinito real, sincronizar dos sliders,
arrastre con física específica o efectos 3D. Si el tema ya trae un slider (Horizon trae el suyo), **se
usa ese** antes que cualquier librería.
