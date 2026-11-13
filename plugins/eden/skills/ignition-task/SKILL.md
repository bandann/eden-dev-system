---
name: ignition-task
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:ignition-task` o pide de forma explícita e inequívoca que se arranque una tarea con el
  flujo de Eden (por ejemplo "haz ignition de esto"). NO lo actives porque el dev pegue una URL de
  ticket (Asana, SMG Hub o ClickUp) o de Figma, ni porque empiece a trabajar, ni porque la situación
  parezca encajar: si no lo pidió por su nombre, no se usa. Ante la duda, pregúntale si quiere el flujo Eden en vez de
  ejecutarlo. — Qué hace cuando SÍ se invoca: arranque **e implementación** de una tarea de Eden.
  Lee por MCP todo el contexto del ticket del tracker (descripción, requerimientos, campos,
  comentarios, adjuntos y subtareas), extrae el diseño de Figma nodo por nodo en mobile y desktop con
  Figma Console, mapea el proyecto, valida los fundamentos de diseño y el sitemap, pregunta de dónde
  sale la rama y la crea, propone un plan repartido por un orquestador según complejidad y alcance, y
  —una vez aprobado— **implementa las unidades de trabajo**. NO comenta en el tracker, NO commitea, NO
  pushea y NO abre PRs: todo eso es tarea de `turnoff-task`.
argument-hint: "<url-del-ticket> (Asana, SMG Hub o ClickUp) [| url-de-figma] [| descripción libre]"
disable-model-invocation: true
---

## Ignition Task — arranque Eden

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre. **El plan** se presenta igual, pero en `--auto` no se espera su aprobación para el trabajo local y reversible de la rama: el dev puede leerlo y pararlo en cualquier momento; las preguntas previas que no se pueden suponer (rama base, sabor, derechos) se hacen todas juntas al arrancar.

Argumento recibido: `$ARGUMENTS`

Ejecuta los pasos **en orden**. **No escribas ni una línea de código hasta que el Paso 8 (plan) esté
aprobado por el dev**; a partir de ahí, el Paso 10 implementa. Si falta información, pregunta — nunca
inventes un requerimiento.

Reglas del equipo que gobiernan todo lo de abajo (léelas si no están en contexto):
`rules/eden-workflow-rules.md` y `rules/eden-component-strategy-rules.md`. Las referencias detalladas de
este skill viven en `ignition-task/references/`.

Si el stack tiene líder (`/eden-{stack}`, p. ej. `/eden:shopify`), este skill es el playbook de tarea que el
líder usa; sus puertas de aprobación no cambian.

> **Idioma:** **español solo para hablarle al dev** en la consola. **Todo lo que quede escrito va en
> inglés**: código, ramas, commits, PR y docs.

**Reparto de responsabilidades — no lo cruces:**

| `ignition-task` (este skill) | `turnoff-task` |
|---|---|
| Entiende la tarea, mide el diseño, prepara la base de desarrollo (rama, artefactos) e **implementa** | Verifica, audita, commitea, pushea, abre el PR |
| **Lee** el tracker cuanto haga falta | **Escribe** en el tracker: el comentario de cierre |
| Reporta al dev en consola, en español | Produce el reporte formal y el cierre |

Este skill **no publica comentarios en el tracker, no commitea, no pushea y no abre PRs.** Ni siquiera al
terminar de implementar: el trabajo queda en la rama, sin commitear, listo para `turnoff-task`.

**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). Tú, la sesión
principal, eres el orquestador: entiendes, decides, verificas y hablas con el dev. **Todo trabajo de
traer datos o producir cambios se delega a un agente (nivel `fast`)**, por rol — `explorer` para escanear e
inventariar, `design-extractor` para el Design Spec, `implementer` para escribir, `design-auditor`
para medir, `reviewer` para revisar. Los agentes se resuelven por rol con el roster del stack del
proyecto (`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`); si el stack no tiene roster, se usa
`teams/_generic/roster.md`. Lo que llega de un agente es una afirmación: se verifica.

Si la sesión corre claramente en un modelo rápido o pequeño (Haiku, un Flash, un Mini…), dilo en una
línea (`⚠️ Esta sesión no está en el modelo principal — el kit asume el más capaz para planificar.` y
cómo cambiarlo en esta herramienta: en Claude Code, `/model opus`) y sigue; no bloquees el trabajo. Si
no sabes en qué modelo corre la sesión, no digas nada.


**Contexto — no llenarlo, descargarlo por hitos** (`rules/eden-context-rules.md`). Una tarea larga no
debe obligar a comprimir ni a abrir sesión nueva:

- **Toda lectura grande se delega, sin excepción** — escaneos, árboles de Figma, diffs largos,
  inventarios. La sesión principal recibe conclusiones, nunca volcados. Única excepción: un archivo
  concreto y acotado que se va a modificar ahora mismo.
- **En contexto quedan punteros, no contenido.** Lo destilado se escribe en `.claude/context/` y en la
  sesión queda una línea con la referencia.
- **Se descarga en los hitos** (`/eden:context offload`): tras extraer Figma, tras inventariar, **al
  cerrar cada unidad de trabajo**, tras cada auditoría.
- **Nunca se sueltan** el requerimiento, el plan, las decisiones ni lo pendiente. Y **nada se suelta
  sin haberlo escrito antes**.

**Perfil de operación.** Antes de asumir cualquier default, comprueba si el proyecto tiene perfil
activo (`<!-- eden-profile: … -->` en `CLAUDE.md`, o `profile` en `.claude/project-config.json`) y lee su
`profile.json`. El perfil trae las verdades concretas —estados del tracker, ramas, roles, umbrales— que
si no, tendrías que preguntar. **Precedencia:** el dev en el momento > el proyecto > el perfil > el
default del núcleo. Si algo no lo cubre el perfil, aplica el default y **dilo en una línea**; nunca te
bloquees por eso (`rules/eden-profiles-rules.md`).

> Un marcador legado `fl-` (`fl-fundaments`, `fl-sitemap`, `fl-profile`…) sigue siendo válido: se
> propone migrarlo a `eden-`, nunca se reescribe en silencio.

---

### Paso 0 — Contexto de arranque

1. Registra la **hora de inicio** (para reportar tiempo en `turnoff-task`) y resuelve el **tracker**
   del proyecto (`rules/eden-tracker-rules.md`: dev > referencia > `tracker.provider` > perfil >
   config global > default `asana`).
2. Identifica al dev: `git config user.email` / `user.name`.
3. Detecta si ya hay trabajo previo sobre esta tarea (rama existente, PR abierto, checkpoint):
   ```bash
   git branch -a --list "*{ticket-id}*"
   git status --short
   ```
   - Rama existente del mismo dev → **continuar**, no re-arrancar: salta al Paso 7 y re-sincroniza el plan.
   - Rama de otro dev → estás entrando a **QA**, no a implementación: dilo explícitamente y adapta el plan.
   - `.claude/checkpoint.md` presente y vigente → léelo y reanuda desde ahí. Ese archivo es la
     **memoria de trabajo** del kit (`rules/eden-memory-rules.md`).
4. **Consulta el cerebro** antes de planear — `/eden:memory recall {tema de la tarea}`: qué sabemos ya del
   stack, qué nos pasó antes en algo parecido, qué recetas funcionaron. Llegar a mitad de la tarea con
   un "por cierto, esto ya nos había pasado" no sirve de nada; se mira **al arrancar**.
   Si el proyecto tiene grafo (`rules/eden-brain-rules.md`), aquí también se le pregunta a él —
   `graphify query "{lo que hay que entender}" --budget 2000`— **antes** de mandar a nadie a leer medio
   repo. Y se comprueba con `/eden:brain status` que el grafo no esté más viejo que el último commit: uno
   desactualizado responde con seguridad sobre código que ya no existe.

---

### Paso 1 — Leer el ticket del tracker

Resuelve el tracker por la referencia y extrae el id del ticket (Asana, SMG Hub o ClickUp; tabla de
formatos en `references/tracker.md`). Con el adaptador del tracker (`rules/eden-tracker-rules.md`),
lee con estas operaciones:

| Necesitas | Operación |
|---|---|
| Datos del ticket | `task.read` |
| Comentarios (contexto que no está en la descripción) | `task.comments` |
| Campos personalizados (para interpretar ids) | `task.fields` |
| Adjuntos (specs, capturas, PDFs) | `task.attachments` |
| Subtareas | `task.subtasks` |

Detalles y casos borde en `references/tracker.md`.

**Qué debes sacar en limpio** (si algo no está, se pregunta, no se asume):

- Objetivo real de la tarea en una frase.
- Requerimientos explícitos, uno por uno, numerados.
- Criterios de aceptación (si el ticket no los tiene, propónlos y valídalos con el dev).
- Alcance: qué páginas/plantillas/componentes toca, y qué **NO** toca.
- Enlaces: Figma, Loom/YouTube, staging, docs.
- Fuera de alcance / ambigüedades / contradicciones → lista aparte para preguntar.

**Subtareas.** Si la tarea tiene subtareas, léelas **todas** con su descripción y estado. Cada subtarea
es una unidad de trabajo del plan y se mapea 1:1 a un ítem del Paso 8. Si una subtarea ya está cerrada,
no la re-implementes: verifícala.

**Video en el ticket.** Si aparece un Loom/YouTube/MP4, procésalo con el skill `video-to-ticket` antes
de planear — no le pidas al dev que te lo resuma.

---

### Paso 2 — Extracción de diseño con Figma Console

Si la tarea (o el dev) trae una URL de Figma, el diseño se **mide**, no se estima.

**Delega la extracción al `design-extractor` (rol)** — obligatorio, no opcional (`eden-context-rules.md`): te
devuelve el Design Spec destilado en vez de que el árbol completo de Figma ocupe tu contexto. Al
terminar, **descárgalo** a `.claude/context/design-spec-{sección}.md` y quédate con el puntero. El procedimiento que sigue
está en `references/figma-extraction.md`; lo de abajo es lo que debes exigirle al resultado.

**Caché primero** (`rules/on-demand/eden-design-cache-rules.md`): si esa sección ya se midió y el
archivo de Figma no cambió, el extractor devuelve la caché sin volver a leer Figma. Muéstrale al dev su
línea `🎨` (igual a lo guardado · guardado por primera vez · qué cambió) tal cual, en español.

Secuencia mínima:

1. `figma_get_status` — confirmar conexión con el archivo.
2. `figma_navigate` al nodo de la URL (parámetro `node-id`).
3. `figma_get_component_for_development_deep` sobre el frame objetivo — estructura nodo por nodo:
   jerarquía, auto-layout, padding, gap, tamaños, constraints, texto, fills, strokes, efectos.
4. `figma_get_variables` / `figma_get_token_values` / `figma_get_text_styles` — tokens reales
   (color, tipografía, espaciado) en vez de valores crudos.
5. `figma_capture_screenshot` del frame — referencia visual para el QA posterior.
6. **Repetir para cada breakpoint que pida la tarea**: como mínimo **mobile y desktop**; tablet si el
   diseño lo especifica. Si solo existe un breakpoint en Figma, dilo — no inventes el otro.

**Salida obligatoria: un Design Spec** con, por breakpoint y por elemento: ancho de contenedor,
padding/margins, gap, tipografía (familia, tamaño, peso, line-height, letter-spacing), colores como
token, tamaños de imagen/aspect-ratio, estados (hover/focus/disabled/vacío) y comportamiento
responsive entre breakpoints.

Si **no hay Figma**, dilo explícitamente en el plan y marca la tarea como no-visual; no la trates como
pixel-perfect. Si además la tarea lleva UI y no hay captura ni documento de dirección visual, salvo que el proyecto declare `uiux.mode: off`, **propón** UI/UX Pro Max con el bloque 🎨 de `skills/uiux-pro/SKILL.md` y **espera la respuesta**; solo con un sí sigue ese skill (nunca lo corras por tu cuenta). Con un no, sigue como hasta ahora.

---

### Paso 3 — Mapeo del proyecto

Antes de proponer nada, entiende dónde vas a trabajar. **Delega el escaneo al `explorer` (rol)** —
obligatorio: te devuelve el mapa y las convenciones ya resumidos, sin volcarte los archivos. Un listado
de tema en el contexto son miles de tokens que desplazan el requerimiento y el plan.

- **Proyecto Shopify** → aplica el módulo Shopify: lista `sections/ snippets/ blocks/ assets/ layout/
  templates/ locales/ config/`; lee `layout/theme.liquid`, 2–3 secciones representativas y
  `config/settings_schema.json`. Registra base del tema (Horizon/Dawn/custom), metodología CSS, patrón
  de JS (Web Components), plantillas JSON vs liquid, y convenciones propias del tema.
- **Cualquier otro stack** → detecta framework, convenciones, entry points, sistema de estilos, tests.

Guarda esto como **Project Context** para toda la sesión. Si ya lo escaneaste en esta sesión, dilo en
una línea y no lo repitas: `↩ Uso el Project Context ya cargado en esta sesión.`

**Reuse-first.** Busca lo que ya existe y podría resolver la tarea antes de pensar en código nuevo
(`rules/eden-component-strategy-rules.md`). Lo que encuentres alimenta el plan.

---

### Paso 4 — Artefactos del proyecto: fundamentos y sitemap

Dos artefactos que viven a nivel de proyecto, no de tarea. **Se validan en cada ignición**; si faltan,
se proponen antes de planear, porque el plan se apoya en ellos.

#### 4A — Fundamentos de diseño

**Bloqueante para cualquier tarea visual.** Un proyecto sin fundamentos obliga a estimar valores en
cada tarea, y entonces "pixel-perfect" no significa nada.

Comprueba los cuatro artefactos de fundamentos:

```bash
ls docs/design-system.md .claude/project-config.json 2>/dev/null
grep -rnE "(eden|fl)-fundaments" CLAUDE.md docs/design-system.md .claude/project-config.json 2>/dev/null
```

| Estado | Qué haces |
|---|---|
| **No existen** (típicamente la primera ignición del proyecto) | **Ejecuta `create-fundaments`**: entra al Figma, extrae el design system completo y lo integra al proyecto. Se hace **antes** de planear la tarea — el plan se apoya en esos tokens. |
| **Incompletos** (falta alguno de los cuatro, o no hay marcador) | `create-fundaments` completa solo lo que falta. |
| **El Figma cambió** desde el marcador de sincronización | `create-fundaments --refresh`: reporta el diff de tokens y deja que el dev decida antes de escribir. |
| **Completos y sincronizados** | Una línea y sigues: `↩ Fundamentos vigentes ({fecha}) — sigo.` |

Avísale al dev antes de arrancar la creación — es trabajo que no estaba en el ticket:

> El proyecto todavía no tiene fundamentos de diseño. Antes de planear la tarea los levanto del Figma
> e integro el design system al proyecto (`create-fundaments`). Son unos minutos y a partir de ahí
> ninguna tarea vuelve a estimar valores. ¿Le doy?

Si el dev prefiere no hacerlo ahora, **se sigue con la tarea pero se declara en el plan** que las
medidas salen directo del Figma de esta tarea y que el proyecto sigue sin fundamentos.

Si la tarea **no tiene componente visual**, se valida igual pero no bloquea: se reporta y se sigue.

#### 4B — Sitemap de la tienda

El sitemap dice qué páginas y secciones componen la tienda, de qué nodo de Figma sale cada una
(NODE-SECTION) y cuáles ya están construidas. Es lo que permite ubicar la tarea dentro del proyecto en
vez de tratarla como una isla.

```bash
ls docs/sitemap.md 2>/dev/null
grep -rnE "(eden|fl)-sitemap" docs/sitemap.md .claude/project-config.json 2>/dev/null
```

| Estado | Qué haces |
|---|---|
| **No existe** | Propón `create-sitemap`. **No bloquea una tarea puntual**: si el dev prefiere seguir, se sigue y se anota en el plan. Sí conviene tenerlo cuando el proyecto es una tienda entera o varias páginas. |
| **Existe** | **Ubica la tarea en él**: qué NODE-SECTION toca, en qué páginas aparece esa sección (blast radius real), y cuál es su estado. Eso alimenta el plan y las unidades de trabajo. |
| **Existe pero desactualizado** (el Figma cambió, o el tema avanzó) | Propón `create-sitemap --refresh`. |

Cuando el sitemap existe, **el plan cita el NODE-SECTION** de lo que se va a tocar: es la forma de que
el reviewer sepa exactamente qué nodo de Figma corresponde a cada cambio.

#### 4C — Fuente de diseño y anti-slop

Si la tarea toca UI o textos que llegan al usuario final, lee
`${CLAUDE_PLUGIN_ROOT}/rules/on-demand/eden-antislop-rules.md` y busca la **fuente de diseño** (Figma,
captura, imagen o documento de dirección). Con fuente, solo aplica la capa funcional. Sin fuente, aplica
`antislop.mode`: con `ask`, la pregunta 🧹 de la regla entra en la pausa del Paso 5 y se espera la
respuesta. Queda en el plan como una línea (Paso 8).

---

### Paso 5 — Preguntas al dev (una sola pausa)

Agrupa **todo** lo que necesitas preguntar en **una sola intervención**, no en cinco paradas:

- Ambigüedades y contradicciones del ticket.
- **De dónde sale la rama** (obligatorio, nunca se asume — ver Paso 6).
- Breakpoints a cubrir si Figma no lo deja claro.
- Cualquier decisión de producto que no te corresponde tomar.
- Si no hay fuente de diseño y `antislop.mode` es `ask`: el bloque 🧹 de la regla anti-slop (4C).

---

### Paso 6 — Rama

**La rama base SIEMPRE se pregunta.** Nunca se deduce ni se asume `main`/`develop`.

Si hay perfil activo con `git.default_base_hint`, **se propone esa** (p. ej.
`development`, donde se construye todo mientras las ramas de release están protegidas). Proponer no es asumir:
el dev sigue confirmando.

Muestra las ramas candidatas (`git branch -a`, marcando la actual) y espera respuesta. Luego:

```bash
git fetch origin
git switch <base-elegida> && git pull --ff-only
git switch -c <tipo>/<ticket-id>-<slug>
git config branch.<rama>.ticket-url "<url-del-ticket>"
```

Convención de nombres y trailers en `references/branching.md`.

**Prohibido sin autorización explícita del dev:** commitear o pushear a una rama protegida, y **abrir
un PR contra `main` o `develop`**. `turnoff-task` abre el PR, y solo tras confirmación.

---

### Paso 7 — Orquestación

El **orquestador** clasifica el trabajo y decide quién lo ejecuta. Criterios completos y matriz de
enrutamiento en `references/orchestration.md`. Resumen:

| Complejidad | Señales | Ejecución |
|---|---|---|
| **S — trivial** | 1 archivo, sin schema, sin diseño nuevo | Directo, sin subagentes |
| **M — acotada** | 1 sección/componente, diseño con Figma claro, schema aditivo | `implementer` + `design-auditor` en loop |
| **L — compuesta** | Varias secciones/páginas, o varias subtareas independientes | Un `implementer` por unidad, en paralelo; `reviewer` al final |
| **XL — riesgo alto** | Toca código compartido, migraciones, o alcance difuso | Se parte en subtareas y se re-valida el alcance con el dev antes de tocar nada |

El orquestador **no escribe código**: reparte, integra y verifica. Cada unidad que delega lleva alcance
cerrado, archivos permitidos y criterio de aceptación. El especialista de cada unidad se resuelve por rol
con el roster del stack, y las unidades del `implementer` se parten según la tabla "Propiedad de
archivos" del roster, para que dos unidades en paralelo nunca compartan archivos.

---

### Paso 8 — Plan de implementación

Redacta el plan **en español**, con esta estructura:

```
🚀 PLAN DE IGNICIÓN — {ticket-id} · {título}

