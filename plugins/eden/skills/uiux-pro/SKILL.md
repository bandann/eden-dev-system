---
name: uiux-pro
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA O CON EL SÍ DEL DEV — NUNCA EN AUTOMÁTICO. Se usa únicamente cuando el dev
  escribe `/eden:uiux-pro`, o cuando un flujo de Eden (ignition-task, create-new-section, section-mod,
  create-fundaments, antislop) detectó que la tarea no tiene fuente de diseño, le mostró el bloque 🎨 y el
  dev respondió que sí. No lo actives porque falte un Figma ni porque la tarea sea visual: se propone y se
  espera. — Qué hace cuando SÍ se invoca: usa UI/UX Pro Max (incluido en Eden, MIT) para proponer una
  dirección visual —patrón, estilo, paleta, tipografía, efectos, reglas de UX y lo que hay que evitar— para
  el producto y el stack del proyecto, la traduce a los tokens y las reglas de Eden (Figma y fundamentos
  mandan, WCAG AA, reuse-first, antislop) y la presenta como propuesta. No escribe código ni fundamentos
  sin otro sí del dev.
argument-hint: "[qué se diseña: producto, sección o página] [--stack X] [--variance 1-10] [--motion 1-10] [--density 1-10]"
disable-model-invocation: true
---

## UI/UX Pro Max — dirección visual cuando no hay diseño, con consulta

Argumento recibido: `$ARGUMENTS`

UI/UX Pro Max (https://github.com/nextlevelbuilder/ui-ux-pro-max-skill, MIT, © Next Level Builder) es
una base local de estilos, paletas, tipografías, guías de UX y reglas por stack. **Eden la trae incluida**,
fijada a un commit de upstream, en `${CLAUDE_PLUGIN_ROOT}/vendor/ui-ux-pro-max/` (su `LICENSE` y su
`VENDORED.json` dicen de dónde y de qué versión). No hay que instalar nada. Si el dev prefiere su propia
instalación más nueva, `uiux.source: "installed"` en `~/.claude/eden-config.json`. El script puente es
`${CLAUDE_PLUGIN_ROOT}/scripts/eden_uiux.py`.

> **La regla de oro de este skill:** UI/UX Pro Max **nunca corre sin un sí del dev en ese momento**. Ni
> siquiera una búsqueda de solo lectura. Un sí cubre la consulta que se le mostró; otra consulta distinta
> (otro producto, otros diales, guardar la propuesta como fundamentos) es otra pregunta.

### Cuándo se propone (y solo se propone)

Solo si **no hay fuente de diseño**: ni Figma, ni captura, ni imagen, ni documento de dirección visual. Si
hay Figma, **Figma manda** y este skill no se menciona. Si el proyecto declara `uiux.mode: off` en
`.claude/project-config.json`, tampoco. No existe un modo automático.

El flujo que lo detecta muestra este bloque y **espera**:

```
🎨 Esta tarea no tiene diseño de referencia (sin Figma, captura ni documento).
   ¿Uso UI/UX Pro Max para proponer una dirección visual —estilo, paleta, tipografía y reglas de UX—
   para {producto/sección} en {stack}? Es una propuesta: no escribo código ni fundamentos sin otro sí.
   (sí / no)
```

Con un **no**, se sigue como hasta ahora (tarea no visual, capa estética de antislop si aplica) y no se
vuelve a preguntar en esa tarea.

### Paso 1 — ¿Qué copia se usa?

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_uiux.py" status
```

Dice qué copia corre (la incluida en Eden, o la instalación propia del dev con `uiux.source: "installed"`)
y su versión. Si dice «no disponible», falta `vendor/ui-ux-pro-max` en el plugin: díselo al dev
(reinstalar Eden lo arregla) y detente. **No instales nada por tu cuenta.**

### Paso 2 — Armar la consulta (y mostrarla)

- **Producto y contexto:** del ticket, del `CLAUDE.md` del proyecto o del argumento — tipo de producto,
  industria, público, 2–5 palabras clave. Nada inventado: si falta, se pregunta.
- **Stack:** `python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_uiux.py" stack {project.stack} {flavor}` (vacío =
  solo reglas generales de UX; Liquid y temas de WordPress usan `html-tailwind` como guía de HTML/CSS).
