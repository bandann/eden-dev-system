---
name: turnoff-task
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:turnoff-task` o pide de forma explícita e inequívoca cerrar la tarea con el flujo de
  Eden. NO lo actives porque el dev diga que terminó, ni porque pida commitear, pushear o abrir un
  PR, ni porque el trabajo parezca acabado: si no lo pidió por su nombre, no se usa. Ante la duda,
  pregúntale si quiere el cierre Eden en vez de ejecutarlo. — Qué hace cuando SÍ se invoca: cierre
  de tarea de Eden. Verifica que lo pedido está realmente implementado, audita todo lo que cambió
  en la rama (bugs, regresiones, bleed, código muerto, errores de consola, reglas del equipo), valida
  el diseño contra Figma en mobile y desktop, calcula el tiempo trabajado y — solo tras confirmación
  del dev — commitea, pushea la rama y prepara el PR y el comentario de cierre en el tracker (Asana, SMG Hub o ClickUp). Nunca
  abre un PR a main ni a develop sin autorización explícita.
argument-hint: "[nada | url-del-ticket (Asana, SMG Hub o ClickUp) | notas de cierre] [--dual]"
disable-model-invocation: true
---

## Turnoff Task — cierre Eden

Argumento recibido: `$ARGUMENTS`

El cierre no es "hacer commit y push". Es comprobar que lo que se pidió está hecho, que no rompimos
nada, y dejar el rastro para que otro pueda revisarlo sin preguntarte nada.

**Nada se pushea ni se abre como PR sin confirmación explícita del dev.**

**Testing — test-first, y nada se entrega sin test** (`rules/eden-testing-rules.md`). El criterio de
aceptación se escribe **antes** que el código: del Figma sale el baseline visual (`test-visual
baseline`) y del requerimiento salen los tests de comportamiento (`test-code spec`). Ambos deben
**fallar primero** — un test que pasa antes de implementar no mide nada. Después se implementa hasta
verde.


**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). La sesión principal
decide, verifica y habla con el dev; **el trabajo de traer datos o producir cambios se delega a agentes
(nivel `fast`)**, por rol: `explorer` (escanear e inventariar), `design-extractor` (Design Spec), `implementer`
(escribir), `design-auditor` (medir), `reviewer` (revisar el diff), `quality-auditor` (performance,
accesibilidad y SEO). Los agentes se resuelven por rol con el roster del stack del proyecto
(`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`); si el stack no tiene roster, se usa
`teams/_generic/roster.md`. Lo que reporta un agente
es una afirmación: se verifica antes de darlo por bueno.


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


> **Idioma:** **español solo para hablarle al dev** en la consola. Commits, rama, PR y **todos los
> comentarios del tracker**, en **inglés**.

---

### Paso 1 — Recuperar el contexto de la tarea

```bash
git branch --show-current
git config branch.$(git branch --show-current).ticket-url
git status --short
git log --oneline <base>..HEAD
git diff --stat <base>...HEAD
```

Lee `.claude/checkpoint.md` (plan aprobado, unidades de trabajo, Design Spec). Si no hay checkpoint ni
`ticket-url`, pregunta al dev cuál es la tarea y desde qué base salió — sin eso no puedes verificar
completitud ni abrir un PR al destino correcto.

Recupera también el ticket del tracker (`task.read` + `task.comments`, adaptador en
`rules/eden-tracker-rules.md`): puede haber comentarios nuevos que cambiaron el alcance mientras
trabajabas.

---

### Paso 2 — Verificar completitud contra el ticket

Recorre **requerimiento por requerimiento** y **subtarea por subtarea** del plan de ignición, y marca:

```
✅ hecho · ⚠️ parcial · ❌ no hecho · ➖ fuera de alcance (acordado)
```

Un requerimiento sin evidencia (archivo, línea, captura) no está hecho. **Si algo quedó fuera, se
declara** — nunca se cierra una tarea diciendo que está completa cuando no lo está.

---

### Paso 3 — Auditoría del cambio

Sobre **todo** el diff de la rama (`git diff <base>...HEAD`), no solo el último commit. Checklist
completo en `references/audit-checklist.md`. Los bloques:

1. **Funcional** — ¿hace lo que dice? Casos borde, estados vacíos, datos faltantes, errores.
2. **Regresiones y bleed** — ¿qué más consume lo que tocamos? Estilos que se escapan, componentes
   compartidos, defaults de schema que alteran instancias existentes.
3. **Reglas del equipo** — CSS/BEM, Liquid, JS, performance, accesibilidad (WCAG AA) y SEO.
4. **Limpieza** — sin `console.log`, `debugger`, código muerto, TODOs olvidados, archivos de playground
   o pruebas sueltas.
5. **Validación del stack** — Theme Check en Shopify; linters/tests donde aplique.
6. **Consola del navegador** — cero errores en las páginas tocadas.
7. **Seguridad (puerta bloqueante)** — ver abajo.
8. **Anti-slop funcional (puerta bloqueante)** — ver abajo.

**Delega la auditoría al `reviewer` (rol)**, y la parte de performance, accesibilidad y SEO al
`quality-auditor` (rol) — un `git diff` de varios archivos en el contexto es exactamente lo que no debe
entrar. Cada rol lo cumple el agente que asigne el roster del stack. Te devuelve hallazgos con `archivo:línea`; tú los **verificas** en
vez de darlos por buenos. Descarga los hallazgos a `.claude/context/findings-{fecha}.md` y trabaja
sobre la lista de pendientes.

#### Revisión doble a ciegas (opcional)

Una sola revisión puede perderse lo mismo que se le perdió a quien escribió el código. Para el trabajo
de riesgo hay una segunda opinión **independiente**:

- **Cuándo:** si el dev lo pide (`--dual` en el argumento, o "revisión doble"), si el proyecto la pide
  siempre (`review.dual: true` en `.claude/project-config.json`), o —proponiéndolo, no imponiéndolo— si
  la `🛡️ Superficie` del plan toca autenticación, pagos, permisos, datos personales o migraciones.
- **Cómo:** lanza **dos** agentes del rol `reviewer` **en paralelo, en el mismo turno**, con el mismo
  encargo y sin decirle a ninguno que existe el otro. Ninguno edita: solo leen y devuelven hallazgos con
  `archivo:línea`, severidad y evidencia.
- **Cruce** (lo haces tú, en `.claude/context/findings-{fecha}.md`, una fila por hallazgo):

  | Hallazgo | Revisor A | Revisor B | Veredicto |
  |---|---|---|---|
  | lo vieron los dos | ✅ | ✅ | **confirmado** → se arregla |
  | lo vio uno | ✅ | — | **lo verificas tú** en el código; confirmado o descartado, con el porqué |
  | se contradicen | ✅ | ❌ | **lo decides tú** con la evidencia; si la duda importa, se le pregunta al dev |

- **Rondas:** se arreglan los confirmados y se vuelve a lanzar la pareja **solo sobre lo que cambió**.
  Máximo **dos rondas**; lo que siga abierto va al reporte como pendiente, no se esconde.
- En el reporte: `Revisión doble: {n} confirmados · {n} verificados por ti · {n} descartados · {rondas}`.

#### Puerta de seguridad

Además, lanza el rol `security-auditor` (se resuelve por el roster; agente `eden:security-auditor` o el
del stack) sobre el diff de la rama, contrastándolo con el bloque `🛡️ Superficie` del plan
(`rules/eden-security-rules.md`). Misma disciplina: verificas sus hallazgos, no los das por buenos.

- **Crítica o Alta → BLOQUEA** el commit, el push y el PR hasta que se arreglen, o hasta que el dev
  acepte la excepción de forma explícita y en el momento. La excepción **se escribe en el PR**, en la
  sección `Security exceptions` (hallazgo, motivo, quién la aceptó). Nunca se salta en silencio.
- **Media y Baja** se listan en el reporte y en la sección `Security` del PR.
- Si falta una herramienta (gitleaks, semgrep, osv-scanner), no se bloquea: se declara qué no se pudo
  verificar.
- El hook de commit (`eden_guard.py`) bloquea además cualquier secreto en lo que va a commitearse. Si
  salta, se saca el secreto y se rota; no se esquiva.

#### Puerta anti-slop funcional

Si el diff toca UI o textos que llegan al usuario final, lee
`${CLAUDE_PLUGIN_ROOT}/rules/on-demand/eden-antislop-rules.md` y corre las comprobaciones de
`/eden:antislop` (F-1 a F-10) sobre el diff de la rama, a través de los roles `reviewer` y
`design-auditor`. Verificas sus hallazgos, no los das por buenos.

- **Un F marcado como Bloquea → BLOQUEA** el commit, el push y el PR hasta que se arregle, o hasta que
  el dev conceda la excepción de forma explícita y en el momento. La excepción **se escribe en el PR**,
  en `Anti-slop exceptions`. Nunca se salta en silencio.
- Los hallazgos de la **capa estética y de voz** solo se reportan (si esa capa aplicó en la ignición);
  no bloquean.
- Los choques entre el Figma y la capa funcional se le presentan al dev; no se resuelven en silencio.

---

### Paso 4 — Verificación de diseño (si la tarea es visual)

Contra el Design Spec de la ignición, en **mobile y desktop** como mínimo:

- Mide la implementación real (navegador/preview) y compárala con Figma elemento por elemento.
- Usa el `design-auditor` (rol) para el diff; corrige y vuelve a auditar hasta que no haya diferencias.
- Verifica los estados: hover, focus, disabled, vacío, carga.

Si algo no quedó 1:1 y hay una razón, se escribe en el PR y en el comentario del ticket. No se oculta.

---

### Paso 5 — QA en dispositivos

Pregunta al dev qué probó manualmente. Lo que no probó, ofrécete a verificarlo tú en el navegador.
Registra explícitamente **qué se revisó y qué no** — ese registro va al PR.

**Si hay perfil activo, el checklist de handoff sale de él** (el checklist de handoff que declare el
perfil, `qa.*`): anchos concretos, umbrales de PageSpeed, navegadores y el orden por frecuencia real de
bugs (`qa.bug_frequency`), que se revisa primero.
Sin perfil, mobile/tablet/desktop y los breakpoints del proyecto.

---

### Paso 6 — Documentación

- Componentes/secciones nuevos con schema, metafields o lógica no obvia → doc en `docs/`.
- **Si esta tarea creó o actualizó los fundamentos de diseño**, verifica que los cuatro artefactos
  quedaron sincronizados y con su marcador `eden-fundaments` (un legado `fl-fundaments` es válido y se propone migrar a
  `eden-`, nunca se reescribe en silencio): tokens en código, `docs/design-system.md`,
  `.claude/project-config.json` y el bloque del `CLAUDE.md`. Van commiteados en esta rama, y en el PR
  se declara que se integró el design system.
- **Si el proyecto tiene `docs/sitemap.md`**, actualiza el estado de las secciones que esta tarea tocó
  (`🆕 to-build` → `✅ built`, etc.), su ticket y una fila en el change log. Un sitemap con estados
  viejos engaña sobre cuánto falta del proyecto.
- Si el proyecto tiene `CLAUDE.md` y el cambio altera convenciones o arquitectura, actualízalo en esta
  misma rama (nunca directo sobre una rama protegida).

**Reglas de negocio del perfil.** Si hay perfil activo y el cambio toca algo que él regula, se verifica
antes de cerrar. Son las que declare el perfil (`business_rules`), si existen. Lo que más se omite es una
regla que no falla en la página principal sino en otro lugar donde el tema pinta lo mismo (carruseles,
búsqueda, relacionados, carrito). Se listan **todos** los lugares verificados, uno por uno; y lo que
debe llegar al pedido o al email se prueba **end-to-end**.

---

### Paso 6b — Puerta de tests (bloqueante)

**Ninguna tarea se entrega sin test.** Antes de presentar el reporte:

| Test | Cómo | Requisito |
|---|---|---|
| **Visual** | `test-visual run` — y `qa-pixel-perfect` si la tarea fue una página completa | Verde en **todos** los nodos y **todos** los breakpoints |
| **Código** | `test-code run` | Tests, linter, type-check y Theme Check en verde |
| **Actualidad** | `test-code currency` | Nada deprecado en lo que se escribió |

```
🚦 PUERTA DE TESTS

