# Memoria — Eden (cuatro capas)

El kit recuerda entre sesiones y entre proyectos. No como una caja negra: como **archivos que se pueden
leer, revisar en un PR y corregir**. Lo que el kit aprende en una tienda debe poder aplicarse a las
otras — pero solo después de que un humano lo apruebe.

## Las cuatro capas

| Capa | Responde a | Vive en | Se escribe |
|---|---|---|---|
| **Trabajo** | ¿Qué estoy haciendo ahora? | `.claude/checkpoint.md` del proyecto | Automática, durante la tarea |
| **Episódica** | ¿Qué pasó, cuándo y cómo terminó? | `memory/episodic/` | Al cerrar la tarea |
| **Semántica** | ¿Qué es verdad? | `memory/semantic/` | Cuando un hecho se verifica |
| **Procedural** | ¿Cómo se hace esto? | `memory/procedural/` | Cuando un procedimiento funciona |

Y dos ámbitos:

```
~/.claude/eden-brain/               GLOBAL — vale para todos los proyectos. Se escribe CON APROBACIÓN.
{proyecto}/.claude/brain/memory/  LOCAL  — vale para este cliente. Se escribe automáticamente.
```

> **Las cuatro capas no cambian; cambió dónde viven.** Desde la versión 1.2.0 del kit, la memoria vive
> **dentro del cerebro** (`eden-brain-rules.md`): un vault de Obsidian donde las notas se enlazan con
> `[[wikilinks]]` y se ven como grafo, junto al grafo de código de Graphify. Eso es lo que convierte la
> memoria de una carpeta de apuntes en algo consultable.
>
> Ubicaciones anteriores: `~/.claude/eden-memory/` y `{proyecto}/.claude/memory/`. **`/eden:brain init`
> migra lo que hubiera** y deja un `MOVED.md` apuntando al sitio nuevo — nada se borra en silencio. Si
> un proyecto todavía tiene la carpeta vieja y no la nueva, se lee de la vieja y se propone migrar.

---

## 1 · Memoria de trabajo — `checkpoint.md`

La que ya tenía el kit. Es **efímera y detallada**: el plan aprobado, las unidades de trabajo, el Design
Spec, qué se hizo y qué falta. Sirve para reanudar si la sesión se corta.

**Se borra o se marca como finalizada al cerrar la tarea** — pero antes se **consolida** (ver abajo). Un
checkpoint viejo confunde a la siguiente sesión; un checkpoint sin consolidar tira a la basura todo lo
aprendido.

## 2 · Memoria episódica — qué pasó

Casos concretos, con fecha, proyecto y **desenlace**. Es la que permite decir *"esto ya nos pasó"*.

```markdown
---
type: episodic
date: 2026-09-04
project: {cliente}
task: {ticket}
tags: [horizon, metafields, call-for-price]
---
## Qué pasó
El precio seguía visible en el carrusel del home aunque Call for Price estaba en true.

## Por qué
El carrusel renderiza el precio con su propio snippet, no con el del product card.

## Cómo se resolvió
{qué se hizo}

## Qué aprendimos
→ semantic/shopify-horizon.md: el carrusel del home tiene su propio render de precio.
```

Un episodio sin desenlace no es memoria, es una nota suelta. **Si no terminó, no se guarda todavía.**

## 3 · Memoria semántica — qué es verdad

Hechos estables y verificados. Sin narrativa, sin fecha en el cuerpo: afirmaciones.

```markdown
- En Horizon, los estilos de sección van en `{% stylesheet %}` dentro del propio archivo.
  · Verificado en: {proyecto}, {proyecto} · 2026-09
- Call for Price debe ocultar el precio en 7 lugares, no solo el PDP.
  · Fuente: manual del equipo · confirmado en {proyecto}
```

**Cada hecho lleva de dónde salió y dónde se verificó.** Un hecho sin respaldo es una suposición con
formato de certeza, y eso es peor que no tenerlo.

## 4 · Memoria procedural — cómo se hace

Procedimientos que funcionaron y se repetirán. **Ojo:** los `skills/` del kit ya son memoria procedural
—la oficial y revisada—. Esta capa es para lo que **todavía no** es un skill: recetas, secuencias de
comandos, trucos de un stack concreto.

Si una receta procedural se usa tres veces, **deja de ser memoria y se convierte en skill o en regla**.
Eso es el objetivo: la memoria procedural es la antesala del kit, no un cajón paralelo.

---

## Consolidación — de trabajo a permanente

Al cerrar una tarea (`turnoff-task`), la memoria de trabajo se destila. Por cada cosa que pasó:

| Si es… | Va a |
|---|---|
| Un problema con causa y solución | **Episódica** (local) |
| Un hecho del tema/plataforma que se repetirá | **Semántica** |
| Una secuencia que funcionó y volverás a usar | **Procedural** |
| Solo servía para esta tarea | **Se descarta** |

**Consolidar no es copiar el checkpoint.** Es quedarse con lo que servirá dentro de seis meses.

## Promoción — de local a global

Un hecho local pasa a global cuando **se confirma en dos o más proyectos**, o cuando es del stack (no
del cliente). Entonces se **propone al dev** y espera su sí:

```
🧠 Para memoria global — ¿lo promuevo?
   "{hecho}"
   Visto en: {proyecto A}, {proyecto B}
   Aplicaría a: todos los proyectos {Shopify/Horizon/…}
```

**Nada llega a la memoria global sin aprobación.** Con 40+ tiendas, un caso particular promovido a regla
general se propaga a todas — y ese es el fallo que hace inservible una memoria automática.

---

## Qué NO se memoriza

- **Lo que ya está en el código, en `docs/` o en git.** Si se puede leer del repo, no es memoria: es
  contexto. Memorizarlo lo duplica y lo desincroniza.
- Lo que solo aplicaba a una tarea concreta.
- Credenciales, tokens, datos personales de clientes. **Nunca.**
- Suposiciones sin verificar. Si no se comprobó, no es un hecho.
- Opiniones sobre el código de otros.

## Qué SÍ vale la pena

- **Gotchas**: lo que mordió una vez y volverá a morder.
- **Correcciones del dev**: cuando te dicen "no, en este tema esto va así", eso es oro — es conocimiento
  que ninguna herramienta te iba a dar.
- Decisiones no obvias y **su porqué**, para no volver a discutirlas.
- Diferencias entre clientes que parecen iguales.

## Higiene

- **Un hecho equivocado es peor que ninguno.** Si algo resulta falso, se corrige o se borra — no se
  matiza.
- Cada entrada dice **cuándo** se verificó. Lo que lleva mucho sin confirmarse se marca como dudoso.
- Si dos entradas se contradicen, gana **la realidad del repo**, y se corrige la memoria.
- La memoria se lee **al arrancar** una tarea, no a mitad: llegar tarde con un "por cierto, esto ya nos
  pasó" no sirve de nada.