📌 Objetivo
   {una frase}

📋 Requerimientos (del ticket)
   1. …
   2. …

🧩 Subtareas detectadas
   - [{id}] {título} — {estado} → unidad de trabajo #{n}

🧱 Fundamentos de diseño
   {✅ vigentes ({fecha}) | 🆕 creados en esta ignición ({n} tokens) | ⚠️ el proyecto sigue sin
    fundamentos — las medidas salen solo del Figma de esta tarea}

🗺️ Sitemap
   NODE-SECTION: {page/section} · Figma mobile {node-id} / desktop {node-id}
   Estado actual: {✅ built | 🔧 needs-work | ♻️ reusable | 🆕 to-build}
   También aparece en: {otras páginas — blast radius}
   {o: ⚠️ el proyecto no tiene sitemap}

🎨 Design Spec (Figma)
   Mobile  → {medidas clave}
   Desktop → {medidas clave}
   Tokens  → {los que se usan}
   ⚠️ {huecos o diferencias entre breakpoints}

🧹 Anti-slop: funcional · estética {sí|no} ({motivo})

🧠 Memoria
   {lo relevante que ya sabíamos: hechos, gotchas, episodios parecidos · o "sin memoria previa"}

🔍 Reuse-first — qué ya existe
   {componentes/secciones reutilizables encontrados y por qué sirven o no}

