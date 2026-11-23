# Cerebros de proyecto — Eden (Graphify + Obsidian)

La memoria de cuatro capas (`eden-memory-rules.md`) resolvió **qué recordamos**. Los cerebros resuelven
lo siguiente: **cómo se consulta lo recordado sin leerlo entero**, y cómo se conecta con el código real
en vez de quedar como notas sueltas.

Un cerebro no es una carpeta de apuntes. Es **tres capas que se responden entre sí**:

| Capa | Qué es | Quién la escribe | ¿Se versiona? |
|---|---|---|---|
| **Grafo de código** | `graphify-out/graph.json` — nodos y relaciones reales del repo | **Graphify, automático** | No — se regenera |
| **Vault semántico** | Notas en Obsidian: memoria de 4 capas, decisiones, diseño, episodios | **Nosotros, a mano** | **Sí** |
| **Memoria de trabajo** | `.claude/checkpoint.md` y `.claude/context/` | El flujo, durante la tarea | No |

La de arriba dice **qué hay**; la del medio, **qué significa y por qué**; la de abajo, **qué estamos
haciendo ahora**. Un cerebro sin la del medio es un linter caro. Uno sin la de arriba es un blog.

---

## La regla que mantiene el cerebro vivo: generado vs curado

**Nunca se mezclan en la misma carpeta.**

- Lo **generado** (`brain/code/`, `graphify-out/`) es desechable: se borra y se reconstruye con un
  comando. No se edita a mano **jamás** — la siguiente reconstrucción se lo lleva.
- Lo **curado** (todo lo demás del vault) es el trabajo real: lo escribimos nosotros, entra en el PR y
  sobrevive a cualquier reconstrucción.

Si alguien edita una nota generada, ese trabajo está muerto y no lo sabe. Por eso van separadas y por
eso lo generado se ignora en git.

---

## Los dos ámbitos — espejan la memoria del kit

```
~/.claude/eden-brain/                       CEREBRO PERSONAL
├── me/ semantic/ procedural/               lo general (tu forma de trabajar, hechos de plataforma)
└── projects/{proyecto}/                    lo de cada cliente (curado) + code/ (Graphify) + design/

~/.claude/eden-teams/{equipo}/              CEREBRO DE EQUIPO (opcional, repo git privado compartido)
└── projects/{proyecto}/                    lo que el equipo sabe de ese proyecto
```

**Nada personal se escribe en el repo del cliente**: ni notas, ni grafo exportado, ni caché de diseño.
Lo que Graphify deja en el repo (`graphify-out/`) se ignora en `.git/info/exclude`, nunca en el
`.gitignore` del cliente. Un `.claude/brain/` de versiones anteriores se avisa y se migra con
`/eden:brain migrate-vault`.

Misma precedencia y misma disciplina que `eden-memory-rules.md`:

- **Lo del proyecto se escribe solo**, en su carpeta del cerebro personal (y, si el proyecto está en un
  equipo, el equipo lo lee de `~/.claude/eden-teams/`). Es de ese cliente: el recall nunca lo lleva a la
  sesión de otro proyecto.
- **Lo global también se escribe solo**, pero solo lo verificado o dicho por el dev (`confidence: alta`).
  Con 40+ tiendas, un caso particular promovido a regla general se propaga a todas: lo que es de un solo
  cliente se queda en su proyecto. El dev puede volver a aprobar cada nota con
  `learning.global_writes: "inbox"`.
- **El cerebro global no contiene código de clientes.** Contiene hechos, procedimientos y patrones. Si
  una nota global necesita citar código, cita el **proyecto y la ruta**, no el contenido.

El cerebro global tiene una nota por proyecto que enlaza al local. No lo absorbe: lo **apunta**.

---

## Los wikilinks son la sustancia, no la decoración

Un `[[enlace]]` es lo único que convierte notas sueltas en un cerebro. Sin ellos, Obsidian es una
carpeta con vista bonita.

