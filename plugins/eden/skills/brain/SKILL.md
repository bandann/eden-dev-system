---
name: brain
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:brain` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable del
  cerebro, del grafo, de Obsidian o de recordar algo, ni porque exista un `brain/` o un `graphify-out/`:
  si no lo pidió por su nombre, no se usa. (Los demás comandos del kit consultan el cerebro por su
  cuenta en sus hitos — eso es parte de su flujo.) —
  Qué hace cuando SÍ se invoca: gestiona los cerebros de proyecto — el grafo de código de Graphify más
  el vault de Obsidian con la memoria de cuatro capas. `init` crea el cerebro y migra la memoria que
  hubiera; `build` construye o actualiza el grafo; `query` responde desde el grafo con presupuesto de
  tokens en vez de leer archivos; `affected` da blast radius por relaciones reales; `note` escribe una
  nota enlazada; `sync` reexporta el grafo al vault; `promote` propone subir un hecho local a global;
  `status` dice si el grafo está desactualizado; `open` abre el vault en Obsidian; `inbox` revisa la
  bandeja si el dev pidió aprobar lo general; `learn` muestra y controla el aprendizaje automático.
argument-hint: "[init | build | query | affected | note | sync | promote | status | doctor | open | inbox | learn | recall | team | migrate-vault] [| argumento]"
disable-model-invocation: true
---

## Eden Brain — el cerebro del proyecto

Argumento recibido: `$ARGUMENTS`

Un cerebro son **tres capas**: el grafo de código (Graphify, generado), el vault semántico (Obsidian,
curado) y la memoria de trabajo (`checkpoint.md`, efímera). La regla completa está en
`rules/eden-brain-rules.md` — **léela antes de operar**, sobre todo la separación generado/curado.

> **Idioma:** al dev, en español. Todo lo que quede escrito en el vault —notas, títulos, tags— en
> **inglés**, como el resto de lo que el kit escribe (`eden-workflow-rules.md`).

**Lo que NO hace:** commitear ni pushear. El cerebro global se escribe solo (lo verificado); `note` y
`promote` escriben en él cuando el dev los invoca.

> **Aprendizaje automático.** Además de lo que se escribe a mano, el cerebro aprende solo: al cerrar
> cada sesión con trabajo real, un destilador en segundo plano lee la conversación y escribe lo que vale
> la pena recordar. Lo del proyecto va directo a su cerebro y lo general verificado (tu forma de trabajar,
> hechos de una plataforma) directo al global, sin preguntar. Con `learning.global_writes: "inbox"` lo
> general vuelve a esperar tu sí en `inbox`. Al iniciar
> sesión, lo aprendido se carga solo. Cómo funciona: `rules/eden-brain-rules.md` § Aprendizaje
> automático. Se controla con `learn`.

---

### Dónde vive cada cosa

```
~/.claude/eden-brain/                          PERSONAL — tu cerebro. Se escribe solo (lo verificado).
~/.claude/eden-brain/projects/{proyecto}/      lo tuyo de cada proyecto (curado)
~/.claude/eden-brain/projects/{proyecto}/code/ GENERADO por Graphify. Desechable.
~/.claude/eden-brain/projects/{proyecto}/design/ CACHÉ del Figma medido (eden_design.py)
~/.claude/eden-teams/{equipo}/projects/{proyecto}/  COMPARTIDO — lo que el equipo sabe del proyecto (`team`)
{proyecto}/graphify-out/graph.json             EL GRAFO. Desechable. Ignorado en .git/info/exclude
```

**Nada personal se escribe en el repo del cliente.** `{proyecto}` es el nombre que sale del remoto de git
(`owner-repo`), así que dos clones del mismo repo comparten carpeta. Lo único que Graphify deja dentro del
repo (`graphify-out/`) se ignora en `.git/info/exclude`, que es local y no se versiona: nunca se toca el
`.gitignore` del cliente. Un repo con un `.claude/brain/` de una versión anterior se avisa al iniciar
sesión; `migrate-vault` copia sus notas al cerebro.

La caché de diseño (`rules/on-demand/eden-design-cache-rules.md`) se consulta con
`python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_design.py" status`: qué archivos de Figma y qué secciones
tiene guardadas, y cuándo se comprobó cada archivo por última vez. `/eden:brain status` lo incluye.

