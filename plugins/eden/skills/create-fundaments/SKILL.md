---
name: create-fundaments
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:create-fundaments`, cuando lo pide de forma explícita e inequívoca, o encadenado desde
  `ignition-task` (que ya fue invocado por él y le pide confirmación antes). NO lo actives porque se
  mencione Figma, tokens o un design system, ni porque el proyecto parezca no tener fundamentos: si no
  lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: crea o actualiza los FUNDAMENTOS
  DE DISEÑO del proyecto. Entra al Figma con Figma Console, extrae el design system que ya existe ahí
  (variables, escalas de color, tipografía, espaciado, radios, sombras, breakpoints, grids,
  iconografía y estados), lo mapea contra lo que el proyecto ya tiene, y lo integra como tokens reales
  de código + documentación + configuración. A partir de ahí ninguna tarea vuelve a estimar un valor
  de diseño.
argument-hint: "[url-de-figma] [| --refresh]"
disable-model-invocation: true
---

## Create Fundaments — fundamentos de diseño del proyecto

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre.

Argumento recibido: `$ARGUMENTS`

Los **fundamentos** son la base medible del proyecto: los tokens con los que se construye todo lo demás.
Sin ellos, cada tarea vuelve a estimar colores y tamaños, y "pixel-perfect" deja de significar algo.

Este skill **lee el design system que ya existe en Figma** y lo instala en el proyecto. No inventa un
sistema de diseño: lo trae. Si Figma no lo define, se reporta como hueco — no se rellena con criterio
propio.

> **Idioma:** al dev, en español. Todo lo que quede escrito — nombres de tokens, archivos, código,
> `docs/design-system.md` y cualquier comentario en el tracker — en inglés.

**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). La sesión principal
decide, verifica y habla con el dev; **el trabajo de traer datos o producir cambios se delega a agentes
(nivel `fast`)**, por rol: `explorer` (escanear e inventariar), `design-extractor` (Design Spec), `implementer`
(escribir), `design-auditor` (medir), `reviewer` (revisar). Los agentes se resuelven por rol con el roster del stack del proyecto
(`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`); si el stack no tiene roster, se usa
`teams/_generic/roster.md`. Lo que reporta un agente
es una afirmación: se verifica antes de darlo por bueno.


---

### Paso 1 — ¿Qué hay ya en el proyecto?

Antes de tocar Figma, audita el estado actual. Los fundamentos viven en **cuatro sitios**, y los cuatro
tienen que existir y coincidir:

| Artefacto | Dónde | Qué es |
|---|---|---|
| **Tokens en código** | según el stack (ver `references/output-targets.md`) | La verdad de ejecución |
| **Doc legible** | `docs/design-system.md` | La verdad consultable por el equipo |
| **Config del kit** | `.claude/project-config.json` | Lo que leen los skills y el auditor de diseño |
| **Bloque en `CLAUDE.md`** | sección "Sistema de diseño de este proyecto" | Lo que se carga cada sesión |

```bash
ls docs/design-system.md .claude/project-config.json CLAUDE.md 2>/dev/null
grep -rnE "(eden|fl)-fundaments" CLAUDE.md docs/design-system.md 2>/dev/null
```

Cada doc generado por este skill lleva un **marcador de sincronización** como última línea:

```
<!-- eden-fundaments: updated=YYYY-MM-DD figma={file_key} version={figma_version_id} -->
```

Resultados posibles:

- **No existe nada** → creación completa (Pasos 2–7).
- **Existe pero incompleto** (falta uno de los cuatro artefactos, o el marcador) → completa solo lo que
  falta; no reescribas lo que ya está bien.
- **Existe y está sincronizado** → dilo en una línea y termina. No regeneres por regenerar.
- **Existe pero el Figma cambió** (`figma_get_file_versions` / `figma_get_changes_since_version`
  posteriores al marcador) → modo `--refresh`: reporta el diff de tokens **antes** de escribir nada.
  Para saberlo con una sola llamada, el estado del archivo se compara como en la caché de diseño
  (`rules/on-demand/eden-design-cache-rules.md`, paso 2): `lastModified` igual al del marcador → vigente.

**Escanea también los tokens que el proyecto ya usa** aunque no estén documentados: variables CSS,
archivo de tema, `settings_schema.json`, esquemas de color. Ese inventario es crítico para el Paso 4.

---

### Paso 2 — Entrar al Figma

URL del argumento, de `.claude/project-config.json`, del `CLAUDE.md` o del ticket. Si no hay ninguna,
**pregúntala** — sin Figma no hay fundamentos medidos. Excepción: si el skill se encadena desde
`/eden:w2shopify` en modo `clone`, la fuente es el **sitio medido** (los candidatos de
`.claude/context/w2s/{sitio}/`): se salta la entrada a Figma, el informe dice `fuente: sitio medido
{url}` y todo lo demás —mapeo, informe previo, nada escrito sin el sí— sigue igual. Si el dev confirma que **no existe** un Figma, la
única otra base es una propuesta que él apruebe: ofrécele UI/UX Pro Max (bloque 🎨 de
`skills/uiux-pro/SKILL.md`) y espera; con su sí y la propuesta aprobada, los fundamentos salen de ella,
marcados como `fuente: propuesta UI/UX Pro Max aprobada por el dev` en el informe, y el resto de este skill
sigue igual (informe primero, nada se escribe sin su sí).

```
figma_get_status            → confirmar conexión
figma_list_open_files       → elegir el archivo correcto si hay varios
figma_navigate              → al archivo/página del design system
```

Si el MCP no responde: `figma_reconnect`, luego `figma_diagnose`. **No sigas de memoria con un Figma
desconectado**; dilo y detente.

Registra la **versión del archivo** (`figma_get_file_versions`) — va en el marcador de sincronización.

---

### Paso 3 — Extraer el design system

El detalle de qué herramienta da qué está en `references/token-mapping.md`. Lo que hay que traer:

| Fundamento | Qué extraer | Herramientas |
|---|---|---|
| **Color** | Primitivos y semánticos, por modo (light/dark), con opacidad | `figma_get_variables`, `figma_get_token_values`, `figma_get_styles` |
| **Tipografía** | Familias, pesos, tamaños, line-height, letter-spacing, transform — la escala completa | `figma_get_text_styles` |
| **Espaciado** | La escala real (4/8pt u otra), paddings y gaps recurrentes | `figma_get_variables`, medición de frames |
| **Breakpoints** | Anchos **exactos** de los frames de cada tamaño | `figma_get_file_data` |
| **Grid / contenedores** | Columnas, gutters, márgenes, ancho máximo por breakpoint | layout grids de los frames |
| **Radios y bordes** | Escala de border-radius y anchos de borde | `figma_get_variables` |
| **Sombras / efectos** | Elevaciones nombradas | `figma_get_styles` |
| **Iconografía** | Set, tamaños, grosor de trazo | `figma_search_components` |
| **Estados** | Hover, focus, disabled, error, éxito | variantes de componentes |
| **Panorama** | Resumen del DS y auditoría de consistencia | `figma_get_design_system_kit`, `figma_get_design_system_summary`, `figma_audit_design_system` |

**Prioriza las variables sobre los valores sueltos.** Un color que en Figma es variable se convierte en
token; un color que aparece hardcodeado en tres frames es una inconsistencia del diseño — se anota y se
reporta, no se canoniza como token.

Captura también lo que **no** está definido: si Figma no tiene escala de espaciado, o solo tiene un
breakpoint, eso es un **hueco** y va en el reporte.

---

### Paso 4 — Mapear contra lo que el proyecto ya tiene

El paso que evita romper el proyecto. Por cada token extraído, decide:

- **Ya existe con otro nombre** → **se usa el del proyecto.** No se crea un token paralelo que haga lo
  mismo; se documenta la equivalencia Figma ↔ proyecto.
- **Ya existe con el mismo nombre pero distinto valor** → ⚠️ **conflicto.** No lo pises en silencio:
  va al reporte y lo decide el dev. Cambiar el valor de un token existente repinta el sitio entero.
- **No existe** → token nuevo, siguiendo la convención de nombres que el proyecto ya usa (no la que a
  ti te guste).
- **Existe en el proyecto y no en Figma** → se conserva y se anota como "no cubierto por el design
  system".

Nombres: **primitivos** (`--color-brand-500`) y **semánticos** (`--color-text-primary`) separados; los
componentes consumen semánticos. Si el proyecto ya tiene un esquema de nombres, **manda el proyecto**.

---

### Paso 5 — Proponer al dev y esperar aprobación

**No escribas nada todavía.** Presenta:

```
🎨 FUNDAMENTOS DE DISEÑO — {proyecto}

