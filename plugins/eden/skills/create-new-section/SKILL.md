---
name: create-new-section
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:create-new-section` o lo pide de forma explícita e inequívoca. NO lo actives porque se
  hable de crear una sección, un componente o un bloque: si no lo pidió por su nombre, no se usa. —
  Qué hace cuando SÍ se invoca: construye UNA sección nueva, de punta a punta y por sí solo, sin
  necesidad del ciclo completo de ignición. Pide la URL del ticket (Asana, SMG Hub o ClickUp) y la del
  Figma si existen, además de lo que el dev quiera aportar, recorre la escalera reuse-first antes de escribir
  nada, extrae el Design Spec por breakpoint, implementa siguiendo los patrones del proyecto y verifica
  el resultado 1:1 contra el diseño. No commitea ni pushea.
argument-hint: "[url-del-ticket] [| url-figma] [| qué sección y cualquier detalle útil]"
disable-model-invocation: true
---

## Create New Section — construir una sección nueva

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre.

Argumento recibido: `$ARGUMENTS`

Este skill es para cuando **solo hace falta una sección**, sin arrancar el ciclo completo de una tarea.
Es autónomo: recolecta su propio contexto, planea, construye y verifica.

> **Idioma:** al dev, en español. Todo lo que quede escrito —código, clases, settings, docs— en inglés.

**Lo que NO hace:** commitear, pushear, abrir PRs ni comentar en el tracker. Al terminar, el trabajo queda
en la rama para que `turnoff-task` lo cierre.

**Testing — test-first, y nada se entrega sin test** (`rules/eden-testing-rules.md`). El criterio de
aceptación se escribe **antes** que el código: del Figma sale el baseline visual (`test-visual
baseline`) y del requerimiento salen los tests de comportamiento (`test-code spec`). Ambos deben
**fallar primero** — un test que pasa antes de implementar no mide nada. Después se implementa hasta
verde.


**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). La sesión principal
decide, verifica y habla con el dev; **el trabajo de traer datos o producir cambios se delega a agentes
(nivel `fast`)**, por rol: `explorer` (escanear e inventariar), `design-extractor` (Design Spec), `implementer`
(escribir), `design-auditor` (medir), `reviewer` (revisar). Los agentes se resuelven por rol con el roster del stack del proyecto
(`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`); si el stack no tiene roster, se usa
`teams/_generic/roster.md`. Lo que reporta un agente
es una afirmación: se verifica antes de darlo por bueno.


**Stack — antes de nada, saber en qué plataforma estás** (`rules/eden-stack-rules.md`). Lee
`project.stack` de `.claude/project-config.json`. Lo que aquí se llama "sección" no es lo mismo en cada
plataforma, y el módulo correspondiente es de lectura obligatoria:

| Stack | Módulo | Qué es una sección |
|---|---|---|
| **shopify** | `rules/shopify/eden-shopify-rules.md` | Una section/block de Liquid |
| **wordpress** | `rules/wordpress/eden-wordpress-rules.md` **+ el sabor** de `flavors/{wordpress.flavor}.md` | Pattern o bloque (FSE) · template part (clásico) · widget/plantilla (builder) · componente del front (headless) |
| otro | el núcleo + las convenciones del repo | Lo que el proyecto llame así |

Qué agente cumple cada rol (`explorer`, `implementer`, `reviewer`…) no lo dice esta tabla: lo dice el
roster del stack (`teams/{stack}/roster.md`); si el stack no tiene roster, `teams/_generic/roster.md`.

**En WordPress, si `wordpress.flavor` no está declarado, se pregunta antes de escribir código** — o se
propone correr `/eden:wp-setup`. Construir un bloque en un proyecto de tema clásico es trabajo tirado.


---

### Paso 1 — Recolectar el contexto (una sola pregunta)

Pide en **una sola intervención** lo que falte del argumento:

```
Para construir la sección necesito lo que tengas a mano — lo que no haya, lo trabajo sin ello:

1. URL del ticket (Asana, SMG Hub o ClickUp)  → {si la hay, leo requerimientos y subtareas}
2. URL del Figma (con node-id) → {si la hay, mido el diseño en vez de estimarlo}
3. ¿Qué sección es y dónde va? → página/plantilla donde se monta
4. Cualquier cosa que quieras aportar: referencias, comportamiento esperado, casos borde,
   restricciones, lo que ya intentaste, o qué NO quieres que haga.