- **Diales** opcionales si el dev los pide: `--variance`, `--motion`, `--density`.

Muéstrale al dev la consulta exacta en una línea. Si ya dijo que sí a "proponer una dirección visual",
esta consulta está cubierta; si cambias de producto o de diales, vuelve a preguntar.

### Paso 3 — Ejecutar (solo con el sí)

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_uiux.py" run --approved --save {slug} -- "{producto industria palabras}" --design-system -p "{Proyecto}" --format markdown
```

Para una duda concreta (accesibilidad de un formulario, un patrón de navegación), en vez de
`--design-system` usa una búsqueda por dominio (`--domain ux`, `--domain typography`…) o por stack
(`--stack react`). `--persist`, `--force` y `--output-dir` están bloqueados: lo que se guarda va a
`.claude/context/uiux-{fecha}-{slug}.md`.

### Paso 4 — Traducirlo a Eden (la propuesta es una sugerencia, no una fuente)

Prioridad, de mayor a menor:

1. **Figma**, si apareció mientras tanto: se descarta la propuesta.
2. **Los fundamentos y tokens del proyecto** (`docs/design-system.md`, el bloque del `CLAUDE.md`): la
   paleta y la tipografía de UI/UX Pro Max se **mapean a los tokens que existen**; nunca un hex, un px
   de tipografía ni un `font-family` sueltos. Si el proyecto no tiene fundamentos, la propuesta puede
   servir para crearlos — con otro sí, por `/eden:create-fundaments`.
3. **Las reglas de Eden:** WCAG AA (contraste 4.5:1 medido, foco visible, objetivos táctiles),
   reuse-first (lo que ya existe en el tema o el proyecto antes que un componente nuevo),
   `prefers-reduced-motion`, y la lista "por defecto se evita" de antislop
   (`rules/on-demand/eden-antislop-rules.md`): si UI/UX Pro Max sugiere *bento grid*, *glassmorphism*,
   degradados neón o un layout de plantilla, gana antislop salvo que el dev lo elija con un motivo escrito.
4. **UI/UX Pro Max:** el resto de su propuesta.

### Paso 5 — Presentar y esperar

```
🎨 PROPUESTA DE DIRECCIÓN VISUAL — {producto/sección} · UI/UX Pro Max {versión}

Patrón        {el que propone} — {por qué encaja, en una línea}
Estilo        {estilo} · {lo que se descartó por antislop, si algo}
Paleta        {rol → token del proyecto | color propuesto si no hay tokens} · contraste {medido}
Tipografía    {títulos / cuerpo → tokens | familias propuestas} · escala
Espaciado     {escala propuesta → tokens}
UX            {las 3–5 reglas que más pesan aquí}
Evitar        {anti-patrones que señala}
Guardado      .claude/context/uiux-{fecha}-{slug}.md

¿Qué hago con esto? (a) usarlo como dirección de esta tarea · (b) crear los fundamentos del proyecto con
create-fundaments · (c) ajustar algo · (d) descartarlo
```

Cada opción es otro sí. Con (a), la dirección entra al plan de la tarea como `🎨 Dirección: UI/UX Pro
Max (propuesta aprobada)`, y la capa estética de antislop se aplica sobre ella. Con (b), se encadena
`create-fundaments`, que muestra su propio informe antes de escribir nada.

### Qué NO hace

- Correr sin el sí del dev, o decidir por él entre las opciones del Paso 5.
- Instalar UI/UX Pro Max, sus CLIs o fuentes, o actualizar la copia incluida (`eden_uiux.py vendor-update` solo
  lo corre quien mantiene Eden, cuando lo pide).
- Escribir código, tokens, `docs/design-system.md` o el `CLAUDE.md`: eso pasa por los flujos de Eden, con
  su propia aprobación.
- Reemplazar un Figma, aunque la propuesta parezca mejor.