Origen: Figma {archivo} · versión {id} · {n} variables, {n} estilos de texto

🎨 Color         {n} primitivos · {n} semánticos · modos: {light/dark}
🔤 Tipografía    {n} familias · escala de {n} tamaños
📐 Espaciado     escala {4pt/8pt/otra} · {n} pasos
📱 Breakpoints   mobile {x} · tablet {x} · desktop {x}
🔲 Radios        {n} · 🌑 Sombras {n} · 🎯 Iconos {set, tamaños}

♻️ Ya existe en el proyecto (se reutiliza)
   {token del proyecto} ← {variable de Figma}

⚠️ Conflictos (deciden tú)
   {token} — proyecto: {valor} · Figma: {valor} → ¿cuál gana?

🆕 Tokens nuevos ({n})
   {lista resumida}

🕳️ Huecos en el Figma
   {lo que el design system no define y habrá que preguntar al diseñador}

📝 Se va a escribir en
   {rutas concretas por artefacto}

¿Lo integro así?
```

**En Shopify** se usa el formato de propuesta de `references/shopify-integration.md` (§8), y **en
WordPress el de `references/wordpress-integration.md`** (el mapeo depende del sabor declarado en
`wordpress.flavor`): el mapeo ya resuelto — qué esquema de Figma va a qué `color_scheme` del tema, qué settings nuevos, qué va al snippet
propio, qué no se toca — marcando con ⚠️ todo lo que cambia un valor que ya está en producción.

Los **conflictos y los huecos se resuelven antes de escribir.** Un token con el valor equivocado
propaga el error a todo lo que se construya después. Y la propuesta se presenta **resuelta**: nunca una
pregunta abierta tipo "¿dónde pongo los tokens?", sino el mapeo concreto para que el dev confirme o
corrija.

---

### Paso 6 — Integrar al proyecto

Con la aprobación, escribe los cuatro artefactos. Rutas y formato por stack en
`references/output-targets.md`; **en Shopify, el procedimiento completo está en
`references/shopify-integration.md`, y en WordPress en `references/wordpress-integration.md`** — en
ambas plataformas el proyecto ya tiene un sistema de tokens y lo que se hace es llenarlo, no crear otro
en paralelo. Reglas transversales:

- **Aditivo, nunca destructivo.** No borres ni redefinas tokens existentes salvo que el dev lo haya
  aprobado explícitamente en el Paso 5.
- Los tokens van donde el proyecto ya los pone. Si no hay convención, se propone la del stack y **se
  confirma**.
- `docs/design-system.md` se escribe **en inglés** (convención de `docs/`), con tabla de tokens, valores,
  a qué corresponden en Figma y cuándo usar cada uno.
- El bloque de `CLAUDE.md` se rellena con los valores reales (nada de placeholders).
- `.claude/project-config.json` recibe `figma.file_key`, las URLs y los **breakpoints exactos**.
- Los cuatro artefactos terminan con el marcador `eden-fundaments`.
- Todo esto se commitea **en la rama de trabajo**, nunca directo sobre una rama protegida.

---

### Paso 7 — Verificar

- Los tokens nuevos **no rompen nada existente**: revisa que ningún nombre choque con uno en uso con
  otro significado.
- El proyecto sigue compilando/validando (Theme Check, build, linter — lo que aplique).
- **Contraste WCAG AA** en las combinaciones texto/fondo que definen los semánticos. Si un par del
  design system no llega a AA, **repórtalo** — es un hallazgo real, no algo a corregir por tu cuenta.
- Una página existente renderiza exactamente igual que antes (los fundamentos son aditivos: no deben
  cambiar nada visualmente al instalarse).

---

### Salida final

```
✅ FUNDAMENTOS INTEGRADOS — {proyecto}
   Tokens:   {n} nuevos · {n} reutilizados · {n} conflictos resueltos
   Escritos: {rutas}
   Figma:    {archivo} @ versión {id}
   🕳️ Huecos pendientes con diseño: {lista o "ninguno"}
   Estado visual del sitio: sin cambios (integración aditiva)
```
