# Animación web — Eden (motion)

Reglas para crear, modificar y optimizar animaciones en cualquier stack (Shopify, WordPress, React,
vistas PHP). Las aplica el equipo de animación (`teams/motion/roster.md`, líder `/eden:motion`) y
cualquier skill que toque una animación. Se suman a `eden-quality-rules.md` y `eden-code-style-rules.md`;
el patrón del proyecto manda sobre la preferencia de quien escribe.

Una animación es **una decisión de producto con un coste**: tiempo de CPU, peso de JS, accesibilidad y
Core Web Vitals. Se justifica qué comunica (estado, jerarquía, continuidad) y se mide lo que cuesta.

---

## 1. La escalera de técnicas — la más liviana que funcione

| Escalón | Técnica | Cuándo |
|---|---|---|
| 1 | **CSS**: `transition`, `@keyframes`, `@starting-style` + `transition-behavior: allow-discrete` (entradas y `display`/popover), `linear()` para easings con rebote | Estados (hover, foco, abierto/cerrado), entradas, loops decorativos |
| 2 | **CSS ligado al scroll**: `animation-timeline: scroll()` / `view()` con `animation-range`; **View Transitions** (`document.startViewTransition()` en la misma página, `@view-transition { navigation: auto }` entre páginas) | Apariciones al hacer scroll, barras de progreso, parallax liviano, transiciones de estado o de página |
| 3 | **Web Animations API** (`el.animate()`) e `IntersectionObserver` | Secuencias controladas desde JS, interrumpibles, con promesas (`finished`); disparar al entrar en pantalla |
| 4 | **Librería, con el sí del dev** (se declara y se agrega como dependencia) | Línea de tiempo compleja, scroll con anclaje y scrub, texto dividido con muchas piezas, física |

Cada propuesta dice **en qué escalón se quedó y por qué no bastó el anterior** (como el reuse-first de
`eden-component-strategy-rules.md`). Lo del escalón 2 que no esté en todos los navegadores objetivo va
con `@supports` (o detección en JS) y un estado final correcto sin animación: **sin soporte, se ve bien
y quieto**, nunca roto ni invisible.

### Librerías del escalón 4 (y su licencia — se verifica al agregarla)

| Librería | Para qué | Licencia |
|---|---|---|
| **GSAP** (+ ScrollTrigger, SplitText, Flip) | Líneas de tiempo, scroll con scrub y pin, texto dividido | Licencia propia gratuita de GSAP, **no MIT**: se revisa que el uso del proyecto la cumpla |
| **Motion** (motion.dev, antes Framer Motion) | React y vanilla; animaciones de layout | MIT |
| **Lottie** (`lottie-web` / dotLottie) | Animaciones de diseño exportadas de After Effects | MIT |
| **Embla Carousel** / **Swiper** | Sliders con arrastre cuando `scroll-snap` no basta | MIT |
| **Three.js** | 3D, solo si el diseño lo exige | MIT |

Si el proyecto **ya** usa una (p. ej. GSAP en el tema), se usa esa: no se mete una segunda que haga lo
mismo. Se importa solo lo que se usa (plugins, módulos) y se carga **diferido** (`defer`, import dinámico
o al entrar en pantalla), nunca bloqueando el render.

---

## 2. Rendimiento — requisitos de construcción

1. **Se animan propiedades que compone la GPU**: `transform` y `opacity` siempre; `filter` y
   `clip-path` con medida (pueden repintar). **Nunca** `top`/`left`/`right`/`bottom`, `width`/`height`,
   `margin`/`padding`, `font-size` ni **`transition: all`**: obligan a recalcular el layout en cada cuadro.
   Para "crecer" se usa `transform: scale()` o, en acordeones, `grid-template-rows: 0fr → 1fr` o la
   técnica medida de la Web Animations API.
2. **`will-change` solo mientras anima**, en el elemento que anima, y se quita al terminar. Nunca en
   reglas globales ni en decenas de elementos: cada capa cuesta memoria.
3. **Nada de escuchar `scroll` para animar**: `animation-timeline` o `IntersectionObserver`. Si un
   listener de scroll o `resize` es inevitable: `{ passive: true }`, trabajo dentro de
   `requestAnimationFrame` y nada de lecturas de layout (`getBoundingClientRect`, `offsetTop`) mezcladas
   con escrituras en el mismo cuadro (**layout thrashing**: primero se lee todo, después se escribe).
4. **Core Web Vitals intactos**:
   - **LCP**: el elemento LCP del hero (imagen o titular) **se ve en el primer pintado**. Nada de
     `opacity: 0` ni de esperar al JS para mostrarlo; si se anima, que sea con `transform` desde un estado
     visible, o se animan los elementos secundarios.
   - **CLS = 0** por animaciones: el espacio se reserva (`aspect-ratio`, `min-height`) y las entradas usan
     `transform`, nunca cambian el flujo.
   - **INP**: un clic o tap responde en el siguiente cuadro; la animación arranca después, no al revés.
     Nada de trabajo pesado en el handler del input.