Visual      {n}/{n} asertos ✅   ({n} breakpoints)
Código      {n}/{n} tests ✅ · linter ✅ · Theme Check {n} errores
Actualidad  ✅ verificado con context7 · {n} deprecados en uso (fuera de alcance)

{o bien:}
❌ NO SE PUEDE ENTREGAR
   · {aserto que falla} — {dónde}
   · {test que falla} — {dónde}
```

**Si algo está en rojo, no se cierra la tarea**: se arregla y se vuelve a correr. Si algo **no se pudo
testear**, se declara qué y por qué — nunca se marca como pasado. Un test que nadie corrió da confianza
falsa, que es peor que no tener test.

Y no se toca el baseline para que pase: si el diseño cambió, se re-deriva desde Figma
(`test-visual update`) y el diff se aprueba.

---

### Paso 6c — Sellar lo revisado

Cuando la auditoría, sus arreglos y los tests están en verde, **sella el estado exacto que se revisó**:

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_review.py" stamp
```

Guarda en `.git/eden-review.json` el árbol de lo que hay ahora en la rama (sin tocar el staging). En el
push, el guard compara lo que se sube con ese sello: **si algo cambió después de la revisión, el push se
bloquea** y dice qué archivos. Los commits intermedios son libres (uno por cambio lógico); solo cuenta
lo que llega al remoto. Un push que coincide consume el sello.