- **Toda nota enlaza a lo que toca**: el episodio enlaza al hecho semántico que produjo; el hecho
  enlaza al proyecto donde se verificó; la decisión enlaza a los nodos de código que afecta.
- **Se enlaza aunque la nota destino no exista todavía.** Un `[[enlace]]` roto no es un error: es una
  nota pendiente, y Obsidian los lista. Es la mejor cola de trabajo que da el sistema.
- **Enlazar el vault curado con el generado es el punto de todo esto.** Una decisión que enlaza a
  `[[code/checkout-service]]` hace que, al abrir ese nodo, aparezca *por qué* está así. Eso es lo que
  ninguna de las dos mitades da por separado.

---

## Cuándo se consulta el cerebro — y en qué orden

El cerebro **sustituye lecturas, no las acompaña**. Si se consulta y además se lee todo, no sirvió de
nada. Antes de mandar a un agente a leer medio repo (`eden-context-rules.md`), el orden es:

1. **`graphify query "..." --budget N`** — ¿lo responde el grafo? Es una respuesta acotada en tokens en
   vez de un volcado.
2. **El vault** — ¿ya lo sabíamos? Un hecho semántico o un episodio puede ahorrar la investigación
   entera.
3. **Delegar la lectura a un agente**, como hasta ahora.

Y para blast radius (`eden-component-strategy-rules.md`, `eden-wordpress-rules.md`):

```bash
graphify affected "{lo que se va a tocar}" --depth 2
```

**`affected` se SUMA al grep, no lo sustituye.** El grafo encuentra relaciones reales que el texto no
ve; el grep encuentra cosas que el extractor no modeló. Y en WordPress sigue haciendo falta la tercera:
`wp db search`, porque parte del sitio no está en el repo ni en el grafo. **Las tres, o el blast radius
está incompleto** — y un blast radius incompleto presentado como completo es peor que no medirlo.

---

## Qué extrae de verdad — medido, no supuesto

Graphify tiene **dos pasadas** y no dan lo mismo. Esto se verificó contra `graphifyy 0.8.30`
(2026-09-09) y hay que saberlo antes de prometer nada:

| Pasada | Coste | Qué extrae |
|---|---|---|
| **AST** (`graphify update`) | Barata, **sin LLM** | Solo lenguajes soportados: `.py .js .ts .php .go .java .rb .html .json .md(superficial)` |
| **Semántica** (`/graphify`, o `GEMINI_API_KEY`/`GOOGLE_API_KEY`) | Cara, con LLM | Relaciones que el AST no ve, y **es la única que entiende docs y markdown de verdad** |

Lo que eso significa por plataforma:

| | `affected` sirve | Nota |
|---|---|---|
| **WordPress** | **Sí** — `.php` está soportado | Es donde más rinde: hooks, includes y llamadas reales |
| **Shopify** | **Limitado** — `.liquid` **no** está soportado | Solo se extraen su `.js`, `.json` y `.css`. Para las relaciones de Liquid **sigue mandando el grep** |
| **docs/ y memoria** | Solo con pasada semántica | Con `update` a secas, el markdown queda superficial |

**Consecuencia práctica: en Shopify, `graphify affected` no sustituye nada.** Aporta sobre el JS y los
JSON de plantilla, y ya. El grep sigue siendo la fuente principal, exactamente como antes.

Y una trampa comprobada: **lo que se indexa de más ahoga el grafo.** En una prueba sobre este mismo kit,
1147 de 1149 aristas eran `contains` de archivos de configuración JSON — ruido estructural que enterró
lo poco útil que había. Por eso las exclusiones se declaran, no se dejan al azar: `.obsidian/`,
`_templates/`, `brain/code/`, `node_modules/`, `vendor/`, y el core y los plugins de terceros en WP.

---

## Higiene — un grafo desactualizado miente