```

Lo que el dev aporte en el punto 4 **vale tanto como el ticket**: es el contexto que ninguna
herramienta puede darte. Si aporta algo que contradice el Figma o el ticket, se saca a la luz y se
pregunta — no se elige en silencio.

**Con ticket** → léelo con `task.read` + `task.comments` + `task.subtasks` (adaptador en
`rules/eden-tracker-rules.md`); ver `ignition-task/references/tracker.md`.
**Sin ticket ni Figma** → se construye igual, pero **se declara explícitamente** que las medidas salen
de lo que el dev describió, no de un diseño medido. No se trata como pixel-perfect.

---

### Paso 2 — Diseño: medir, no estimar

Si la tarea viene de `/eden:w2shopify`, el Design Spec **ya existe**: es la medición del sitio en
`.claude/context/w2s/{sitio}/` (mismo formato, por breakpoint); úsala como la fuente de diseño y no la
re-estimes. Si además hay Figma, Figma manda.

Si hay Figma, **delega la extracción al `design-extractor` (rol)** y descarga el resultado a
`.claude/context/design-spec-{sección}.md` (`rules/eden-context-rules.md`). El procedimiento completo
está en `ignition-task/references/figma-extraction.md`. **Caché primero**
(`rules/on-demand/eden-design-cache-rules.md`): lo ya medido y sin cambios en Figma no se vuelve a leer,
y lo que cambió se le reporta al dev.
Mínimo: `figma_navigate` al nodo → `figma_get_component_for_development_deep` →
`figma_get_variables` / `figma_get_text_styles` → `figma_capture_screenshot`, **por cada breakpoint**
(mobile y desktop como mínimo).

Sale un **Design Spec** con números por elemento: contenedor, paddings, gaps, tipografía completa,
colores como token, imágenes y estados.

Si el proyecto tiene **fundamentos** (`docs/design-system.md`), los tokens salen de ahí. Si no los
tiene, dilo — y si el dev quiere, `create-fundaments` los levanta primero.

**Fuente de diseño y anti-slop.** Si la sección lleva UI o textos al usuario final, lee
`${CLAUDE_PLUGIN_ROOT}/rules/on-demand/eden-antislop-rules.md`. Sin Figma, captura, imagen ni documento
de dirección, primero salvo que el proyecto declare `uiux.mode: off`, **propón** UI/UX Pro Max con el bloque 🎨 de `skills/uiux-pro/SKILL.md` y **espera la respuesta**; solo con un sí sigue ese skill (nunca lo corras por tu cuenta). Con un no, sigue como hasta ahora; después aplica `antislop.mode`: con `ask`, muestra el bloque 🧹 de la regla y espera la respuesta.

**Animación.** Si la unidad incluye una animación que no sea una transición simple de hover o foco (un menú que se abre, un hero animado, un slider, apariciones al hacer scroll, texto animado) o toca una animación que ya existe, esa parte va al **rol `motion`** ([`teams/motion/roster.md`](../../teams/motion/roster.md), líder `/eden:motion`) y sigue [`rules/eden-motion-rules.md`](../../rules/eden-motion-rules.md): escalera de técnicas, solo `transform`/`opacity`, LCP visible, CLS 0, `prefers-reduced-motion` y tokens de movimiento. El plan declara el escalón; una librería de animación nueva es un sí aparte del dev.
Queda en la propuesta (Paso 4) como `🧹 Anti-slop: funcional · estética {sí|no} ({motivo})`.

---

### Paso 3 — Escalera reuse-first (antes de escribir una línea)

**Que el skill se llame "create" no significa que haya que crear.** Recorre la escalera de
`rules/eden-component-strategy-rules.md` y **detente en el primer escalón que resuelva**:

1. ¿Una sección/bloque existente ya lo hace, configurándola? → no hace falta código.
2. ¿Un preset o una combinación de opciones ya soportada?
3. ¿Se llega agregando settings (aditivos, **con default neutro**)?
4. ¿Código mínimo acotado a esta sección?
5. Sección nueva — **último recurso**.

```bash
ls sections blocks snippets 2>/dev/null
grep -rn "{palabra-clave-de-la-sección}" --include="*.liquid" --include="*.json" . | head -20
```

Si caes en el escalón 5 duplicando una sección parecida, la copia lleva **su propio nombre, su propio
`type` de schema, su propio namespace de clases y sus propios assets**. El original y todo lo que lo
consume quedan intactos.

Si el proyecto tiene `docs/sitemap.md`, mira si la sección ya está mapeada: puede estar marcada como
♻️ reusable con una base ya identificada.

---

### Paso 4 — Proponer y esperar el visto bueno

```
🧩 NUEVA SECCIÓN — {nombre}

