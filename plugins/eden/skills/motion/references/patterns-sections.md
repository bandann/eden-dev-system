# Secciones — aparición, escalonado, sticky, contadores

## Aparición al entrar en pantalla

- Primera opción: escalón 2 (`animation-timeline: view()`), ver `techniques.md`. Segunda: el
  `RevealOnView` con `IntersectionObserver` + Web Animations API.
- **Una sola clase o componente de reveal para todo el sitio**, con atributos para la variante
  (`data-reveal="up|fade|scale"`), en vez de una animación por sección.
- **Nunca** `opacity: 0` en el HTML esperando al JS: el estado oculto lo pone el CSS solo cuando la
  animación va a correr (dentro de `@supports`/`no-preference` o con una clase que añade el JS antes de
  pintar y que no se aplica al contenido above-the-fold).
- Lo que ya está en pantalla al cargar no se anima con reveal (no esconder el primer pantallazo).

## Escalonado de tarjetas y grillas

`--i` por elemento y `animation-delay: calc(var(--i) * 60ms)` con un tope (los primeros 6–8; el resto
sin retraso). Con reduced-motion, sin retraso ni desplazamiento.

## Sticky / pin

- `position: sticky` primero (cero JS). El contenido que cambia mientras está fijo, con
  `animation-timeline: view()` de cada paso.
- Pin con scrub de GSAP ScrollTrigger solo si el diseño necesita una línea de tiempo atada al scroll que
  CSS no logra; `gsap.matchMedia()` lo apaga en móvil y con reduced-motion.

## Contadores y magnitudes

Web Animations no anima texto: contador con `requestAnimationFrame` que se dispara una vez al entrar en
pantalla, con `font-variant-numeric: tabular-nums` (sin saltos de ancho) y el **número final en el HTML**
(lectores de pantalla y sin JS). Con reduced-motion, el número final directo.

## Secciones largas

`content-visibility: auto` y `contain-intrinsic-size` en secciones fuera de pantalla cuando no rompe el
diseño (anclas, búsqueda en página): menos trabajo de render al cargar.