Es el riesgo real de este sistema. Una nota vieja se nota vieja; **un grafo viejo parece actual y
responde con seguridad sobre código que ya no existe**.

- El grafo se reconstruye cuando el código cambia: `graphify update <path>` (barato, sin LLM), por hook
  o por `watch`.
- **Cada consulta al grafo declara cuándo se construyó.** Si el grafo es más viejo que el último commit
  que toca lo que se pregunta, **se dice** y se verifica contra el repo antes de decidir nada.
- Si el grafo y la realidad se contradicen, **gana la realidad**: se reconstruye el grafo, no se ajusta
  la conclusión.
- Las notas curadas llevan su fecha de verificación, igual que en `eden-memory-rules.md`. Lo que lleva
  mucho sin confirmarse se marca como dudoso.

**Lo que reporta el grafo es una afirmación, no una verificación** — igual que lo que reporta un agente
(`eden-model-strategy-rules.md`). Se comprueba antes de construir encima.

---

## Aprendizaje automático — el cerebro aprende de cada sesión

Además de lo que se escribe a mano, el cerebro **aprende solo**, con los hooks del plugin Eden
(`hooks/hooks.json`, script `${CLAUDE_PLUGIN_ROOT}/hooks/eden_brain.py`). **El cerebro es opcional**: si
`~/.claude/eden-brain/` no existe, estos hooks no hacen nada y no crean carpetas; se activa con
`/eden:setup brain`.

| Hook | Qué hace | Coste |
|---|---|---|
| **SessionStart** | Carga en el contexto de la sesión nueva tu forma de trabajar (`me/working-style.md`), el índice del conocimiento global y el del proyecto actual, y la orden de buscar en el cerebro antes de planear | Ninguno: solo lee archivos |
| **UserPromptSubmit** | **Recall en cada mensaje** (`hooks/eden_recall.py`, dentro de `eden-context-watch`): busca con las palabras del mensaje en un índice SQLite FTS5 de las notas (`.state/recall.db`, desechable) y añade hasta 3 notas relacionadas, resumidas, en 3.000 caracteres. Solo del proyecto actual y de `semantic/`/`procedural/` del global: **nunca de otro cliente**. No busca en un «ok» o «dale», no repite una nota en 20 mensajes y salta las marcadas `status: superseded`. Se ajusta con `recall` en `eden-config.json` | ~10 ms, sin modelo |
| **SessionEnd** y **PreCompact** | Condensa la parte nueva de la conversación, la deja en `.state/queue/` y lanza en segundo plano el **destilador** (`claude -p`, modelo `learning.model`, en `--safe-mode`). También corre `graphify update` si el proyecto tiene grafo | Una llamada al modelo por sesión con trabajo real |

El destilador sigue `hooks/distill-prompt.md`: busca correcciones del dev, preferencias, decisiones con su
porqué, gotchas verificados y procedimientos; **deduplica** contra lo que ya existe; y propone notas
enlazadas con `source: auto`, `session` y `confidence`. Las sesiones triviales (menos de
`learning.min_user_messages` mensajes del dev o sin herramientas) no se destilan.

**El modelo propone, el código escribe.** El destilador solo lee: devuelve cada nota en un bloque
`=== EDEN NOTE ===` y termina con `=== EDEN RESULT: … ===`. `eden_brain.py` valida cada destino y ruta
(solo el cerebro del proyecto, `semantic/`, `procedural/` y `me/working-style.md` del global, nada de
`..` ni rutas absolutas), revisa secretos y escribe.
**Una sesión solo sale de la cola cuando sus notas se escribieron**: un código de salida 0 sin bloque de
resultado no cuenta como éxito. Las sesiones largas se parten en tramos de `learning.max_condensed_chars`
en vez de perder su parte media, y una sesión en un worktree aprende en el repo principal.

**Dónde escribe — la regla de los dos ámbitos se mantiene:**

