---
name: figma-expert
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:figma-expert` o lo pide de forma explícita e inequívoca. NO lo actives porque haya una
  URL de Figma en el chat, porque el ticket sea visual o porque se hable de implementar un diseño: si
  no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: implementa un diseño de Figma
  en código con fidelidad 1:1, de punta a punta, bajo el protocolo pixel-perfect completo. Extrae el
  diseño nodo por nodo con Figma Console (dimensiones, tipografía, espaciados, colores, sombras,
  imágenes, estados y comportamiento responsive), congela un Design Spec medido que se convierte en el
  contrato de implementación, baja los assets reales, implementa siguiendo los patrones y tokens del
  proyecto, y **valida el render real con Playwright** midiendo bounding boxes y estilos computados
  contra el Figma, en un loop medir→corregir→medir hasta que no queda diferencia o queda declarado
  exactamente cuál falta y por qué. Nada se estima: cada valor tiene su origen medido.
argument-hint: "<url-de-figma o node-id> [| url donde se renderiza] [| sección/página] [| breakpoints]"
disable-model-invocation: true
---

## Figma Expert — el diseño es la especificación, el navegador es la prueba

Argumento recibido: `$ARGUMENTS`

Este skill implementa un diseño de Figma **medido y validado**, no "parecido". Se sostiene sobre tres
frases, y todo lo demás se deriva de ellas:

> **Figma no es inspiración. Figma es especificación.**
> **Playwright no es un preview opcional. Playwright es la validación.**
> **Las medidas no son sugerencias. Son requisitos de implementación.**

El estándar completo del rol —el documento fuente, en inglés— vive en
`references/pixel-perfect-standard.md`. Este SKILL.md es cómo se ejecuta **dentro del kit de Eden**.

> **Idioma:** al dev, en español. El código, los nombres de archivo, los tokens y el Design Spec, en
> inglés (`rules/eden-workflow-rules.md`).

**Modelos:** la extracción del Figma y la medición del navegador las ejecutan agentes (nivel `fast`) con los
roles `design-extractor` y `design-auditor`; la implementación, el `implementer`. Los agentes se resuelven por rol con el roster del stack del proyecto (`teams/{stack}/roster.md`, ver
`rules/eden-team-rules.md`); si el stack no tiene roster, se usa `teams/_generic/roster.md`. La sesión
principal decide el alcance, verifica los números y habla con el dev. Ver
`rules/eden-model-strategy-rules.md`.

---

### Dónde encaja — y con qué NO se pisa

| | Qué hace | Cuándo |
|---|---|---|
| **`/eden:figma-expert`** | **Implementa** un diseño con el protocolo pixel-perfect completo, y lo valida él mismo | Cuando el trabajo es traducir un Figma a código y la fidelidad es el criterio |
| `/eden:create-new-section` | Construye una sección nueva dentro del flujo del kit (ticket, reuse-first, cierre) | Cuando la unidad es "una sección" y el flujo del kit aporta |
| `/eden:section-mod` | Modifica una sección existente sin romper a sus consumidores | Cuando ya existe |
| `/eden:attention-detail` | **Mide** una sección y reporta. No corrige | QA puntual |
| `/eden:qa-pixel-perfect` | Mide **y corrige** una página completa ya construida | Pase final de página |

Si el dev invoca `/eden:figma-expert` sobre algo que ya existe, **no se rehace**: se mide primero, se reporta
la diferencia, y se corrige lo que haga falta — es `section-mod` con el protocolo de este skill.

**Este skill no commitea, no pushea y no abre PRs.** El trabajo queda en la rama; lo cierra
`turnoff-task`.

---

### Precondiciones — se verifican antes de tocar nada

Sin esto, el skill **se detiene y lo dice**. No sustituye una medición por una estimación:

1. **Figma Console conectado.** Es la fuente autorizada del diseño. Sin él no hay extracción; leer una
   captura de pantalla no es medir.
2. **Playwright conectado.** Es la fuente autorizada de lo que el código realmente renderiza. Sin él no
   hay validación — y **el CSS escrito y el CSS computado no son lo mismo**, así que revisar el código
   no reemplaza la medición.
3. **Una URL donde se renderice** lo implementado (preview, staging o local).
4. **Los fundamentos de diseño del proyecto** (`docs/design-system.md`, tokens integrados). Si no
   existen, se propone `/eden:create-fundaments` **antes** de construir: sin tokens, cada tarea vuelve a
   inventar su paleta y su escala.
5. **Los breakpoints reales**, de `.claude/project-config.json` → `breakpoints`, que salen de los frames
   de Figma. **Un ancho inventado invalida todo el informe**: medir con la regla equivocada es peor que
   no medir.

Todo lo que falte se pide **en una sola intervención**, no de a una pregunta por turno.

**Anti-slop.** Aquí siempre hay fuente de diseño (el Figma), así que solo aplica la capa funcional de
`${CLAUDE_PLUGIN_ROOT}/rules/on-demand/eden-antislop-rules.md` (contraste medido, estados, teclado, nada
inventado); la estética no se toca. Si el Figma choca con la capa funcional (un color que no pasa
contraste, cifras de ejemplo), **se reporta al dev** en el reporte final; no se resuelve en silencio.
Línea del plan: `🧹 Anti-slop: funcional · estética no (diseño en Figma)`.

---

### Paso 1 — Extracción del diseño (antes de escribir una línea)

Se delega al `design-extractor` (rol). El detalle de qué extraer y con qué herramientas está en
`references/extraction-protocol.md`. **Caché primero** (`rules/on-demand/eden-design-cache-rules.md`):
si el nodo ya se midió y el archivo no cambió, el spec sale de la caché; si cambió, se re-mide solo ese
nodo y se le dice al dev qué cambió.

Se extrae, **por breakpoint**, nodo por nodo:

- **Página**: dimensiones, contenedor, ancho máximo, fondo, grid, secciones, ritmo vertical.
- **Tipografía** de cada texto: familia, tamaño, peso, line-height, letter-spacing, transform, color,
  alineación, restricciones de ancho.
- **Layout**: ancho, alto, X, Y, padding, margin, gap, alineación, distribución, columnas, comportamiento
  flex.
- **Visual**: fondos, gradientes, bordes, radios, sombras, opacidad, blur, overlays.
- **Media**: dimensiones, aspect-ratio, recorte, punto focal, posición — y la variante de cada
  breakpoint, que casi nunca es la misma imagen.
- **Componentes**: qué es reutilizable, sus variantes y sus estados.

Las **diferencias entre breakpoints son requerimientos**, no errores del diseñador
(`rules/eden-design-rules.md`). Cada una se anota explícitamente.

---

### Paso 2 — Design Spec: el contrato

Lo extraído se congela en un archivo antes de implementar. Es lo que convierte "pixel-perfect" en algo
verificable, y lo que permite escribir el test **antes** que el código (`rules/eden-testing-rules.md`).

Va a `.claude/context/design-spec-{sección}.md` (`rules/eden-context-rules.md`), y en el contexto vivo
queda **solo el puntero**, no las medidas.

Formato y ejemplo en `references/design-spec.md`.

**Una vez escrito, el Design Spec manda sobre la memoria.** Si a mitad de la implementación surge una
duda de medida, se lee el spec — no se recuerda.

---

### Paso 3 — Tokens y assets

**Tokens.** Todo valor se resuelve, en este orden (`rules/eden-design-rules.md`):

1. Un token existente del proyecto.
2. Una variante derivada de un token (alpha, escala).
3. Solo si no está cubierto: el proceso documentado del proyecto para agregar un token — **nunca** un
   hex ni un px suelto repartido por el código.

Un color correcto pero **hardcodeado falla igual**: coincide en pantalla y rompe el sistema.

**Assets.** Si el asset existe en Figma, se usa el asset real. No se sustituye un icono por un carácter
Unicode, ni un logo por texto, ni una foto por un placeholder. Se bajan con `/eden:download-figma-img` o se
exportan directo; el formato y la densidad, según `references/extraction-protocol.md`.

---

### Paso 4 — Implementación

Antes de escribir código, la **escalera reuse-first** (`rules/eden-component-strategy-rules.md`). Que el
diseño sea nuevo no significa que el código lo sea: se recorre la escalera en orden y se declara en qué
escalón se paró y **por qué los anteriores no alcanzaban**.

Al escribir:

- **HTML semántico**, jerarquía de encabezados sin saltos, la estructura del DOM reflejando la jerarquía
  de componentes del Figma. Nada de envoltorios de más.
- **CSS** con los patrones del proyecto: BEM, mobile-first, donde el proyecto pone sus estilos
  (`rules/eden-code-style-rules.md`). Flexbox, Grid y posicionamiento absoluto **cuando el diseño lo pide**
  — el absoluto es legítimo para un decorativo en una posición exacta, y es un parche cuando compensa un
  layout mal construido.
- **Nada de JavaScript innecesario.** HTML y CSS primero; JS solo para interacción, estado o
  comportamiento dinámico, en Web Components Light DOM.
- **Accesibilidad y performance no se sacrifican por fidelidad**, y la optimización no altera el diseño
  (`rules/eden-quality-rules.md`).
- Si el proyecto es Shopify o WordPress, manda su módulo (`rules/shopify/`, `rules/wordpress/`): la
  naturaleza dinámica de la plataforma **no es excusa** para una diferencia visual.

**Prohibido**, sin matices:

```
valores provisionales · "aproximado" · TODO de fidelidad · breakpoints inventados
assets placeholder · valores arbitrarios · "se ve bastante parecido"
```

Si hace falta un valor y no está en el spec, **se vuelve al Figma y se mide**.

---

### Paso 5 — Validación con Playwright

**Ninguna implementación está terminada antes de esto.** El protocolo completo —viewports, los seis
niveles de validación, bounding boxes, estilos computados, overlay y comparación de imagen— está en
`references/validation-protocol.md`.

Lo esencial:

- El viewport de Playwright es **exactamente** el del frame de Figma.
- No basta con la captura: se leen `boundingBox()` y los estilos computados de cada elemento relevante.
- **La tipografía se verifica primero.** Una fuente mal cargada cambia anchos, saltos de línea, alturas
  y el ritmo vertical entero: ajustar espaciados sobre una fuente equivocada es perseguir un síntoma.
- Cada diferencia se **clasifica** (POSITION, SIZE, SPACING, TYPOGRAPHY, COLOR, BORDER, RADIUS, SHADOW,
  IMAGE, RESPONSIVE, CONTENT, INTERACTION) y se busca su **causa raíz**.
- **Un cambio a la vez**: identificar → cambiar la propiedad mínima → volver a medir → confirmar. Tocar
  cinco propiedades a la vez y ver si mejora no es depurar.

**Tolerancia: 0 desviación intencional.** Puede haber diferencias por rasterización o antialiasing; lo
que no puede haber es un CSS incorrecto justificado como "así renderiza el navegador".

---

### Paso 6 — El loop, y cuándo se cierra

```
medir → clasificar → causa raíz → corregir una cosa → volver a medir
```

Se repite por cada breakpoint y cada componente. Y **después de cada corrección se vuelve a medir todo
lo que pudo moverse**: corregir un padding desplaza lo que hay debajo, y arreglar desktop sin verificar
mobile es como se arregla una cosa y se rompen dos.

El loop cierra de una de dos formas, nunca de una tercera:

- ✅ **1:1 en todos los breakpoints medidos** — diciendo cuántos elementos se midieron.
- ⚠️ **Queda declarado exactamente qué no coincide y por qué** (la fuente no está disponible, la
  plataforma no lo permite, el Figma se contradice). Se declara; **no se aproxima**.

"Quedó cerca" no es un resultado de este skill.

---

### Paso 7 — Reporte al dev

```
🎯 FIGMA EXPERT — {sección o página}