🛠️ Unidades de trabajo (orquestación)
   #1 {qué} · complejidad {S/M/L} · archivos {…} · ejecuta {directo | {rol} → {agente del roster}}
      test: {baseline visual + spec de código} · acepta cuando {los tests están en verde}
   #2 …

🛡️ Superficie
   Entra:     {datos externos que recibe} | nada
   Sale:      {dónde se pinta o envía cada dato, y en qué contexto}
   Quién:     {permisos requeridos} | público
   Secretos:  {tokens o claves que toca} | ninguno
   Terceros:  {scripts, librerías o apps nuevas} | ninguno
   {Si la superficie no es cero: cómo se protege cada punto — `rules/eden-security-rules.md`}

🌿 Git
   Base: {rama-base confirmada} → Nueva: {tipo}/{ticket}-{slug}

⚠️ Riesgos / blast radius
   {qué más consume lo que vamos a tocar y por qué es seguro}

❓ Pendiente de decisión
   {lo que sigue sin resolver, si queda algo}

⏱️ Estimación: {…}
```

El bloque `🛡️ Superficie` es obligatorio (`rules/eden-security-rules.md`): si las cinco respuestas son
"nada/ninguno", se dice "superficie cero"; si no, el plan explica cómo se protege cada punto, y las
unidades de trabajo siguen la sección de seguridad del módulo del stack.

**Espera la aprobación explícita del dev.** Sin un "dale / ok / apruebo", no se implementa.

---

### Paso 9 — Poner la tarea en marcha

Con el plan aprobado, y **sin publicar ningún comentario**:

1. **Mover a `in_progress`** (`task.move`), resolviendo el nombre real con `tracker.statuses`; si no
   está declarado, usa el habitual del tracker y, si no coincide con el tablero, pregunta cuál
   corresponde en vez de adivinar. Nunca se completa ni se cierra un ticket.
2. **Time tracking**: `time.start` si el `time_provider` lo ofrece (Asana no tiene cronómetro por
   MCP); si no, **dilo en una línea** y guarda la hora de inicio en el checkpoint para que
   `turnoff-task` la reporte. Si el `time_provider` es `smg-hub` y el ticket es de Asana, el tiempo
   se carga al cierre con `create-time-entry` usando `externalLinkUrl` = permalink de Asana (o con el
   pasos de `time.add` de `rules/eden-tracker-rules.md`).
3. Escribe `.claude/checkpoint.md` con el plan aprobado, la rama, las unidades y el Design Spec — es lo
   que permite reanudar y lo que `turnoff-task` leerá para verificar completitud.

---

### Paso 10 — Implementar

Aquí se construye. El orquestador ejecuta el plan aprobado, unidad por unidad
(`references/orchestration.md`).

**Por cada unidad de trabajo:**

1. **Test primero (🔴)** — `test-visual baseline` desde el Design Spec y `test-code spec` desde el
   requerimiento. Se corren y deben fallar (`rules/eden-testing-rules.md`).
2. **Ejecuta** — directo si es S; con el `implementer` (rol) que el roster asigna a esos archivos si es
   M o mayor, entregándole el alcance
   cerrado: qué, dónde (lista de archivos), con qué (Design Spec y tokens), **el test que debe poner en
   verde** como criterio de aceptación, y qué NO hacer.
2. **Paraleliza** solo unidades cuyos archivos no se cruzan (tabla "Propiedad de archivos" del
   roster); si dos tocan el mismo archivo, van en serie.
3. **Verifica el resultado.** El reporte de un agente es una afirmación, no una verificación: revisa el
   diff tú mismo antes de darlo por bueno.
4. **Loop de diseño** en las unidades visuales: implementar → el `design-auditor` (rol) mide contra el Design
   Spec → corregir → volver a medir, hasta que no haya diferencias. El dev no debería ver un resultado
   que todavía no pasó ese loop.
5. **Actualiza el checkpoint y descarga contexto al cerrar cada unidad** (`/eden:context offload`): qué
   se hizo, qué archivos, qué decisiones, qué quedó — a `.claude/context/unit-{n}-{slug}.md`. Después,
   en el contexto vivo queda una línea. Es lo que permite encadenar cinco unidades sin comprimir.
   **Nada se suelta sin haberlo escrito.**

**Se detiene y se pregunta** si el alcance real resultó mayor que el planeado, si hay que tocar algo
compartido cuyo blast radius no es aceptable, si el diseño y el ticket se contradicen, o si aparece una
decisión de producto. Detenerse cuesta minutos; adivinar cuesta un rollback.

**Al terminar, el trabajo queda en la rama sin commitear.** No commitees, no pushees, no abras PRs y no
comentes en el tracker: eso es `turnoff-task`, y solo con la confirmación del dev.

---

### Salida final del skill

```
✅ IGNICIÓN COMPLETA — {ticket-id}
   Rama:      {tipo}/{ticket}-{slug}  (base: {base})
   Diseño:    {n} frames extraídos ({breakpoints})
   Implementado: {n}/{n} unidades
     #1 {qué} — ✅ {archivos tocados}
     #2 {qué} — ⚠️ {qué quedó pendiente y por qué}
   Sin commitear · sin comentarios en el tracker
   Siguiente: `/eden:turnoff-task` para auditar, commitear y cerrar
```

Si alguna unidad quedó incompleta o bloqueada, **se dice aquí**, con lo que falta. Un resumen optimista
que no coincide con el código cuesta más que uno incómodo.
