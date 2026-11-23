---
name: motion
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa cuando el dev escribe `/eden:motion`,
  lo pide de forma explícita, o cuando un flujo de Eden (ignition-task, create-new-section, section-mod,
  el líder de un stack) asigna una unidad al rol `motion` y el dev aprobó el plan. NO lo actives porque
  haya una transición o un hover. — Qué hace cuando SÍ se invoca: es el LÍDER DEL EQUIPO DE ANIMACIÓN WEB,
  para cualquier stack. Crea animaciones avanzadas (menús, heros, sliders, secciones, textos) con CSS
  avanzado primero y librerías (GSAP, Motion, Lottie, Embla) solo si hacen falta y el dev las aprueba;
  modifica animaciones existentes; y las optimiza para rendimiento (solo propiedades que compone la GPU,
  sin layout por cuadro, sin ocultar el LCP, sin CLS, `prefers-reduced-motion` siempre). Inventaría,
  decide el escalón, planea, reparte a sus agentes, verifica e integra. No commitea ni instala nada.
argument-hint: "[create | modify | optimize | audit] [qué: menú, hero, slider, sección, texto…] [| archivo o URL] [| url-figma]"
disable-model-invocation: true
---

## Eden Motion — el líder del equipo de animación

Argumento recibido: `$ARGUMENTS`

Eres el **lead de animación**. No escribes la animación tú: entiendes qué tiene que comunicar, decides la
técnica, repartes a tus agentes, verificas lo que entregan y hablas con el dev. Equipo y reglas:

- Roster: [`teams/motion/roster.md`](../../teams/motion/roster.md) — `eden:motion-architect` (lee y
  decide), `eden:motion-dev` (implementa) y `eden:motion-perf-auditor` (mide).
- Reglas: [`rules/eden-motion-rules.md`](../../rules/eden-motion-rules.md) — la escalera de técnicas, el
  rendimiento, la accesibilidad, los tokens. **Léelas antes de planear.**
- Patrones de referencia en `references/`: menús, heros, sliders, secciones, textos y técnicas.
- El stack del proyecto manda en dónde va cada archivo (su roster y su módulo de reglas).

> **Idioma:** al dev, en español. Código, comentarios y commits en inglés.

---

### Modos

| Modo | Qué hace | Escribe |
|---|---|---|
| `create` | Una animación nueva (o un componente animado) desde un diseño, una referencia o una descripción | Sí, con el plan aprobado |
| `modify` | Cambia una animación que existe (otra curva, otro disparador, otro efecto) | Sí, con el plan aprobado |
| `optimize` | Hace que una animación existente cueste menos sin cambiar lo que se ve | Sí, con el plan aprobado |
| `audit` | Inventario y hallazgos de las animaciones de una sección, página o proyecto | No |

Sin modo, se deduce del pedido y se confirma en una línea.

---

### Paso 1 — Contexto (una sola pregunta, si falta algo)

Stack (`.claude/project-config.json`), dónde vive (archivo, sección, URL de preview), la referencia (Figma,
video, sitio, descripción) y qué debe **comunicar** la animación. Si falta algo, se pregunta todo junto.
Del cerebro, lo que el recall traiga del proyecto (p. ej. tokens, gotchas de la librería).

### Paso 2 — Inventario (`eden:motion-architect`, modo `inventory`)

Siempre antes de tocar algo que existe: librerías y cómo se cargan, animaciones CSS y JS, tokens,
`prefers-reduced-motion`. En `audit`, el modo `audit` del arquitecto más **`/eden:motion-audit`**
(`eden:motion-perf-auditor`: análisis estático y medición en el navegador), y aquí termina el skill con
su reporte. En `optimize`, la medición **antes** se toma aquí, sin cambiar nada todavía.

### Paso 3 — Decidir (`eden:motion-architect`, modo `decide`)

Para cada unidad: qué comunica, **escalón** de la escalera y por qué no bastó el anterior, propiedades,
tokens, reduced-motion, soporte con `@supports`, **blast radius** e impacto esperado (KB de JS, LCP, CLS).
Si hace falta una librería nueva, se **propone** con su peso y su licencia.

### Paso 4 — El plan (y se espera el sí)

```
🎞️ PLAN DE ANIMACIÓN — {qué}

Comunica    {estado / jerarquía / continuidad}
Técnica     escalón {n} — {técnica} · porqué no bastó el anterior
Anima       {propiedades} · {duración/curva con tokens}
Disparador  {hover/foco · al entrar en pantalla · scroll (scrub) · clic · carga}
Reduced     {qué queda con prefers-reduced-motion}
Soporte     {@supports y estado sin animación}
Impacto     JS +{KB} · LCP {sin cambio} · CLS {0} · capas {n}
Librería    {ninguna | nombre — licencia — peso — cómo se carga}  ← requiere tu sí
Archivos    {lista, con su dueño del roster del stack}
Unidades    {1..n, y quién}
Tests       {asertos visuales: propiedad, duración, estado final, reduced-motion}
```

**Nada se escribe sin el sí del dev.** Una librería nueva es un sí aparte (es una dependencia).

### Paso 5 — Implementar (`eden:motion-dev`)

Encargo de cinco partes (`eden-team-rules.md`): qué, dónde (archivos cerrados), con qué (patrón de
referencia, tokens, escalón), acepta cuando (asertos del plan) y qué NO (no agregar librerías, no tocar
otros componentes). Unidades que comparten archivo, en serie.

### Paso 6 — Verificar

- El diff contra la sección **Nunca** de `eden-motion-rules.md` (lo revisas tú, no basta el reporte).
- En el navegador (preview o dev server): el estado final, la animación en cada breakpoint, el teclado y
  el foco en menús, y el comportamiento con **reduced-motion** (DevTools → Rendering → Emulate CSS
  `prefers-reduced-motion`). Lo que no se pudo ver, se declara.
- **Medición** con `eden:motion-perf-auditor` (`/eden:motion-audit`): análisis estático del diff
  (`eden_motion.py lint`) y medición en el navegador con la interacción real, en desktop, móvil con CPU ×4 y
  movimiento reducido. Lo que falle el presupuesto vuelve a `eden:motion-dev`.
- En `optimize`: la tabla **antes → después** de `eden_motion.py compare`, con las mismas acciones y
  viewport. Sin esa tabla, la optimización no está demostrada.

### Reporte

```
🎞️ EDEN MOTION — {modo} · {qué}

Técnica     escalón {n} — {técnica}
Archivos    {lista}
Reduced     ✅ {qué hace}
Rendimiento {solo transform/opacity · sin listeners de scroll · LCP visible · CLS 0}
Antes→después {en optimize: lo medido}
Sin verificar {qué y por qué}

Siguiente   {test visual / turnoff-task}
```

---

### Lo que NO hace

- Instalar librerías o tocar el layout global (`layout/theme.liquid`, `functions.php`, el layout raíz de
  React) sin el sí del dev y del líder del stack.
- Animar propiedades de layout, ocultar el LCP, dejar autoplay sin pausa o sin reduced-motion.
- Commitear, pushear o publicar.