Figma        {archivo} · node-id {id} · breakpoints medidos: {…}
Implementado {rutas}
Escalón      {1–5 de la escalera reuse-first} — {por qué no alcanzaba el anterior}
Design Spec  .claude/context/design-spec-{x}.md

Validación
  {bp}  {n} elementos medidos · {n} coinciden · {n} corregidos · {n} no coinciden

Correcciones aplicadas
  {elemento} · {categoría} · esperado {x} / medido {y} → corregido en {archivo:línea}

⚠️ No coincide / no se pudo medir
  {qué, por qué, y qué haría falta}

Pendiente
  {lo que queda fuera de alcance, si lo hay}
```

Las capturas finales por breakpoint se adjuntan siempre. **Una validación sin captura no se declara
hecha.**

---

### Al terminar

- Descarga el Design Spec y los hallazgos a `.claude/context/` y deja el puntero
  (`rules/eden-context-rules.md`).
- Si el proyecto tiene sitemap, actualiza el estado del NODE-SECTION.
- Si apareció un hecho que se repetirá (un gotcha del tema, una corrección del dev), va a memoria
  (`rules/eden-memory-rules.md`). Lo global **se propone**, no se escribe solo.
- El cierre —commit, push, PR, comentario en el tracker— es de `turnoff-task`.

---

### Checklist final

No se declara completo sin esto. La versión larga, en `references/pixel-perfect-standard.md` (§38).

```
Figma          nodos inspeccionados · dimensiones · tipografía · colores · espaciados
               assets · responsive por breakpoint · componentes y estados
Implementación HTML semántico · tokens (cero hardcode) · assets reales
               responsive explícito · a11y AA · sin JS innecesario
Playwright     cada breakpoint medido · bounding boxes · estilos computados
               capturas finales · discrepancias investigadas y corregidas
Código         sin valores provisionales · sin placeholders · sin TODOs de fidelidad
               sin APIs deprecadas · validador del stack en verde
```
