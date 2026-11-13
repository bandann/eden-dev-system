# Estrategia de modelos — Eden (el modelo principal planifica, el ejecutor ejecuta)

El kit corre con **dos niveles de modelo** y cada uno tiene un trabajo distinto. No es una preferencia:
es lo que mantiene el contexto de la sesión limpio y hace que las decisiones las tome siempre el modelo
que ve el panorama completo. Eden no depende de un proveedor: los niveles se llaman `strong` y `fast`, y
cada herramienta los cumple con sus propios modelos.

| Nivel | Quién | En Claude Code | En otras herramientas |
|---|---|---|---|
| **`plan`** — el orquestador | La sesión de `/eden:go`: entiende, arma la cadena de skills, planea, reparte, verifica | **Fable** | El modelo más capaz que el dev tenga para razonar y planear |
| **`strong`** — el modelo principal | La sesión con la que habla el dev (fuera de `/eden:go`), y los agentes de las unidades **complejas** | Opus | El modelo más capaz que el dev tenga (GPT de gama alta, Gemini Pro, Qwen, Kimi, GLM, DeepSeek…) |
| **`fast`** — el modelo ejecutor | Los agentes de las unidades **acotadas** | Sonnet | El modelo rápido de la herramienta, o el de la sesión si la herramienta no deja elegir |

Cómo traduce Eden el nivel a cada herramienta (y cómo cambiarlo): `scripts/eden_ai.py` → `TIERS`, y
`ai.tiers` en `~/.claude/eden-config.json`.

## El reparto

| | **`strong`** — la sesión principal | **`fast`** — los agentes |
|---|---|---|
| **Es** | El orquestador. Habla con el dev y sostiene el hilo de la tarea | Los ejecutores. Reciben un encargo cerrado y lo cumplen |
| **Hace** | Entender el ticket, leer el diseño, decidir el alcance, planear, repartir, **verificar** e integrar | Escanear, medir, extraer, escribir código, auditar |
| **Mantiene** | El contexto completo: requerimientos, Design Spec, decisiones, qué falta | Solo lo suyo; no necesita saber el resto |
| **Decide** | Todo lo que sea una decisión | Nada — si hay que decidir, se detiene y reporta |

**Regla corta: el modelo principal piensa y decide, el ejecutor hace.**

## Por qué

- **Contexto.** Un escaneo del tema, un volcado de Figma o un diff largo son miles de tokens de datos
  crudos. Si entran en la sesión principal, desplazan lo que de verdad hay que recordar: el
  requerimiento, el plan, lo que ya se decidió. Delegándolos, la sesión principal recibe **la
  conclusión**, no el volcado.
- **Calidad de las decisiones.** El alcance, el blast radius, el escalón reuse-first y "esto rompe algo
  en producción" son juicios; se toman con el panorama completo, no dentro de una tarea aislada.
- **Coste y velocidad.** La ejecución acotada y verificable es exactamente para lo que sirve un modelo
  más rápido.

## Qué delega la sesión principal, siempre

| Trabajo | Agente |
|---|---|
| Escanear el proyecto, inventariar una sección, medir el blast radius | `eden:explorer` |
| Extraer el diseño de Figma y armar el Design Spec | `eden:figma-extractor` |
| Escribir código de una unidad de trabajo | `eden:implementer` |
| Medir Figma vs implementación real | `eden:design-auditor` |
| Revisar el diff completo buscando bugs y regresiones | `eden:qa-reviewer` |
| Ejecutar en modo informe un skill que `/eden:go` enrutó y el dev confirmó | `eden:router-qa` · `eden:router-design` · `eden:router-knowledge` · `eden:router-wp` |

**Estos son los roles genéricos.** Qué agente concreto cumple cada rol depende del stack: lo dice
`teams/{stack}/roster.md` (en Shopify, los `eden-shopify-*`). Ver `rules/eden-team-rules.md`.

Los `eden-router-*` **no deciden la ruta**: la decide la sesión principal en `/eden:go`. Solo corren skills
que no preguntan a mitad del flujo, o los corren hasta la propuesta, porque un subagente no puede
preguntarle nada al dev.

### Delegar con proporción: solo con un motivo que se pueda nombrar

Delegar cuesta: el agente arranca sin el contexto, hay que escribirle el encargo y hay que verificar lo
que devuelve. Por eso **se delega cuando hay un motivo concreto**, y si no lo hay, la sesión principal lo
hace ella misma:

| Se delega cuando… | Ejemplo |
|---|---|
| **Leer es grande**: más de ~3 llamadas de lectura, ~10k tokens de datos crudos o 5 búsquedas para encontrar algo | Escanear el tema, inventariar una sección, un árbol de Figma, un diff largo |
| **Hay trabajo en paralelo** sobre archivos que no se cruzan | Dos unidades de un plan aprobado |
| **Hace falta un verificador independiente** para algo de riesgo | La revisión de `turnoff-task`, la auditoría de seguridad, la medición contra Figma |
| **El contexto se está llenando** y la tarea sigue | Pasado `save_at`, lo que quede de lectura va por agente |