- Si después del sello hay que tocar algo (un comentario del dev, un arreglo de último momento), **se
  revisa lo que cambió y se sella de nuevo**. No se esquiva el bloqueo.
- Si el dev decide subirlo sin volver a revisar, es su decisión y se dice en el PR:
  `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_review.py" clear`.

---

### Paso 7 — Confirmación del dev (la pausa obligatoria)

Presenta el reporte y **espera respuesta**. No commitees antes de esto.

```
📋 REPORTE DE CIERRE — {ticket-id} · {título}

✔️ Completitud
   1. {requerimiento} … ✅
   2. {requerimiento} … ⚠️ {por qué}

🔎 Auditoría
   Funcional   {resultado}
   Regresiones {resultado}
   Reglas      {resultado}
   Limpieza    {resultado}
   Validación  {salida del linter/Theme Check, explicada en español}
   Consola     {errores encontrados}

🛡️ Seguridad
   Superficie  {la declarada en el plan · ¿coincide con el diff?}
   Escáneres   {gitleaks / semgrep / osv-scanner: corridos | no instalados}
   Hallazgos   Críticos {n} · Altos {n} (bloquean) · Medios {n} · Bajos {n}
   Excepciones {aceptadas por el dev y escritas en el PR, o "ninguna"}

🧹 Anti-slop
   Fuente      {Figma {nodo} | captura | ninguna} · estética {sí | no}
   Funcional   Bloqueantes {n} · avisos {n} · excepciones: {aceptadas y escritas en el PR, o "ninguna"}
   Estética    {n avisos | no aplicó}

🤖 Supuestos (si la tarea corrió en /eden:go --auto)
   {Q abiertas de .claude/context/questions-{tarea}.md y qué depende de cada una | "ninguno"}

🔏 Sello
   {árbol sellado {hash corto} · la rama lleva exactamente lo revisado}

🚦 Tests
   Visual      {n}/{n} asertos ✅ en {n} breakpoints
   Código      {n}/{n} ✅ · linter ✅ · Theme Check {n} errores
   Actualidad  {✅ | ⚠️ deprecados reportados}
   Sin testear {qué y por qué, o "nada"}

🎨 Diseño vs Figma
   Mobile  {✅ 1:1 | diferencias}
   Desktop {✅ 1:1 | diferencias}

📱 QA
   Probado: {qué y dónde}   ·   Sin probar: {qué}

📦 Cambios
   {n} archivos · {n} commits
   {lista resumida}

⏱️ Tiempo: {inicio} → {fin} = {duración}

🌿 Destino del PR: {rama}  ← ⚠️ requiere tu autorización si es main/develop

¿Confirmas que commiteo, pusheo y abro el PR?
```

