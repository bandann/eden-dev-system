# Heros — revelados, parallax, video

## La regla del hero: el LCP no espera a la animación

El titular o la imagen principal **se pintan visibles en el primer cuadro**. Animaciones posibles sin
retrasar el LCP:

- Animar el **titular desde un estado visible** solo con `transform` (p. ej. `translateY(12px)` → 0),
  sin tocar su `opacity`: un elemento transparente no cuenta como pintado y el LCP se retrasa.
- Animar los **secundarios**: subtítulo, botones, decoraciones, un degradado.
- Revelado con `clip-path` sobre una **copia decorativa** o un fondo, no sobre el elemento LCP.
- La imagen del hero: `fetchpriority="high"`, sin `loading="lazy"`, tamaño reservado; el zoom lento
  (`transform: scale(1.06)` → 1) arranca cuando ya pintó.

## Revelado del titular por línea (escalón 1–3)

Envolver cada línea en un contenedor con `overflow: hidden` y animar la línea interior con
`transform: translateY(100%)` → 0, escalonado. Cortar en líneas en el **markup** (o con un split
accesible, ver `patterns-text.md`), no midiendo en JS al cargar. Con reduced-motion: sin desplazamiento.
**Si el titular es el elemento LCP, este revelado no**: el texto empieza recortado y el LCP espera. Para
el LCP, desplazamiento corto desde un estado visible; el revelado por línea, para titulares de secciones
más abajo.

## Parallax liviano

- Escalón 2: `animation-timeline: scroll()` con `transform: translateY()` en una capa decorativa, dentro
  de `@supports` y `prefers-reduced-motion: no-preference`.
- Nada de mover la imagen LCP ni de escuchar `scroll`. En móvil, parallax reducido o ninguno.

## Video de fondo

- `<video autoplay muted loop playsinline poster="…" preload="metadata">` con el póster como imagen LCP
  y tamaño reservado. Fuentes en formato moderno y liviano.
- **Pausa visible** (WCAG 2.2.2) y pausa automática con reduced-motion (se muestra el póster) y fuera de
  pantalla (`IntersectionObserver`).
- El texto sobre el video con contraste AA en cualquier cuadro (capa de color o sombra).