| Lo hace la sesión principal cuando… | Ejemplo |
|---|---|
| El cambio es pequeño y ya se entiende | Un texto, un estilo, un arreglo de una o pocas líneas en un archivo conocido |
| Basta leer un archivo concreto y acotado que se va a tocar | El snippet que se edita, el schema de una sección |
| Delegar costaría más que hacerlo | Una búsqueda puntual con resultado esperado |

Al delegar, el motivo se dice en una línea ("lo delego porque es un escaneo de 40 archivos"). Un motivo
que no se puede nombrar es señal de que no hacía falta.

**Para lecturas grandes —la primera fila de arriba— la delegación es obligatoria, no una recomendación** (`eden-context-rules.md`):
escaneos, árboles de Figma, diffs largos e inventarios van sí o sí por agente. Es lo que permite
sostener una tarea larga sin comprimir el contexto.

## Qué NO delega nunca

- Hablar con el dev: preguntas, planes, reportes, decisiones que le corresponden a él.
- Decidir el alcance, el escalón reuse-first, o si algo se puede tocar.
- Aprobar el resultado de otro agente. **El reporte de un agente es una afirmación, no una
  verificación**: la sesión principal comprueba el diff, no lo da por bueno.
- Commitear, pushear, abrir PRs, comentar en el tracker o mover una tarea.
- Resolver una contradicción entre el ticket, el diseño y el proyecto.

## Cómo se le encarga algo a un agente

Un encargo sin estas cinco cosas produce un resultado que hay que rehacer:

1. **Qué** — el resultado observable, en una frase.
2. **Dónde** — la lista cerrada de archivos o el alcance exacto. Fuera de ahí, no toca nada.
3. **Con qué** — Design Spec, tokens, lo reutilizable ya identificado, convenciones del proyecto.
4. **Acepta cuando** — criterio verificable.
5. **Qué NO hacer** — lo que está fuera de alcance y podría tentar.

Y una instrucción que va en todos: **si algo es ambiguo, detente y reporta; no adivines.**

## Paralelismo

Se lanzan varios agentes a la vez solo cuando sus **conjuntos de archivos no se cruzan**. Dos agentes
escribiendo el mismo archivo se pisan. Cuando se paralelice, van en un solo turno para que corran de
verdad en paralelo.

## Configurar la sesión

Los agentes declaran su nivel en el frontmatter con el nombre de Claude (`model: sonnet` = `fast`,
`model: opus` = `strong`). Eso es parte del kit y no hay que tocarlo. En otras herramientas se traduce al
campo que cada una entiende (`fast` en Qwen Code, `inherit` en Cursor), o se omite para que el agente
herede el modelo de la sesión cuando la herramienta no tiene ese campo o sus ids dependen de la cuenta.

**Que la sesión principal corra en el nivel `strong` lo configura el dev**, no el kit:

| Herramienta | Cómo |
|---|---|
| Claude Code | `/model opus`, o `"model": "opus"` en `settings.json` del proyecto o global |
| Claude Code con otro proveedor (Kimi, GLM, MiniMax, DeepSeek, Qwen) | `ANTHROPIC_MODEL` con el modelo más capaz del proveedor |
| Qwen Code · Codex · Gemini | `/model`, y el más capaz |
| Cursor · OpenCode | El selector de modelo (`/models` en OpenCode) |

Si un comando del kit arranca y la sesión corre claramente en un modelo **rápido o pequeño** (Haiku, un
Flash, un Mini, un Lite…), se le dice al dev en una línea y se le deja decidir si cambia o sigue igual.
No se bloquea el trabajo por eso, pero tampoco se calla: el reparto de modelos es parte de cómo el kit
garantiza sus resultados. Si no se sabe en qué modelo corre la sesión, no se dice nada.

## `/eden:go` orquesta: Fable planea, Opus y Sonnet ejecutan

Con `/eden:go`, la sesión es el **orquestador** (nivel `plan`, Fable en Claude). No escribe el código de las
unidades: las reparte, y **por cada encargo elige el modelo del agente** según la complejidad (en Claude, el
parámetro `model` al lanzar el agente; los agentes declaran `sonnet` por defecto y solo se sube lo que lo
amerita). El motivo va en una línea ("a Opus: toca carrito, checkout y tres consumidores").

| A **Opus** (`strong`) si… | A **Sonnet** (`fast`) si… |
|---|---|
| Toca varias capas o algo compartido con blast radius grande | Es una unidad con archivos y criterio de aceptación cerrados |
| Hay que decidir el diseño de la solución dentro de la unidad | El cómo ya está decidido en el plan |
| Depuración con causa desconocida, seguridad, datos, migraciones | Escanear, medir, extraer, testear, reportar |
| Ya falló una vez con Sonnet | Es repetitivo o mecánico |

Si la sesión de `/eden:go` no corre en el nivel `plan`, se le dice al dev en una línea (en Claude Code,
`/model fable`) y se sigue: no se bloquea. En herramientas sin modelos equivalentes, el agente hereda el de la
sesión (`scripts/eden_ai.py` → `TIERS`).
