---
name: qa-pixel-perfect
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:qa-pixel-perfect` o lo pide de forma explícita e inequívoca. NO lo actives porque haya
  un Figma, porque la página parezca terminada o porque se hable de QA: si no lo pidió por su nombre,
  no se usa. — Qué hace cuando SÍ se invoca: QA de fidelidad de una PÁGINA COMPLETA contra su Figma, y
  **corrige** lo que no coincide. Recorre todas las secciones de la página en todos los breakpoints
  midiendo el render real con Playwright contra el nodo de Figma: tipografía (familia, tamaño, peso,
  grosor, altura de línea), espaciados (padding, margin, gap), dimensiones, alineaciones, colores de
  todo tipo y animaciones. Aplica las correcciones seguras, se detiene a preguntar en las que tienen
  blast radius, y repite el ciclo medir→corregir→medir hasta que la página es 1:1 o queda declarado
  exactamente qué falta y por qué.
argument-hint: "<url de la página> [| url-de-figma] [| sección concreta]"
disable-model-invocation: true
---

## QA Pixel Perfect — la página entera, 1:1, y corregida

Argumento recibido: `$ARGUMENTS`

**No hay punto medio: o la página es idéntica al Figma, o queda escrito exactamente qué no lo es y por
qué.** "Quedó cerca" no es un resultado aceptable de este skill.

> **Idioma:** al dev, en español. El código que se corrija, en inglés.

**Dependencias:** **Playwright** (medir el render real) y **Figma Console** (medir el diseño). Si
Playwright no responde, **dilo y detente**: el CSS escrito y el computado no son lo mismo, y medir leyendo
el código produce un informe falso.

### Cómo se reparte con los otros tres

| | Qué hace | ¿Corrige? |
|---|---|---|
| **`test-visual`** | Semáforo repetible de una sección, contra baseline versionado | No |
| **`attention-detail`** | Microscopio sobre **una** sección: informe exhaustivo | No |
| **`qa-pixel-perfect`** | **Página completa**, mide **y corrige** hasta 1:1 | **Sí** |
| `design-auditor` (rol) | El agente que ejecuta la medición | No |

Este es el único que **toca código**. Los otros reportan.

Los agentes se resuelven por rol con el roster del stack del proyecto (`teams/{stack}/roster.md`, ver
`rules/eden-team-rules.md`); si el stack no tiene roster, se usa `teams/_generic/roster.md`.

---

### Paso 1 — Preparar el barrido

```
1. URL de la página renderizada (preview, staging o local)
2. Figma de esa página — si el proyecto tiene docs/sitemap.md, los NODE-SECTION ya la mapean
3. Breakpoints: los del proyecto o del perfil (`qa.breakpoints`, si lo declara)
4. ¿Alcance? La página completa (por defecto) o una sección concreta
```

**Los anchos salen de `.claude/project-config.json`**, que a su vez salen de los frames de Figma. Medir
con una regla equivocada invalida el informe entero: si no están, se levantan antes
(`create-fundaments`).

**Inventaría las secciones de la página antes de medir** — del sitemap si existe, o recorriendo el DOM
y el frame de Figma. El barrido cubre **todas**; una sección saltada es una sección que nadie revisó.

---

### Paso 2 — Medir: todo, en todas partes

Por cada sección y **cada breakpoint**. Procedimiento y trampas en
`attention-detail/references/measuring.md`; lo que se asevera, en
`test-visual/references/what-to-assert.md`. Resumen de los grupos — **ninguno es opcional**:

| Grupo | Qué se compara |
|---|---|
| 🔤 **Tipografía** | Familia real cargada, tamaño, **peso/grosor**, line-height, letter-spacing, transform |
| 📐 **Espaciado** | Padding ×4, margin ×4, **gap** — y la separación real entre cajas |
| 📏 **Dimensiones** | **Ancho y alto**, max-width del contenedor, aspect-ratio |
| 🧭 **Alineación** | Alineación de texto, justificación y alineación del flex/grid, posición relativa al contenedor |
| 🎨 **Color** | Texto, fondo, bordes, iconos, gradientes, sombras — **y que venga del token** |
| 🎬 **Animación** | Propiedad, duración, easing, delay, y `prefers-reduced-motion` |
| 🖼️ **Imágenes** | Tamaño renderizado, aspect-ratio, object-fit, `alt`, `width`/`height` |

Y lo que **solo se ve a nivel página** y por eso este skill existe
(`references/page-level-checks.md`): el **orden** de las secciones, el **espaciado entre** ellas, el
ritmo vertical, header y footer, la coherencia de tokens entre secciones, y que **no haya scroll
horizontal** en ningún ancho.

**La medición se delega** al `design-auditor` (rol) por sección (`rules/eden-context-rules.md`): devuelve
deltas, no volcados. Después de cada sección, descarga el resultado a `.claude/context/`.

---

### Paso 3 — Clasificar cada discrepancia antes de tocar nada

**Este paso es lo que evita que "arreglar el pixel perfect" rompa el sitio.** Cada diferencia cae en una
de tres:

| | Qué es | Qué se hace |
|---|---|---|
| 🟢 **Corrección segura** | El valor vive en esta sección y no lo consume nadie más | **Se corrige** |
| 🟡 **Requiere decisión** | Tocaría un token, un componente compartido o el default de un setting | **Se para y se pregunta** |
| 🔴 **No se puede igualar** | La fuente no está disponible, la plataforma no lo permite, el Figma no lo define | **Se reporta como bloqueante** |

La 🟡 es la importante: **igualar el Figma aquí puede desalinear otras diecinueve páginas.** Antes de
tocar cualquier valor compartido se mide el blast radius (`grep`, y `graphify affected` si el proyecto
tiene cerebro) y **lo decide el dev**. Corregir en silencio algo compartido es exactamente el fallo que
las reglas del kit existen para evitar.

La 🔴 **no se aproxima**. Si la fuente del Figma no está disponible, no se pone "la más parecida" y se
da por bueno: se reporta, se dice qué hace falta, y queda como pendiente declarado.

---

### Paso 4 — Corregir

Solo las 🟢, y las 🟡 que el dev haya aprobado. Con las reglas del kit, que aquí no se suspenden:

- **Colores y tipografía por token**, nunca un valor crudo. Si la corrección correcta es un hex porque
  no hay token, eso es una 🟡, no una 🟢.
- **Acotado a la sección**: BEM del bloque, nada que se filtre a lo global.
- **Los patrones del proyecto mandan** — dónde viven los estilos, cómo se nombran las clases.
- **Nada de "ya que estoy"**: se corrige la discrepancia medida, no lo que a uno le parezca mejorable.
- Si la diferencia entre mobile y desktop revela un **hueco de configuración** (un bloque de texto con
  un solo control de tamaño), eso es 🟡: se propone la variante responsive con default neutro, no un
  override CSS.

Corrección de volumen → el `implementer` (rol) con alcance cerrado.

---

### Paso 5 — El loop, hasta que cierre

```
medir → clasificar → corregir → MEDIR OTRA VEZ
```

**No se da por corregida una discrepancia sin volver a medirla.** Corregir un padding puede mover lo que
hay debajo; corregir un tamaño de fuente puede cambiar la altura de la caja. El ciclo se repite hasta
que:

- **No quedan 🟢 ni 🟡 aprobadas sin cerrar**, y
- lo que queda son 🟡 pendientes de tu decisión o 🔴 declaradas.

Si un arreglo rompe otra medida, **se dice** — no se corrige el nuevo fallo en silencio y se sigue.

---

### Paso 6 — El veredicto

```
🎯 QA PIXEL PERFECT — {página}

