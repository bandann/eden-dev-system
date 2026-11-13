---
name: test-visual
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:test-visual` o lo pide de forma explícita e inequívoca, o encadenado desde
  `create-new-section` / `section-mod` / `turnoff-task` como puerta de entrega. NO lo actives porque
  haya un Figma o porque el trabajo parezca listo: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: TDD visual. Deriva del Figma un baseline de valores esperados ANTES de
  implementar, lo versiona, y corre el test contra el render real con Playwright: nodo por nodo y
  breakpoint por breakpoint verifica colores (y que vengan del token), familia/tamaño/peso/line-height/
  letter-spacing, paddings, margins, gaps, dimensiones, animaciones y reduced-motion. Reporta rojo/verde
  por propiedad con el delta exacto.
argument-hint: "<sección> [| baseline | run | update] [| url del render]"
disable-model-invocation: true
---

## Test Visual — TDD de fidelidad

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre.

Argumento recibido: `$ARGUMENTS`

El diseño es el criterio de aceptación, y se congela **antes** de implementar. Después, el test dice
rojo o verde — no "se ve parecido".

Disciplina completa en `rules/eden-testing-rules.md`.

> **Idioma:** al dev, en español. El baseline y los archivos de test, en inglés.

**Dependencias:** Figma Console (para derivar el baseline) y **Playwright** (para medir el render). En
`/eden:w2shopify` el baseline se deriva de la **medición del sitio de origen** (`.claude/context/w2s/`):
los mismos asertos, con `desde sitio {url} · {ancho}` en lugar del nodo de Figma. Si
Playwright no responde, **dilo y detente** — no sustituyas la medición por una lectura del CSS: el CSS
escrito y el computado no son lo mismo.

### Cómo se reparte con `attention-detail`

| | `test-visual` | `attention-detail` |
|---|---|---|
| **Qué es** | La suite repetible: baseline versionado, rojo/verde | La auditoría exhaustiva y exploratoria |
| **Cuándo** | Antes de implementar (baseline) y en cada cambio | Cuando algo no cuadra, o en el pase final |
| **Sale con** | Lista de asertos que pasan y fallan | Informe con deltas, imágenes exportadas, hallazgos |

Uno es el semáforo; el otro, el microscopio. No se sustituyen.

---

### Modo `baseline` — congelar el diseño (🔴 primero)

**Antes de escribir código.** Deriva del Figma los valores esperados y escríbelos.

1. **Delega la extracción al `design-extractor` (rol)** (obligatorio — `rules/eden-context-rules.md`), por
   cada breakpoint que aplique. El agente lo resuelve el roster del stack (`teams/{stack}/roster.md`; sin
   roster, `teams/_generic/roster.md`).
2. Convierte el Design Spec en **asertos**: cada propiedad medible, un aserto.
3. Escribe el baseline en `tests/visual/{section}.baseline.json` (o donde el proyecto ponga sus tests) y
   **versiónalo**: es el contrato del diseño y debe revisarse en el PR como el código.

Formato y qué se asevera en cada grupo: `references/baseline-format.md`.

4. **Corre el test y comprueba que falla.** Si pasa antes de implementar, el test no está midiendo nada
   — revísalo antes de seguir.

```
🔴 BASELINE CREADO — {sección}
   {n} asertos · {n} breakpoints · desde Figma {node-id} v{versión}
   Corriendo contra el estado actual: {n} fallan, {n} pasan
   → Correcto: debe fallar antes de implementar.
```

---

### Modo `run` — el test (🟢 después)

Por cada breakpoint del baseline:

1. `browser_resize` al **ancho exacto** del frame.
2. `browser_navigate` al render y **espera de verdad**: `document.fonts.ready` y las imágenes
   completas. Medir antes da tipografía y alturas falsas.
3. `browser_evaluate` para leer `getBoundingClientRect()` y `getComputedStyle()` de cada nodo del
   baseline.
4. Compara aserto por aserto.

**Los siete grupos que se verifican** (detalle en `references/what-to-assert.md`):

| Grupo | Asertos |
|---|---|
| 🎨 **Color** | Texto, fondo, borde, icono — **y que el valor venga de una custom property**, no hardcodeado |
| 🔤 **Tipografía** | `font-family`, `font-size`, `font-weight`, `line-height`, `letter-spacing`, `text-transform` |
| 📐 **Espaciado** | `padding` ×4, `margin` ×4, `gap` |
| 📏 **Dimensiones** | Ancho, alto, `max-width` del contenedor, `aspect-ratio` |
| 🎬 **Animación** | Propiedad, duración, easing, delay — y que con `prefers-reduced-motion` se desactive |
| 📱 **Responsive** | Todo lo anterior en **cada** breakpoint, y que el reflujo coincida con el diseño |
| 🖼️ **Imágenes** | Presencia, tamaño renderizado, aspect-ratio, `object-fit`, `alt` |

**El aserto de token es el que más se salta y el que más importa a largo plazo:** un `#1a1a1a` correcto
en pantalla pero hardcodeado **falla**, porque no se actualizará cuando cambie el esquema de color.

```
🟢 TEST VISUAL — {sección}

📱 MOBILE @375   {n}/{n} ✅
🖥️ DESKTOP @1440 {n}/{n}

❌ FALLA · {nodo} · font-size
   esperado 18px (baseline, Figma 12:118)
   actual   16px
   dónde    sections/hero.liquid:42

❌ FALLA · {nodo} · color
   esperado var(--color-text-primary)
   actual   #1a1a1a  ← hardcodeado
   dónde    sections/hero.liquid:58

Resultado: {n} pasan · {n} fallan · {n} no se pudieron medir
```

Lo que **no se pudo medir** se reporta como tal. Nunca se cuenta como verde.

---

### Modo `update` — cuando el diseño cambió

Solo cuando **el Figma cambió**, no cuando el test molesta.

- Se re-deriva el baseline **desde Figma**, nunca se edita a mano para que pase.
- Se muestra el **diff del baseline** (qué valores cambiaron) y se espera aprobación.
- Se anota la versión del Figma de la que salió.

> Ajustar el baseline para que pase el test es la forma más rápida de que "pixel-perfect" deje de
> significar nada.

---

### El ciclo

```
baseline (🔴 falla)  →  implementar  →  run (🟢 pasa)  →  refactor  →  run
```

En `create-new-section` y `section-mod` el baseline se crea en el paso de diseño y el `run` es parte de
la verificación. En `turnoff-task` es **puerta**: sin verde, no se entrega — o se declara exactamente
qué quedó fuera y por qué.