---

### Paso 8 — Commit, push y PR

Solo con el "sí" del dev.

1. **Commits** — Conventional Commits en inglés, con trailer `Ticket: <url>`. Un commit por cambio
   lógico. Nunca `.env`, secretos, `node_modules/` ni generados.
2. **Push de la rama de trabajo** — directo está bien. A una rama protegida, **jamás**. Si el guard
   responde que lo que se sube no es lo que se revisó, se vuelve al paso 3 sobre lo que cambió y se
   sella de nuevo (paso 6c).
3. **PR** — título en formato de commit; cuerpo con: qué se hizo, cómo probarlo, checklist de QA,
   capturas mobile/desktop, link a la tarea, lo que quedó fuera, y la sección `Security`
   (con `Security exceptions` si el dev aceptó alguna).
   - **PR contra `main` o `develop` → se pregunta al dev en el momento, aunque ya haya confirmado el
     push.** Son dos autorizaciones distintas.
   - Nunca se mergea solo.

---

### Paso 9 — Cerrar en el tracker

1. **Comentario de cierre en inglés** (`task.comment`). Es el **único** comentario que el flujo
   publica en toda la tarea, **se muestra el borrador completo y se espera el sí del dev antes de
   publicarlo** (en Asana es permanente: no se edita ni se borra; en SMG Hub va `isInternal: true`
   salvo que el dev pida otra cosa), y **describe qué se hizo** — no es un reporte de auditoría ni un
   volcado del QA. Contiene: la descripción del trabajo, lo que quedó fuera, el link del PR y el link
   de preview apuntando a **la página exacta del cambio** (no la home; uno por página tocada). El
   detalle técnico —cómo probarlo, checklist de QA, capturas— vive en el **PR**, no aquí. Plantilla en
   `references/closeout.md`.