Qué es           {una frase}
Dónde va         {página/plantilla}
Escalón          {1–5} — {por qué no bastó el anterior}
Base             {sección que se reutiliza o duplica, o "desde cero"}

Diseño           Mobile {medidas clave} · Desktop {medidas clave}
Tokens           {los que se usan}
🧹 Anti-slop: funcional · estética {sí|no} ({motivo})
{⚠️ huecos del diseño o diferencias entre breakpoints}

Archivos         {los que se crean o tocan — lista cerrada}
Settings         {nuevos, con su default neutro}
Traducciones     {claves nuevas}
Blast radius     {qué más se ve afectado, o "ninguno"}

🛡️ Superficie
   Entra:     {datos externos: settings, metafields, params} | nada
   Sale:      {dónde se pinta cada dato y en qué contexto}
   Quién:     {permisos} | público
   Secretos:  {…} | ninguno
   Terceros:  {…} | ninguno
   {Si no es superficie cero: cómo se protege cada punto}

❓ {lo que sigue sin resolverse}

¿Lo construyo así?
```

La superficie se declara según `rules/eden-security-rules.md`; la construcción sigue la sección de
seguridad del módulo del stack.

**Sin aprobación no se escribe código.** Si el trabajo es grande o toca varias secciones, dilo: puede
que corresponda `ignition-task`, no este skill.

---

### Paso 5 — Rama

Si el dev ya está en una rama de trabajo, se sigue en ella. Si no:

> ¿Creo rama para esto? Si sí, **¿desde dónde sale?** (nunca lo asumo)

Convención en `ignition-task/references/branching.md`. **Nunca se trabaja directo sobre una rama
protegida.**

---

### Paso 5b — Tests primero (🔴)

**Antes de escribir la sección**, con el plan ya aprobado:

1. `test-visual baseline` — del Design Spec sale el baseline versionado: colores (y su token),
   tipografía completa, paddings, margins, gaps, dimensiones, animaciones y su `prefers-reduced-motion`,
   por cada breakpoint.
2. `test-code spec` — los tests del comportamiento que la sección debe tener.
3. **Se corren y deben fallar.** Todavía no hay nada implementado: si algo pasa, el test no mide nada.

Esto es lo que hace que el diseño mande sobre la implementación, y no al revés.

---

### Paso 6 — Construir

Directo si es pequeño; con el `implementer` (rol) si tiene volumen, entregándole alcance cerrado, lista de
archivos, Design Spec y criterio de aceptación.

Innegociables mientras se construye (`rules/eden-code-style-rules.md`, `eden-quality-rules.md`):

- **Los patrones del proyecto mandan** — dónde viven los estilos, cómo se registran los componentes,
  cómo se nombran los archivos. No tus preferencias.
- Colores y tipografía **por tokens**, nunca hardcodeados. Mobile-first.
- Texto visible **por el sistema de traducciones**, nunca hardcodeado.
- Todo setting nuevo con **default que reproduce el comportamiento actual**.
- Semántica, foco visible, teclado, labels, `alt` descriptivo, contraste AA — desde el primer intento.
- Imágenes con dimensiones, `srcset` y `loading="lazy"` bajo el fold.

---

### Paso 7 — Verificar

1. **Tests en verde (🟢)** — `test-visual run` y `test-code run`. Se corrigen los rojos y se vuelve a
   correr hasta que no quede ninguno. Si hace falta el microscopio para entender un fallo,
   `attention-detail` da el informe detallado; `test-visual` es el semáforo.
2. **Validación del stack** — Theme Check en Shopify; `php -l` + PHPCS (estándar `WordPress`) sobre
   nuestras rutas en WordPress; linter/tests donde aplique.
3. **Consola limpia** en la página donde se monta.
4. **Estados**: vacío, sin imagen, texto largo, un ítem, muchos ítems.
5. **Sin residuos**: `console.log`, `debugger`, código comentado, archivos de prueba.

---

### Paso 8 — Documentar y reportar

- Sección con schema, campos de datos o lógica no obvia → doc en `docs/` (plantilla `_TEMPLATE.md`).
- Si el proyecto tiene `docs/sitemap.md`, actualiza el estado de esa sección.

```
✅ SECCIÓN LISTA — {nombre}
   Escalón reuse-first: {n} — {qué se reutilizó}
   Archivos:   {lista}
   Settings:   {n} nuevos (defaults neutros)
   Diseño:     {✅ 1:1 mobile y desktop | diferencias pendientes}
   Validación: {salida real}
   Pendiente:  {lo que quedó fuera, o "nada"}
   Sin commitear — `/eden:turnoff-task` para auditar y cerrar
```
