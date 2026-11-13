# Equipos por stack — Eden (roles, rosters y líderes)

El kit trabaja como un **equipo de desarrollo multidisciplinario**: un líder que habla con el dev y
decide, y especialistas que ejecutan cada subtarea. El núcleo es agnóstico; **cada stack aporta su
equipo** con un roster. Hoy: Shopify y WordPress. Después: React, apps web y móviles.

## Las tres capas

| Capa | Qué es | Dónde vive | Modelo |
|---|---|---|---|
| **Enrutador** | `/eden:go` — entiende el pedido y elige la ruta | `skills/go/` | `strong` (sesión) |
| **Líder de stack** | `/eden-{stack}` — tech lead del equipo: clasifica, planea con el dev, reparte, integra, verifica | `skills/eden-{stack}/` | `strong` (sesión) |
| **Especialistas** | Subagentes `eden-{stack}-*` con una subtarea cerrada | `agents/` | `fast` |

**El líder es un skill, nunca un subagente.** Un subagente no puede preguntarle nada al dev, y el
líder tiene que aprobar el plan con él, pedir la rama base y parar ante cualquier decisión. Si el líder
fuera un subagente, o se saltaría las puertas de aprobación o se quedaría bloqueado en ellas.

## Los skills piden ROLES, no agentes

Un skill del kit no nombra agentes concretos. Nombra un **rol**, y el roster del stack del proyecto
dice qué agente lo cumple. Así, un skill escrito una vez sirve para todos los stacks, y agregar un stack
es agregar su roster, no editar veinte skills.

### Vocabulario de roles (cerrado)

| Rol | Responsabilidad | Escribe |
|---|---|---|
| `explorer` | Escanear, inventariar, medir blast radius | No |
| `architect` | Auditar un proyecto existente y proponer la decisión de arquitectura / escalón reuse-first | No |
| `design-extractor` | Figma → Design Spec por breakpoint | No |
| `web-extractor` | Sitio web en vivo → Design Spec por breakpoint, midiendo el render con Playwright (`/eden:w2shopify`) | Solo en `.claude/context/w2s/` |
| `design-system` | Integrar los fundamentos al sistema de tokens del stack | Sí |
| `implementer` | Escribir el código de una unidad de trabajo | Sí |
| `data` | Modelo de datos, contenido estructurado, APIs e integraciones | Sí |
| `devops` | Entorno, CLI, configuración, herramientas de validación, sincronización | Local (remoto según el roster) |
| `design-auditor` | Medir Figma vs render real | No |
| `tester` | Escribir y mantener las suites de pruebas del stack (unitarias, integración, e2e) con su runner; **test-first**: el test falla antes de que exista el código | Solo tests y fixtures |
| `reviewer` | Revisión independiente del diff | No |
| `quality-auditor` | Performance, accesibilidad, SEO, analytics | No |
| `security-auditor` | Auditar la seguridad del diff o del proyecto: modelo de amenazas, checklist OWASP, secretos, dependencias; reporta con severidad | No |
| `migrator` | Mover datos o sitios entre entornos | Sí, con backup |

Un rol nuevo se agrega **aquí primero**, y después en los rosters. Un roster no inventa roles.

### Resolución: qué agente cumple el rol

En este orden, y se para en el primero que responda:

1. **Lo que diga el dev en el momento.**
2. **Roster del proyecto**: `{proyecto}/.claude/teams/{stack}/roster.md` (un proyecto puede sustituir un
   especialista).
3. **Roster del stack instalado**: `${CLAUDE_PLUGIN_ROOT}/teams/{stack}/roster.md`.
4. **Roster genérico**: `${CLAUDE_PLUGIN_ROOT}/teams/_generic/roster.md`.

El stack sale de `rules/eden-stack-rules.md`. Si el rol **no tiene agente en ningún roster** (p. ej.
`devops` en un stack sin roster), el trabajo lo hace la sesión principal o el dev, y se declara en una
línea. **Nunca se bloquea el trabajo por falta de especialista.**

### Roles con especialización por archivos

`implementer` puede tener varios agentes en un stack. El roster declara **qué archivos le tocan a
cada uno** (tabla de propiedad). El líder reparte las unidades de trabajo por esa tabla. Cuando una
unidad cruza dos dueños, se parte en dos unidades secuenciales, o se le asigna al dueño del archivo
principal con un encargo explícito sobre el otro. **Dos agentes nunca escriben el mismo archivo en
paralelo.**

## Contrato de todo especialista

Todos los `eden-{stack}-*` cumplen esto, además de lo propio de su rol:

1. **Encargo con las cinco partes** de `eden-model-strategy-rules.md` (qué, dónde, con qué, acepta
   cuando, qué NO hacer). Sin ellas, pide que lo completen en su respuesta, en vez de adivinar.
2. **No le pregunta nada al dev.** Ante una decisión, se detiene y la devuelve como
   `DECISIÓN PENDIENTE`.
3. **Solo toca los archivos del encargo.** Si aparece otro archivo necesario, se detiene y lo reporta.
4. **Nada remoto sin autorización explícita escrita en el encargo**: ni el tracker, ni git remoto, ni la
   tienda o el sitio. Lo que el roster prohíbe, lo prohíbe aunque el encargo lo pida.
5. **Reporta con el formato de handoff** del roster de su stack: qué hizo, archivos, escalón
   reuse-first, qué verificó, qué no, y qué queda para quién.
6. **El reporte es una afirmación, no una verificación.** El líder revisa el diff antes de dar algo por
   hecho.

## Qué hace el líder, siempre

- Clasifica el trabajo: **proyecto nuevo**, **proyecto avanzado** (onboarding) o **tarea**.
- Lee memoria y cerebro al arrancar (`eden-memory-rules.md`, `eden-brain-rules.md`).
- Propone el plan **con el especialista asignado a cada unidad** y espera el sí.
- Paraleliza solo unidades cuyos archivos no se cruzan, en un solo turno.
- Integra, verifica, y pasa por `reviewer`, `design-auditor` y `security-auditor` antes de cerrar.
- Descarga contexto en los hitos (`eden-context-rules.md`) y mantiene el checkpoint.
- **No commitea, no pushea, no publica.** Eso sigue siendo de `turnoff-task`.

## Agregar un stack nuevo

1. `teams/{stack}/roster.md` con los roles que cubre, los agentes, la tabla de propiedad de archivos,
   las prohibiciones y el formato de handoff.
2. Los agentes `agents/{stack}-*.md` (se invocan como `eden:{stack}-*`).
3. `skills/{stack}/` (el líder, `/eden:{stack}`) y `skills/{stack}-setup/` (levanta el entorno), y sus
   filas en `skills/go/references/routing-table.md`.
4. El módulo de reglas `rules/{stack}/` (con `flavors/` si el stack tiene sabores) y su fila en
   `eden-stack-rules.md`, más su detección en `scripts/eden_stack.py`.
5. `tests/test_stacks.py` lo valida: roster con roles del vocabulario, agentes que existen, líder,
   setup y módulo presentes, y la detección con un proyecto de ejemplo.

Los skills del núcleo **no se tocan** para agregar un stack.