---

### `init` — preparar el cerebro de este proyecto (fuera del repo)

1. **Mira qué hay ya.** La carpeta del proyecto es `~/.claude/eden-brain/projects/{proyecto}/`
   (`python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" pending` y `project_slug` dan el nombre). Si
   existe, **no la rehace**: reporta el estado y ofrece completar lo que falte.
2. **Copia la plantilla** `brain/project/` del kit a esa carpeta, sustituyendo `{{PROJECT}}`, `{{STACK}}` y
   `{{DATE}}`. **Nunca dentro del repo del cliente.**
3. Si el repo tiene un `.claude/brain/` antiguo, ofrece `migrate-vault`.
4. Añade `graphify-out/`, `.claude/context/` y `.claude/checkpoint.md` a **`.git/info/exclude`** del repo
   (local, no se versiona). El `.gitignore` del cliente no se toca.
5. Si el equipo tiene cerebro compartido, ofrece `team link`.
6. Ofrece encadenar `build`.

Si el **cerebro global** no existe (`~/.claude/eden-brain/`), se crea desde `brain/global/` — pero
**vacío de contenido**: los hechos globales llegan con el aprendizaje automático o con `promote`.

---

### `build` — construir o actualizar el grafo

**Primera vez** (caro, usa backend LLM para nombrar comunidades): se **propone** y se espera el OK,
diciendo qué va a indexar y cuánto pesa el corpus.

```bash
graphify <path> --obsidian --obsidian-dir ~/.claude/eden-brain/projects/{proyecto}/code
```

**Actualizaciones** (baratas, sin LLM):

```bash
graphify update <path>
graphify export obsidian --dir ~/.claude/eden-brain/projects/{proyecto}/code
```

Qué se indexa —el dev lo confirma la primera vez y queda escrito en `project-config.json`:

- **El código del proyecto**, siempre.
- **`docs/`** — sí: `design-system.md` y `sitemap.md` consultables junto al código es medio sentido de
  esto.
- **`brain/memory/` y `brain/decisions/`** — sí, para que un episodio salga en la misma consulta que el
  código que lo causó.
- **Nunca**: `node_modules/`, `vendor/`, el core de WordPress, plugins de terceros, `uploads/`,
  `wp-config.php`, `.env`, dumps de base de datos, **`.obsidian/`, `_templates/`, `brain/code/` y
  `brain/design/`** (los specs en JSON de la caché de diseño solo meterían ruido en el grafo).
  Se declara la exclusión, no se asume.
  > Lo que se indexa de más **ahoga el grafo**: en una prueba real, unos pocos archivos de configuración
  > JSON generaron 1147 de 1149 aristas y enterraron todo lo demás.

⚠️ **`update` (barato, sin LLM) solo hace extracción AST**, y eso cubre los lenguajes soportados —
**no** entiende markdown de verdad. Para que `docs/` y la memoria aporten algo hace falta la **pasada
semántica**: el skill `/graphify` completo, o un `GEMINI_API_KEY`/`GOOGLE_API_KEY` configurado. Si no
lo hay, **se dice** y se indexa solo código; no se promete un grafo de documentación que no existe.

Al terminar: **`sync`** y actualizar la fecha del grafo en el índice del vault.

---

### `query` — preguntar al grafo en vez de leer archivos

```bash
graphify query "{la pregunta}" --budget 2000 --graph graphify-out/graph.json
```

Es el **primer intento** antes de delegar una lectura grande (`eden-context-rules.md`): devuelve una
respuesta acotada en tokens en vez de un volcado.

Tres reglas al usarlo:

1. **Se declara la antigüedad del grafo** en la respuesta. Si el grafo es más viejo que el último commit
   que toca lo preguntado, **se dice y se verifica contra el repo** antes de decidir nada.
2. **Lo que responde el grafo es una afirmación, no una verificación.** Si de ahí sale una decisión, se
   comprueba en el código.
3. **Si el grafo no lo sabe, se delega la lectura como siempre.** No se fuerza una respuesta pobre por
   haber preguntado.

Complementos: `graphify explain "X"` (qué es un nodo y sus vecinos) y `graphify path "A" "B"` (cómo se
conectan dos cosas).