2. **Tiempo** — `time.stop` si se arrancó en la ignición, o `time.add` con la duración calculada
   desde la hora del checkpoint, tras confirmarla con el dev. Si la celda del adaptador es "—" (p. ej.
   Asana sin `time_provider`), dilo en una línea y repórtale la duración al dev para que la cargue.
   Con `time_provider: smg-hub` y un ticket de Asana, `create-time-entry` usa `externalLinkUrl` =
   permalink de Asana (pasos de `time.add` en `rules/eden-tracker-rules.md`).
3. **Estado y asignación** — `task.move` al estado lógico `review`, resuelto con `tracker.statuses`.
   Si hay perfil activo, usa lo que declara: p. ej. la tarea va a `review` asignada al rol que declare
   el perfil (`roles.qa`), y **el dev nunca cierra** — cerrar o devolver a In Progress es de ese rol. Un
   ticket **nunca se completa ni se cierra** desde aquí (`done` es solo del lead). Confírmalo con el
   dev en una línea antes de moverla. Sin perfil, pregúntale a qué
   estado la mueve y a quién se asigna: no lo decidas tú.
4. **Cerrar el ciclo de la estimación** — si la tarea tenía estimado (`.claude/context/estimate-*.md`),
   compara **estimado vs real** unidad por unidad. Si la desviación es significativa, guárdala con
   `/eden:memory save`: es lo que hace que la próxima estimación sea mejor. Sin esta comparación, el kit
   estima igual de mal dentro de un año.
5. **Consolidar y limpiar** — `/eden:memory consolidate` y luego `/eden:context close`. Lo consolidado va al
   **cerebro** (`rules/eden-brain-rules.md`), y ahí una nota sin enlaces no sirve: cada episodio enlaza al
   hecho que produjo, y cada decisión a los nodos de código que afecta. Si se tocó bastante código,
   `/eden:brain build` deja el grafo al día — un grafo que se queda en la versión anterior empieza a
   mentir en la siguiente tarea. Primero se destila
   lo que servirá dentro de seis meses; **recién entonces** se limpia `.claude/context/`, que es
   efímero de la tarea. Borrarlo antes de consolidar es tirar lo aprendido. El checkpoint es memoria de **trabajo**: antes
   de borrarlo se destila lo que servirá dentro de seis meses (episodios con desenlace, hechos
   verificados, procedimientos que funcionaron) y se descarta lo que solo valía para esta tarea. Lo
   local se escribe solo; **lo que aplicaría a todos los proyectos se te propone y espera tu sí**.
5. **Checkpoint** — recién entonces, márcalo como finalizado o bórralo. No debe quedar un checkpoint
   obsoleto confundiendo a la siguiente sesión — ni perderse sin consolidar lo aprendido.

---

### Salida final

```
🔌 TAREA APAGADA — {ticket-id}
   Rama:     {rama} → pusheada
   PR:       {url o "pendiente de autorización"}
   Seguridad: {n} críticos/altos · {n} medios/bajos · excepciones: {n}
   Anti-slop: {n} bloqueantes · {n} avisos · excepciones: {n}
   Tracker:  comentario publicado · estado {estado} · {duración} registrada
   Fuera:    {lo que no se hizo, o "nada"}
```