Resultado: {✅ 1:1 | ⚠️ {n} pendientes}

Por breakpoint
   1920 ✅ {n}/{n}   1440 ✅ {n}/{n}   1280 ⚠️ {n}/{n}
   1024 ✅ {n}/{n}    768 ✅ {n}/{n}
    414 ⚠️ {n}/{n}    375 ✅ {n}/{n}

Por sección
   ✅ hero-banner        {n} nodos · corregidas {n}
   ⚠️ product-carousel   {n} nodos · {n} sin resolver

🔧 CORREGIDO ({n})
   {sección} · {propiedad}: {antes} → {ahora}   {archivo:línea}

🟡 REQUIERE TU DECISIÓN ({n})
   {qué} — igualar el Figma exige {tocar X}
   Blast radius: {n} páginas / {n} instancias
   Opciones: {A} · {B}

🔴 NO SE PUEDE IGUALAR ({n})
   {qué} — {por qué} — {qué haría falta}

📊 Nodos medidos {n} · coinciden {n} · no se pudieron medir {n}
```

**Lo que no se pudo medir se cuenta aparte, nunca como verde.** Y si el resultado no es 1:1, el titular
lo dice: no se presenta como aprobado algo con pendientes.

---

### Reglas

- **No hay punto medio.** O es 1:1, o hay una lista exacta de qué falta, por qué, y qué hace falta para
  cerrarlo. "Se ve bien" no es un resultado.
- **No se toca nada compartido sin aprobación.** El blast radius se mide antes, siempre.
- **No se aproxima lo que no se puede igualar.** Se declara.
- **No se ajusta la medición para que cuadre.** Si el Figma y el render difieren, el dato es el dato.
- **Se vuelve a medir después de cada corrección.** Un arreglo sin verificar es una suposición.
- **Diferencias bajo 1px se ignoran** (redondeo de render); todo lo demás se reporta.
- Si el Figma cambió después de construir, **eso no es un bug del código**: se reporta y se decide.

---

### Cuándo usar cuál

- Construyendo una sección → `test-visual` (baseline y semáforo).
- Una sección no cuadra y no sabes por qué → `attention-detail`.
- **La página entera, antes de entregar, y quieres que quede igual** → este.
- Cerrando la tarea → `turnoff-task`, que exige el verde.