---

### `affected` — blast radius por relaciones reales

```bash
graphify affected "{lo que se va a tocar}" --depth 2 --graph graphify-out/graph.json
```

**Se SUMA al grep, no lo sustituye.** Son fuentes distintas y cada una ve lo que la otra no.

⚠️ **Cuánto aporta depende de la plataforma** (verificado, ver `rules/eden-brain-rules.md`): en
**WordPress** rinde —`.php` está soportado y salen hooks, includes y llamadas reales—; en **Shopify**
aporta poco, porque **`.liquid` no está soportado** y solo se extraen su `.js`, `.json` y `.css`. Ahí el
grep sigue siendo la fuente principal. **Se dice cuál fue la cobertura real**, no se presenta el grafo
como si lo hubiera visto todo.

| Fuente | Ve | No ve |
|---|---|---|
| `graphify affected` | Relaciones reales (llamadas, imports, renders) | Lo que el extractor no modeló |
| `grep` | Coincidencias de texto, strings, clases CSS | Relaciones indirectas |
| `wp db search` *(WordPress)* | **Contenido publicado en la base de datos** | Nada del repo |

**En WordPress las tres son obligatorias**: parte del sitio no está ni en el repo ni en el grafo
(`rules/wordpress/eden-wordpress-rules.md`). Un blast radius incompleto presentado como completo es peor
que no medirlo.

El reporte dice **qué fuente encontró cada cosa**, para que se sepa qué cobertura hubo de verdad.

---

### `note` — escribir en el cerebro

Crea una nota desde su plantilla (`_templates/`), en la capa que toque, **y la enlaza**.

- **Semántica** → un hecho verificado, con su fuente y dónde se confirmó.
- **Procedural** → un procedimiento que funcionó. Si `times_used` llega a **3**, se avisa: eso ya
  debería ser un skill o una regla, no una nota.
- **Episódica** → un caso con **desenlace**. Sin desenlace no se guarda todavía.
- **Decisión** → qué se decidió, por qué, y **qué se descartó**.

Lo que hace útil la nota, y sin lo cual no se escribe:

- **Enlaces.** A la nota de la que sale, al proyecto, y a los nodos de `code/` que toca. Una nota sin
  enlaces es una nota que el grafo no conecta con nada: existe pero nadie la encuentra.
- **Fecha de verificación.**
- **Nada de secretos ni datos personales.**

**No se guarda lo que ya está en el repo, en `docs/` o en git**: se enlaza. Una copia se desincroniza y
acaba mintiendo.

---

### `sync` — reexportar el grafo al vault

```bash
graphify export obsidian --dir ~/.claude/eden-brain/projects/{proyecto}/code
```

Regenera `brain/code/`. **Sobrescribe**: por eso ahí no se edita nunca a mano. Los enlaces desde las
notas curadas hacia `[[code/...]]` sobreviven porque apuntan por nombre.

---

### `promote` — de local a global

Un hecho sube cuando **se confirmó en dos o más proyectos**, o cuando es **del stack y no del cliente**.

```
🧠 Para el cerebro global — ¿lo promuevo?
   "{el hecho}"
   Visto en: {proyecto A}, {proyecto B}
   Aplicaría a: todos los proyectos {Shopify | WordPress | …}
   Enlazaría con: [[{nota global existente}]]
```

**Nada llega al cerebro global sin el sí del dev.** Con 40+ tiendas, un caso particular promovido a
regla general se propaga a todas.

Al promover: la nota global cita **en qué proyectos se verificó** y la local queda enlazada a ella. El
código del cliente **no viaja**: se cita proyecto y ruta.

---

### `status` — ¿el cerebro miente?

```bash
git log -1 --format=%cd                     # último commit
stat -c %y graphify-out/graph.json          # última construcción del grafo
graphify check-update .                     # ¿hay re-extracción pendiente?
```

Reporta:

- **Antigüedad del grafo** vs el último commit. Si el código se movió después, el grafo **miente con
  seguridad** — es el riesgo real de este sistema, porque un grafo viejo no *parece* viejo.
- Cuántas notas hay por capa, y cuántas llevan mucho sin verificarse.
- **Enlaces sin resolver**: la cola de trabajo del vault.
- Notas huérfanas (sin ningún enlace): candidatas a enlazar o a borrar.

