---
name: go
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:go` o pide de forma explícita e inequívoca que el enrutador del kit elija el comando
  ("eden, ¿qué uso para esto?"). NO lo actives porque el dev describa una tarea, pegue una URL de un ticket (Asana, SMG Hub o ClickUp)
  o de Figma, o parezca no saber qué comando usar: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: es el ENRUTADOR del kit. Lee lo que el dev quiere en lenguaje libre, detecta el
  stack y el estado del proyecto (fundamentos, sitemap, sabor de WP, tarea en curso), elige el skill
  del kit que corresponde —con sus argumentos ya armados y lo que conviene encadenar después— y lo
  PROPONE. No ejecuta nada hasta que el dev dice que sí. Si el skill elegido puede correr sin
  preguntas a mitad del flujo, ofrece delegarlo a un agente enrutador de dominio (`eden-router-*`) para
  no cargar la sesión; si no, lo corre en la sesión principal con todas sus puertas de aprobación.
argument-hint: "[--auto] <qué quieres hacer, en lenguaje libre> [| url-ticket] [| url-figma] [| sección o página] · answers"
disable-model-invocation: true
---

## Eden — el enrutador del kit

Argumento recibido: `$ARGUMENTS`

Un punto de entrada para los 30 comandos del kit. El dev dice **qué quiere**; este skill decide **qué
comando lo hace**, con qué argumentos y en qué orden, y se lo propone. El dev confirma y el comando
corre.

> **Idioma:** al dev, en español. Los argumentos que se le pasan al skill elegido, tal como los
> espera ese skill.

**Modelos:** el enrutamiento es una decisión, así que lo toma la sesión principal — el **orquestador**, nivel
`plan` (**Fable** en Claude Code; si la sesión corre en otro modelo, dilo en una línea, `/model fable`, y sigue).
Las unidades de trabajo van a agentes: **Opus** (`strong`) las complejas, **Sonnet** (`fast`) las acotadas; el
orquestador elige el modelo de cada encargo (`rules/eden-model-strategy-rules.md`). Los agentes `eden-router-*`
ejecutan skills en **modo informe** cuando el dev acepta delegarlos.

### Lo que NO hace

- **No ejecuta nada sin el sí del dev.** Invocar `/eden:go` es pedir una recomendación, no autorizar un
  comando. La autorización llega cuando el dev confirma la propuesta. Desde ese momento, el skill
  elegido cuenta como invocado explícitamente.
- **No se salta las puertas de los skills.** Si el skill elegido pide aprobación del plan, confirmación
  antes de escribir o la rama base, esas preguntas se hacen igual. El enrutador no responde por el dev.
- **No encadena por su cuenta, salvo en `--auto`.** Sin `--auto`, propone la cadena ("después conviene
  `/eden:test-visual`") y cada paso siguiente se confirma otra vez. Con `--auto`, ver "Modo orquestador".
- **No duplica la lógica de los skills.** No mide, no implementa, no audita: elige y delega.

---

### Paso 1 — Entender el pedido

Del `$ARGUMENTS` saca:

| Señal | Ejemplo | Qué indica |
|---|---|---|
| **Verbo** | arrancar, cerrar, crear, modificar, revisar, medir, estimar, registrar, migrar | La familia del skill |
| **Objeto** | tarea, sección, página, diseño, imágenes, tiempo, sitio, memoria | El skill concreto |
| **URLs** | `app.asana.com/…`, `hub.solomediagroup.com/…/tasks/…`, `app.clickup.com/t/…`, `figma.com/design/…?node-id=…`, `pastel…`, una URL del sitio | Los argumentos |
| **Alcance** | "una sección", "la página entera", "todo el sitio" | Distingue `attention-detail` de `qa-pixel-perfect`, `section-mod` de `ignition-task` |
| **Momento** | "empiezo", "ya terminé", "antes de lanzar", "QA del cliente" | La fase del ciclo |
| **Seguridad** | "revisa la seguridad", "audita", "¿es seguro?", "blinda", "secretos", "vulnerabilidades" | `security-check` y su modo (`diff`, `section`, `project`, `secrets`, `deps`); informe delegable a `eden:router-qa` |
| **Anti-slop** | "slop", "se ve genérico", "parece hecho por IA", "revisa los textos/copy", "comentarios de IA", "contraste" | `antislop` y su modo (`section`, `page`, `copy`, `code`, `contrast`); informe delegable a `eden:router-qa` |
| **Dirección visual sin diseño** | "no hay Figma", "propón un diseño", "mejora el diseño", "qué estilo/paleta/tipografía uso", "UI/UX Pro Max" | `uiux-pro` — se **propone** y se ejecuta solo con el sí del dev (nunca en modo informe por agente: necesita consultarle) |
| **Duplicar un sitio en Shopify** | "copia/duplica este sitio en Shopify", "pasa esta web a Shopify", "clona el diseño de esta URL", "w2shopify" | `w2shopify <url…>` — primero confirma el derecho a reproducir el diseño; mide con Playwright y reconstruye en el tema |

Si `$ARGUMENTS` está vacío, muestra el mapa corto de familias (la tabla del Paso 3 resumida en una
línea por familia) y pregunta qué quiere hacer. No adivines.

### Paso 2 — Leer el estado del proyecto (barato, sin agentes)

Lecturas cortas y acotadas. Nada de escanear el repo:

1. **Stack**, en el orden de `rules/eden-stack-rules.md`: lo que diga el dev, luego
   `.claude/project-config.json` → `project.stack`, luego el marcador `<!-- eden-stack: -->` del
   `CLAUDE.md`, y por último la detección por carpetas (`sections/`+`snippets/` → Shopify;
   `wp-content/` o `style.css` con `Theme Name:` → WordPress).
2. **Precondiciones del kit**:
   - ¿Existen `docs/design-system.md` o los fundamentos declarados en `project-config.json`?
   - ¿Existe `docs/sitemap.md`?
   - En WordPress: ¿está declarado `wordpress.flavor`?
3. **Tracker**, en el orden de `rules/eden-tracker-rules.md`: lo que diga el dev, luego la **referencia**
   (una URL de Asana, de SMG Hub o de ClickUp dice dónde vive el ticket; un id que no encaja con
   ningún formato se pregunta), luego `tracker.provider` de `project-config.json`, el perfil y
   `~/.claude/eden-config.json`; por defecto Asana. Se detecta para armar bien los argumentos, no se
   asume ClickUp.
4. **Trabajo en curso**: ¿existe `.claude/checkpoint.md` sin marcar como finalizado? ¿La rama actual
   lleva un ticket (`git config branch.<rama>.ticket-url`)?

Esto no bloquea: sirve para que la propuesta sea correcta. Por ejemplo, si el dev pide
`/eden:create-new-section` y no hay fundamentos, se le dice antes de proponerla.

### Paso 3 — Elegir el skill

Usa la tabla de enrutamiento completa en [`references/routing-table.md`](references/routing-table.md).
Criterios, en este orden:

0. **Primero el stack.** Si el stack tiene líder (`/eden:shopify` hoy; ver la sección "Líderes de
   stack" de la tabla) y el pedido necesita coordinar varias unidades o es un proyecto nuevo u
   onboarding, la ruta es el líder. Si es una sola skill, va directo a ella: las skills ya resuelven
   al equipo del stack por su roster.
1. **Si hay una tarea en curso** (checkpoint abierto) y el pedido encaja en ella, se enruta **dentro de
   esa tarea** (p. ej. "ya terminé" → `turnoff-task`), no a un flujo paralelo.
2. **El skill más chico que resuelve el pedido.** Es la escalera reuse-first aplicada a los comandos:
   no se propone `ignition-task` para un ajuste de una sección que `section-mod` resuelve, ni
   `qa-pixel-perfect` cuando piden medir una sola sección.
3. **Las precondiciones van primero**, pero se proponen, no se imponen. WordPress sin sabor → `wp-setup`
   antes de cualquier `wp-*` o sección. Proyecto sin fundamentos → se avisa, y el dev decide si corre
   `create-fundaments` antes.
4. **Si dos skills encajan igual de bien**, se proponen los dos con la diferencia en una línea y el dev
   elige. No se elige por él.
5. **Si ninguno encaja**, se dice en una línea y se trabaja de forma normal, sin el flujo del kit. No se
   fuerza un skill.

### Paso 4 — Decidir dónde corre

Cada skill de la tabla tiene una columna **Modo**:

| Modo | Significa | Dónde corre |
|---|---|---|
| 🟢 **Delegable** | No pregunta a mitad del flujo y no escribe fuera de `.claude/context/` en el modo pedido | Se **ofrece** delegarlo al `eden-router-*` de su dominio. El dev elige: delegado (la sesión queda liviana) o en línea |
| 🟡 **Hasta la propuesta** | El skill mide y arma una propuesta, y luego pide un sí antes de escribir | El agente corre **hasta la propuesta** y la devuelve. La sesión principal se la muestra al dev y, si dice que sí, **continúa el skill en línea** desde ese paso |
| 🔴 **Solo en línea** | Pide decisiones a mitad del flujo, o escribe en el tracker o en git | Siempre en la sesión principal, con `Skill`. Nunca se delega |

Un subagente no puede preguntarle nada al dev. Por eso lo 🔴 nunca se delega: saltarse una puerta de
aprobación no es una optimización, es romper el kit.

### Paso 5 — Proponer y esperar

Presenta exactamente esto y **detente**:

```
🧭 RUTA PROPUESTA