5. **Lo que no se ve, no anima**: loops y carruseles se pausan fuera de pantalla
   (`IntersectionObserver`) y con la pestaña oculta (`visibilitychange`); `content-visibility: auto` en
   secciones largas fuera de pantalla cuando no rompe el diseño.
6. **Presupuesto**: 60 fps en un móvil de gama media; ninguna tarea larga (> 50 ms) causada por una
   animación; JS de animación de la página ≤ 30 KB comprimido salvo que el diseño justifique más (y se dice).
7. **Limpieza**: todo listener, observer, `requestAnimationFrame` o instancia de librería se crea en
   `connectedCallback` (o `useEffect`) y se destruye en `disconnectedCallback` (o el cleanup). En Shopify,
   el editor de temas recarga secciones: la animación sobrevive a `shopify:section:load` / `unload` sin
   duplicarse.

---

## 3. Accesibilidad — no negociable

- **`prefers-reduced-motion: reduce`** en **toda** animación: se quita el movimiento (desplazamientos,
  parallax, zoom, autoplay) y queda, como mucho, un fundido corto. En JS: `matchMedia('(prefers-reduced-motion: reduce)')`
  y escuchar su cambio. El estado final es el mismo con y sin movimiento.
- **Nada parpadea más de 3 veces por segundo** (WCAG 2.3.1).
- **Todo lo que se mueve solo más de 5 s** (sliders con autoplay, marquesinas, fondos animados) tiene
  **pausa visible y por teclado** (WCAG 2.2.2), y se pausa con foco o hover dentro.
- **Menús y diálogos**: foco gestionado (al abrir va dentro, al cerrar vuelve al disparador), `Esc` cierra,
  `aria-expanded` refleja el estado, el foco no se queda atrapado en algo invisible.
- El **texto dividido** (por letra o palabra) conserva la lectura: el texto completo queda en
  `aria-label` del contenedor o los fragmentos llevan `aria-hidden` con un duplicado accesible.
- Una animación nunca es la única forma de comunicar algo (estado, error, éxito).

---

## 4. Tokens de movimiento

Duraciones y curvas son **tokens del proyecto**, como los colores: nada de `0.3s` ni
`cubic-bezier(...)` sueltos.

```css
--{prefix}-duration-fast: 150ms;     /* hover, foco, toggles */
--{prefix}-duration-base: 300ms;     /* abrir/cerrar, entradas */
--{prefix}-duration-slow: 600ms;     /* hero, secciones */
--{prefix}-ease-out: cubic-bezier(.2, .8, .2, 1);
--{prefix}-ease-in-out: cubic-bezier(.65, 0, .35, 1);
```

Si el tema ya tiene tokens de movimiento (Horizon: `--animation-speed`, `--animation-easing`…), se usan
esos. **JS que lee un token de tiempo** parsea la unidad: el CSS minificado puede convertir `500ms` en
`.5s` (`ms` → número; `s` → ×1000; vacío → valor por defecto).

---

## 5. Cómo se entrega una animación

- El plan de la unidad dice: **qué comunica**, el **escalón** y por qué, las **propiedades** que anima,
  duración/curva (tokens), el comportamiento con **reduced-motion**, y el **impacto** esperado (JS
  añadido, capas, LCP/CLS).
- El test visual (`eden-testing-rules.md`) cubre propiedad, duración, easing y delay, el estado final, y
  el estado con `prefers-reduced-motion`.
- Optimizar una animación existente es **un cambio con antes y después medido**: lo que costaba (fps,
  tareas largas, layout, peso) y lo que cuesta ahora. Sin medida, es una opinión.
- Herramientas: `scripts/eden_motion.py lint` (análisis estático, `--changed {base}` para un diff),
  `eden_motion.py measure` (navegador headless con scroll, hover, clic o tecla; `--mobile`, `--throttle 4`,
  `--reduced`) y `eden_motion.py compare` (antes → después). Las usa `/eden:motion-audit`.

## Nunca

- `transition: all`, animar propiedades de layout, `will-change` permanente o global.
- Animar con `setInterval`/`setTimeout` lo que puede hacer CSS, la Web Animations API o `requestAnimationFrame`.
- Ocultar el contenido hasta que cargue el JS (`opacity: 0` en el HTML esperando una librería).
- Una segunda librería de animación cuando el proyecto ya tiene una, o una librería para lo que hace CSS.
- Autoplay sin pausa, parpadeo, o animación sin salida para `prefers-reduced-motion`.