---

### `doctor` — comprobaciones del entorno

- `graphify --version` y que el `graph.json` parsee.
- Que Obsidian esté instalado y que el vault tenga su `.obsidian/`.
- **Que la `description` del skill `graphify` siga siendo la de invocación explícita.**
  ⚠️ `graphify install` la **sobrescribe** en cada reinstalación o upgrade del paquete, y la suya es un
  cajón de sastre que se auto-activa con cualquier pregunta sobre el código — justo lo que el kit
  prohíbe. Si se revirtió, se reaplica y **se le dice al dev**.
- Que lo generado esté en `.gitignore` y que no haya `graph.json` ni dumps versionados.

---

### `open` — abrir el vault

```bash
start "" "obsidian://open?path={ruta absoluta del vault}"
```

Si Obsidian no está instalado, se dice — **y no se bloquea nada**: el vault son archivos markdown y
Claude los lee y escribe igual. La app es para que **tú** veas el grafo.

Obsidian solo abre por URI un vault que ya conoce. Si nunca se abrió esa carpeta como vault, el enlace
no hace nada: se le dice al dev que la abra una vez con **Open folder as vault** y se da la ruta.

---

### `inbox` — aprobar lo que el cerebro aprendió solo (opcional)

Solo hay propuestas si el dev puso `learning.global_writes: "inbox"` en `~/.claude/eden-config.json`
(por defecto lo general se escribe directo), o si quedaron de una versión anterior. Lista
`~/.claude/eden-brain/inbox/*.md`. Para cada propuesta
muestra en **una línea**: tipo (`working-style` · `semantic` · `procedural`), acción (`new` · `update` ·
`confirm`), la afirmación, y de qué proyecto y sesión salió.

```
🧠 BANDEJA — {n} pendientes

 1. [working-style · new]  "Wants plans approved before any file is written" — eden-kit · 2026-10-22
 2. [semantic · update]    "Theme Check misses unclosed {{ }} …" → [[shopify-theme-check-…]] — store-x
 3. [procedural · new]     "Rename a kit prefix safely: dry-run script, then git mv" — eden-kit

¿Qué hago? (p. ej. "aprueba 1 y 3, descarta 2", "todas", "edita 2: …")
```

Y aplica lo que el dev diga, **nada sin su respuesta**:

| Decisión | Qué se hace |
|---|---|
| **Aprobar** `working-style` | Se integra como viñeta en `me/working-style.md` (sin duplicar: si ya hay una equivalente, se mejora esa) y se borra de la bandeja |
| **Aprobar** `semantic` / `procedural` · `new` | Se mueve a `semantic/` o `procedural/` quitando `kind`, `action` y la línea **Proposal**; se enlaza desde el MOC que corresponda |
| **Aprobar** `update` / `confirm` | Se aplica el cambio o la nueva línea de verificación a la nota enlazada, y se borra la propuesta |
| **Editar** | Se reescribe con lo que diga el dev y se aprueba |
| **Descartar** | Se mueve a `inbox/_rejected/` (no se borra: el destilador lo consulta para no volver a proponerlo) |

Si la bandeja está vacía, se dice en una línea y se termina.

---

### `team` — el cerebro compartido del equipo

Un repo git **privado** que el equipo comparte, además del cerebro personal de cada uno
(`scripts/eden_team.py`). Se clona en `~/.claude/eden-teams/{equipo}/` y guarda
`projects/{proyecto}/`: lo que el equipo sabe de cada proyecto. Un proyecto está en el equipo si esa
carpeta existe; como el nombre sale del remoto de git, todos los que trabajan en ese repo caen en la
misma. Tu forma de trabajar y tus notas personales **nunca** van al equipo.