- **Lo del proyecto, directo** a `~/.claude/eden-brain/projects/{proyecto}/`. **Nunca crea archivos en el
  repo de un cliente.**
- **Lo general, directo al global.** Tu forma de trabajar va a `me/working-style.md` y los hechos de
  una plataforma a `semantic/` o `procedural/`, sin preguntar. Solo entra lo verificado o dicho por el
  dev; lo de un solo cliente se queda en su proyecto. Una nota que resulte falsa se corrige o se borra a
  mano. Con `learning.global_writes: "inbox"` en `eden-config.json`, lo general vuelve a esperar tu sí en
  `/eden:brain inbox`.

**Úsalo en cada tarea.** Al arrancar, la sesión recibe el índice del cerebro; antes de planear o tocar
algo, busca en él (Grep por el tema, la herramienta o el error) y lee lo que aplique. Lo que aprenda se
guarda solo al cerrar: recordar no necesita permiso.

Lo aprendido automáticamente es **memoria, no verdad**: la sesión que lo lee lo trata como contexto, lo
verifica contra el repo antes de decidir con él y, si resulta falso, se corrige o se borra. Se apaga con
`learning.enabled: false` en `eden-config.json` (o `/eden:brain learn off`), y su estado se ve con
`/eden:brain learn`.

**Privacidad antes de encolar.** Los secretos (con los patrones del guardián de commits, más cabeceras
`Authorization`, JWT y variables `SECRET=`/`TOKEN=`) se sustituyen por `[REDACTED:tipo]`, y lo que el dev
marque `<private>…</private>` por `[PRIVATE]`, **antes** de que la sesión llegue a la cola o al modelo.
Los proyectos y comandos de `learning.exclude` no se aprenden. Tras cada destilado, las notas nuevas se
revisan otra vez: la que conserve un secreto va a `.state/quarantine/` y no entra al vault.

**Sin CLI con sesión, no se pierde nada.** El destilador en segundo plano necesita el CLI `claude` con
sesión iniciada (`claude auth status`). Si falla por eso, se registra el motivo, se deja de reintentar
durante una hora, el inicio de sesión lo avisa en una línea y `/eden:brain learn now` destila la cola
**dentro de la sesión**, con el sí del dev. Lo que no se destila en 30 días (`learning.queue_max_age_days`)
caduca y se avisa.

---

## Qué NO va al cerebro

- **Secretos, tokens, credenciales, datos personales de clientes.** Nunca, en ninguna capa. Un vault es
  texto plano y se sincroniza.
- Lo que ya está en el código, en `docs/` o en git: **se enlaza, no se copia**. Una copia se
  desincroniza y acaba mintiendo.
- Resúmenes de cosas que no se entendieron. Un resumen equivocado en el cerebro se propaga a todo lo que
  venga después.
- Notas generadas editadas a mano (ver arriba).
- El grafo en el repo: `graphify-out/` y `brain/code/` van al `.gitignore`. Se reconstruyen.

---

## Relación con el resto del kit

| Regla | Qué cambia |
|---|---|
| `eden-memory-rules.md` | Las cuatro capas **no cambian**. Cambia dónde viven: la memoria del proyecto pasa a `~/.claude/eden-brain/projects/{proyecto}/`, fuera del repo, navegable y enlazable. `/eden:brain migrate-vault` copia lo que hubiera en un `.claude/brain/` antiguo. |
| `eden-context-rules.md` | Consultar el grafo pasa a ser **el primer intento** antes de delegar una lectura grande. La regla de "punteros, no contenido" se cumple sola: una consulta al grafo devuelve un puntero. |
| `eden-component-strategy-rules.md` | `graphify affected` se suma como fuente de blast radius. No sustituye al grep. |
| `eden-model-strategy-rules.md` | Sin cambios: consultar el grafo es traer datos, así que lo hacen los agentes o el skill, y el orquestador recibe la conclusión. |

Lo opera `/eden:brain`. Nada de esto se activa solo.