Entendí: {el pedido en una frase}
Stack: {shopify | wordpress (sabor) | otro} · Tarea en curso: {ticket | ninguna}

▶ /{skill} {argumentos ya armados}
  Por qué este: {una línea — y por qué no el más grande o el más chico}
  Dónde corre: {🟢 delegado a eden-router-{dominio} | 🟡 eden-router-{dominio} hasta la propuesta, luego en línea | 🔴 en línea}

⚠️ Antes: {precondición que falta, si hay — o "nada"}
➜ Después conviene: {/skill siguiente — se confirma aparte}

¿Lo corro así? (sí · en línea · otro skill)
```

Si hay dos candidatos, muestra dos bloques `▶` y pregunta cuál.

### Paso 6 — Ejecutar lo confirmado

- **🔴 o "en línea"** → invoca el skill con la herramienta `Skill` y los argumentos armados. A partir de
  ahí manda ese skill, no este.
- **🟢 delegado** → lanza el agente del dominio con un encargo que tenga las cinco partes de
  `rules/eden-model-strategy-rules.md`:

  ```
  Skill: {nombre} · Modo: {modo del skill, p. ej. run | recall | doctor}
  Argumentos: {los armados}
  Proyecto: {ruta absoluta} · Stack: {…} · Perfil: {… | ninguno}
  Autorizado por el dev en /eden: sí — el skill cuenta como invocado explícitamente.
  Acepta cuando: {resultado observable}
  No hacer: escribir fuera de .claude/context/, escribir en el tracker/Figma/git, preguntar al dev.
  ```

  **Primer o segundo plano lo decide la columna `Plano` de la tabla, no la comodidad.** Un subagente
  en segundo plano pierde la mayoría de las herramientas internas, entre ellas `Agent`, y no tiene
  garantizados los MCP. Todo lo que mide con Figma o Playwright, lee el tracker o lanza un `eden-*` corre en
  **primer plano** (`run_in_background: false`). Solo lo que es lectura local pura (memoria, cerebro,
  contexto) va en segundo plano. Cuando vuelva, **su
  informe es una afirmación, no una verificación**: revisa los números clave antes de dárselos por
  buenos al dev, y muéstrale la conclusión con el puntero al archivo en `.claude/context/`.
- **🟡** → como 🟢, pero con `Modo: hasta-la-propuesta`. Cuando el agente devuelve la propuesta, se le
  muestra al dev tal cual pide el skill ("¿Lo integro así?", "¿Los bajo así?"). Con el sí, se invoca el
  skill en línea con `Skill` indicando que el análisis ya está en `.claude/context/{archivo}` y que
  continúe desde el paso de escritura, sin volver a medir.

### Paso 7 — Después

Si el skill terminó y la tabla indica un siguiente paso natural, se ofrece en una línea
(`➜ ¿Sigo con /eden:test-visual {sección}?`). Una sola oferta; si el dev no la toma, no se insiste.

---

## Reglas

- **Una ruta, con su porqué.** Nunca una lista de diez comandos para que el dev elija.
- **El enrutador no tiene memoria propia.** Si la ruta sale mal ("no, para esto se usa X"), la
  corrección se guarda con `/eden:memory save` y se ajusta `references/routing-table.md` en el repo del
  kit. No se memoriza en silencio.
- **La tabla vive en el repo del kit.** Cuando se agrega un skill al kit, se agrega su fila en
  `references/routing-table.md` en el mismo PR. Un skill sin fila no es enrutable.

---

## Modo orquestador — `/eden:go --auto <tarea>`

Para que el desarrollo no se detenga mientras el dev no está: el orquestador recorre la cadena de skills de
la tarea, **sigue adelante con las dudas que no bloquean** (las deja anotadas para cuando el dev tenga tiempo)
y solo se detiene ante lo bloqueante. Lo activa el dev, por tarea, con `--auto` (o el proyecto con
`go.auto_default: true` en `.claude/project-config.json`). Nunca se activa solo.

**Qué autoriza `--auto`:** todo lo **local y reversible dentro de la rama de trabajo** — leer, planear,
escribir código, correr tests y mediciones, encadenar los skills. **Nada más.** La regla de autorización
(`rules/eden-workflow-rules.md`) sigue intacta para todo lo que sale de la máquina o no se puede deshacer.

### 1 · Arranque

1. Lee el pedido como en el Paso 1 y el estado como en el Paso 2.
2. Arma la **cadena** de skills (de `references/routing-table.md`), p. ej. `ignition-task` → `create-new-section`
   → `test-visual` → `attention-detail` → `turnoff-task` (este, hasta su pausa del Paso 7).
3. Muéstrala **una vez** con lo que va a ser bloqueante, y arranca sin esperar:

```
🤖 MODO AUTÓNOMO — {tarea}
Cadena    {skill} → {skill} → … → turnoff-task (se detiene antes de commitear)
Modelos   orquesta {Fable} · unidades complejas → Opus · acotadas → Sonnet
Preguntas .claude/context/questions-{tarea}.md — respóndelas cuando puedas (/eden:go answers)
Se detiene solo si: {lo bloqueante que ya se ve, o "algo bloqueante aparece"}
```

Las preguntas que los skills hacen **antes de empezar a escribir** y que no se pueden suponer sin riesgo
(la rama base, el sabor de WordPress, el derecho a reproducir un diseño) se hacen **todas juntas al
arrancar**, en un solo bloque; mientras el dev no responde, se avanza en lo que no depende de ellas
(lectura, mapeo, medición).

### 2 · Repartir: Fable decide, Opus y Sonnet hacen

Por cada unidad del plan, el orquestador lanza el agente del rol (roster del stack) con el encargo de cinco
partes y **elige el modelo** según la tabla de `rules/eden-model-strategy-rules.md` (en Claude, el parámetro
`model` del agente: `opus` o `sonnet`), con el motivo en una línea. Unidades con archivos que no se cruzan van
en paralelo. Lo que devuelve un agente **se verifica** antes de seguir.

### 3 · Cada pregunta: ¿bloquea o no?

| ❌ **Bloqueante** — se detiene y espera | ✅ **No bloqueante** — supone, anota y sigue |
|---|---|
| Commit, push, PR, merge | Un texto que el ticket no da (se usa un marcador obvio) |
| Escribir en el tracker, Figma, la tienda o `settings_data` | El nombre de una clase, un archivo, un setting |
| Borrar o sobrescribir algo que no se creó en esta tarea | Un valor que el diseño no define y el proyecto tiene como token |
| Instalar, quitar o actualizar dependencias | Cuál de dos patrones del proyecto seguir (el más usado) |
| Excepciones de seguridad; un hallazgo crítico o alto | Un detalle responsive que el diseño no muestra (mobile-first del proyecto) |
| Una contradicción que cambia el **alcance** o el **resultado** del ticket | El orden de las unidades |
| El derecho a reproducir un diseño (`w2shopify`), usar UI/UX Pro Max | Copy de mensajes de error o estados vacíos (marcador) |

**Ante la duda, es bloqueante.** El supuesto no bloqueante es siempre **el más reversible**: el que sigue el
patrón del proyecto, no inventa requisitos y se cambia tocando pocos archivos.

### 4 · El tablero de preguntas

Cada pregunta no bloqueante va a `.claude/context/questions-{tarea}.md`:

```markdown
## Q{n} · {la pregunta, en una línea}   — abierta
- Supuse: {lo que se hizo} · por qué: {una línea}
- Depende: {archivos / unidades}
- Si la respuesta es otra: {qué se rehace}
```

Al terminar cada fase, una sola línea: `🤖 {fase} lista · {n} preguntas abiertas (no bloquean)`. Sin pausa.

### 5 · Cuando el dev responde — `/eden:go answers`

(o simplemente escribe sus respuestas, "Q2: sí, Q3: el azul"). Por cada respuesta: si coincide con el
supuesto, la pregunta se cierra; si no, el orquestador **rehace solo lo que dependía de ella** (por agente,
con el mismo criterio de modelo) y la cierra. Las respuestas que valen más allá de la tarea se proponen al
cerebro.

### 6 · El cierre

La cadena llega hasta la pausa de `turnoff-task` (Paso 7) y ahí **se detiene siempre**: el reporte de cierre
lleva un bloque `🤖 Supuestos` con las preguntas aún abiertas y lo que dependía de cada una. Commit, push, PR y
el comentario del tracker esperan el sí del dev, como siempre. Nada sale de la máquina con un supuesto abierto
sin que el dev lo sepa.