| `team …` | Qué hace | Script |
|---|---|---|
| `join {url}` | Clona el cerebro del equipo y lo registra en `eden-config.json` (`teams`) | `eden_team.py join {url} [--name N]` |
| `init {url}` | Igual, para un repo **vacío** recién creado: le pone `README.md` y `projects/`, y hace push | `eden_team.py init {url} [--name N]` |
| `link` | Añade **este** proyecto al equipo (`projects/{proyecto}/` con su índice), commit y push | `eden_team.py link [--team N] --cwd {proyecto}` |
| `status` | Equipos, sus clones, último pull, proyectos y si este está enlazado | `eden_team.py status --cwd {proyecto}` |
| `pull` | Trae lo nuevo de todos los equipos (el inicio de sesión ya lo hace en segundo plano, cada 10 min como mucho) | `eden_team.py pull` |
| `doctor` | Remoto alcanzable con tus credenciales, árbol limpio, rama con upstream | `eden_team.py doctor` |
| `leave {equipo}` | Lo quita de la configuración; el clon se queda en disco | `eden_team.py leave {equipo}` |

Todos con `python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_team.py" …`. Quien invoca `/eden:brain team init`,
`join` o `link` está pidiendo ese clone, commit y push: se ejecuta y se reporta el resultado. Git corre
sin pedir contraseña (`GIT_TERMINAL_PROMPT=0`): el acceso es el de las credenciales de git del dev. Una
URL con credenciales dentro se rechaza.

Qué ya hace (fase 1): al iniciar sesión se listan las notas del equipo de este proyecto y el recall de
cada mensaje busca también en ellas. Escribir en el equipo automáticamente al destilar llega en la fase 2;
mientras tanto, una nota se comparte copiándola a `projects/{proyecto}/` del clon y haciendo commit y push.

---

### `migrate-vault` — sacar del repo un cerebro antiguo

Las versiones anteriores a 4.1 creaban `.claude/brain/` dentro del repo del cliente. Ya no se usa.
`python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" migrate-vault {proyecto}` **copia** sus notas (y la
caché de diseño sin capturas) a `~/.claude/eden-brain/projects/{proyecto}/`; una nota que ya existe no se
pisa (la copia queda con `-from-vault`). No borra nada: quitar la carpeta del repo del cliente es un
commit en ese repo y lo decide el dev.

---

### `recall` — lo que el cerebro le recuerda a cada mensaje

En cada mensaje del dev, el hook `eden-context-watch` busca en las notas las que comparten palabras con lo que
pidió y las añade al contexto, resumidas (`hooks/eden_recall.py`). Solo del proyecto actual (tu carpeta y la del equipo) y del
conocimiento general (`semantic/`, `procedural/`): nunca de otro cliente.

| `recall …` | Qué hace |
|---|---|
| *(sin argumento)* o `status` | `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_recall.py" status`: si está activo, cuántas notas hay indexadas y los ajustes |
| `search {texto}` | `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_recall.py" search "{texto}" --cwd {proyecto}`: qué notas saldrían para ese mensaje, con las palabras que coincidieron y su puntuación. Para entender por qué algo salió o no |
| `index` | Rehace el índice desde cero (`.state/recall.db` es desechable; las notas markdown son la fuente) |
| `off` / `on` | Pone `recall.enabled` en `~/.claude/eden-config.json` |

Ajustes en `recall` de `eden-config.json`: `top_k` (3), `max_chars` (3000), `repeat_after` (20 mensajes),
`min_terms` (2 palabras en común como mínimo). Una nota con `status: superseded` no se recuerda.

---

### `learn` — ver y controlar el aprendizaje automático

Sin argumento, reporta el estado leyendo `~/.claude/eden-brain/.state/`:

- Si el cerebro está activo: existe `~/.claude/eden-brain/` (si no, se dice que es opcional y se ofrece
  `/eden:setup brain`) y `learning.enabled` está activo en `eden-config.json`. Los hooks vienen con el
  plugin (`${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json`); si `~/.claude/settings.json` todavía tiene hooks de
  Eden de la instalación antigua, se ofrece `/eden:setup migrate` para no duplicarlos.
- La cola y su salud: `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" pending` devuelve las
  sesiones que esperan (proyecto, rama, evento, fecha) y el estado del destilador
  (`.state/distill_status.json`: último éxito y último error clasificado `auth` · `timeout` ·
  `permission` · `format` · `other`). Con `auth`, el CLI `claude` no tiene sesión: se dice, con
  `claude auth login` y con `learn now`. Una sesión solo sale de la cola cuando sus notas **se
  escribieron de verdad**; un `format` o `permission` la deja esperando, con su salida en
  `.state/logs/{archivo}.out.md`.
