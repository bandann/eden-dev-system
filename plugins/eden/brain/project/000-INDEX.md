---
type: index
scope: project
project: "{{PROJECT}}"
updated: "{{DATE}}"
---

# 🧠 Cerebro de {{PROJECT}}

La puerta de entrada. Si no sabes por dónde empezar, empieza aquí.

> **Cómo se lee esto:** abre la **vista de grafo** (icono del grafo, o `Ctrl+G`). Cada color es una
> capa: verde lo que es verdad, naranja cómo se hace, morado qué pasó, rojo las decisiones, y azul
> grisáceo el código. Lo que está conectado, está conectado por algo.

## Estado

| | |
|---|---|
| **Stack** | `{{STACK}}` |
| **Grafo de código** | `{{GRAPH_STATUS}}` — última construcción: `{{GRAPH_DATE}}` |
| **Cerebro global** | `~/.claude/eden-brain` — lo que vale para todos los proyectos |

## Por dónde entrar

- **[[MOC-decisiones]]** — qué decidimos y **por qué**. Lo que evita volver a discutir lo mismo.
- **[[MOC-arquitectura]]** — cómo está construido este proyecto de verdad.
- **[[MOC-gotchas]]** — lo que mordió una vez y volverá a morder.

## Las capas

### 🟢 Semántico — qué es verdad
`memory/semantic/` · Hechos estables y verificados, con su fuente y dónde se confirmaron.

### 🟠 Procedural — cómo se hace
`memory/procedural/` · Procedimientos que funcionaron y se repetirán.
> Si uno se usa **tres veces**, deja de ser memoria: se convierte en skill o en regla del kit.

### 🟣 Episódico — qué pasó
`memory/episodic/` · Casos concretos con fecha y **desenlace**. Un episodio sin desenlace no es
memoria, es una nota suelta.

### 🔴 Decisiones
`decisions/` · Por qué se hizo así y qué se descartó. Enlazan al código que afectan.

### 🎨 Diseño — cómo es el Figma *(caché — no editar)*
`design/` · El Design Spec de cada sección ya medida en Figma (`manifest.json`, `specs/`), para no
volver a leer Figma si nadie lo cambió. Lo escribe `eden_design.py save`; las capturas (`shots/`) no
entran en git. Ver `rules/on-demand/eden-design-cache-rules.md` del kit.

### 🔵 Código *(generado — no editar)*
`code/` · Lo produce Graphify desde el repo. **Se borra y se reconstruye**; cualquier edición a mano se
pierde en la siguiente construcción.

## Reglas de este vault

1. **Todo enlaza.** Un `[[enlace]]` a una nota que aún no existe **no es un error**: es la cola de
   trabajo. Obsidian los lista como "enlaces sin resolver".
2. **Nada de secretos, tokens ni datos personales de clientes.** Un vault es texto plano.
3. **No se copia lo que ya está en el repo** — se enlaza. Una copia se desincroniza y acaba mintiendo.
4. **Lo generado no se edita.**
5. **Lo que se verifica, lleva fecha.** Lo que lleva mucho sin confirmarse se marca como dudoso.

## Enlaces sin resolver = trabajo pendiente

Panel derecho → *Enlaces sin resolver*. Cada uno es algo que dijimos que importaba y aún no escribimos.