- Las sesiones largas se parten en **tramos** (`…-p1.md`, `…-p2.md`) de `learning.max_condensed_chars`;
  cada tramo se destila aparte.
- **Recuperar** una sesión entera (p. ej. una que se perdió): `eden_brain.py requeue {transcript.jsonl} [cwd]`
  la vuelve a poner en la cola desde el principio, en tramos, sin lanzar el destilador.
- Las últimas líneas de `.state/logs/eden-brain.log` (destiladas, saltadas por triviales, aplazadas,
  caducadas, en cuarentena) y si hay notas en `.state/quarantine/`.

Con argumento:

| `learn …` | Qué hace |
|---|---|
| `off` / `on` | Pone `learning.enabled` en `eden-config.json` |
| `now` | Destila ya lo que haya en la cola (abajo) |
| `model {sonnet\|haiku\|opus}` | Cambia `learning.model` (solo para el CLI `claude`; otro proveedor o modelo: `/eden:setup ai`) |

#### `learn now` — destilar ya, con el respaldo dentro de la sesión

1. `pending` y se le muestra al dev: cuántas sesiones, de qué proyectos y ramas. **Se pregunta antes de
   procesar**: destilar consume uso de la cuenta.
2. Si `claude auth status` dice que hay sesión, se usa el camino de siempre:
   `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" distill {la más antigua}` (procesa toda la cola).
3. **Si no hay sesión en el CLI**, se destila dentro de esta sesión, de la más antigua a la más
   reciente, **en lotes de 5**:
   - Por cada sesión, un agente `eden:brain-distiller` (solo lectura) con la salida de
     `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" prompt {archivo}` como encargo. El agente
     **no escribe**: devuelve los bloques `=== EDEN NOTE ===` y la línea `=== EDEN RESULT: … ===`.
     Hasta 5 en paralelo **solo si son de proyectos distintos** (sus índices se pisarían).
   - Su respuesta, **tal cual**, se guarda con Write en
     `~/.claude/eden-brain/.state/replies/{nombre del archivo de la cola}` y se aplica con
     `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py" apply {archivo} {respuesta}`: valida cada ruta
     (dentro de `project_brain`, o `semantic/`, `procedural/` y `me/working-style.md` del global), manda a `.state/quarantine/` la nota que lleve un
     secreto, escribe el resto y retira la sesión de la cola. Con `ok: false` la sesión **se queda** y se
     dice por qué (`format`, `permission`).
   - Se revisan las rutas de `written` antes de dar el lote por bueno.
   - Tras cada lote: resumen corto (notas nuevas, propuestas en bandeja, cuarentena) y se pregunta si
     seguir con el siguiente.
4. Al final, si hubo propuestas en la bandeja, se ofrece `/eden:brain inbox`.

#### Privacidad — lo que nunca llega a la cola

- **Secretos** (tokens, claves, contraseñas, cabeceras `Authorization`, JWT, credenciales en URLs,
  variables `SECRET=`/`TOKEN=`…) se sustituyen por `[REDACTED:tipo]` al condensar, con los mismos
  patrones del guardián de commits.
- **`<private>…</private>`**: lo que el dev escriba entre esas etiquetas se sustituye por `[PRIVATE]`.
- **Exclusiones**: `learning.exclude.projects` (nombres o rutas con comodines) y
  `learning.exclude.bash_patterns` (comandos que no se registran) en `eden-config.json`, o
  `learning.enabled: false` en el `project-config.json` de un proyecto.
- Las sesiones que no se destilan en `learning.queue_max_age_days` (30) caducan y se avisa una vez.

---

### Reporte

```
🧠 EDEN BRAIN — {modo}

Cerebro   {local: ruta} · {global: ruta}
Grafo     {n} nodos · construido {fecha} · {✅ al día | ⚠️ desactualizado desde {commit}}
Vault     {n} notas — {n} semánticas · {n} procedurales · {n} episódicas · {n} decisiones

{el resultado del modo}

⚠️ Atención
  {grafo viejo, notas dudosas, enlaces sin resolver, lo que no se pudo verificar}

Siguiente
  {qué conviene hacer ahora}
```

**No se maquilla.** Si el grafo está viejo, se dice — la utilidad entera de esto depende de que se pueda
confiar en lo que responde.
