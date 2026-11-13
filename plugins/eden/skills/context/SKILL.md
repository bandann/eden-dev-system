---
name: context
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:context` o lo pide de forma explícita e inequívoca. NO lo actives porque la sesión
  sea larga o el contexto parezca cargado: si no lo pidió por su nombre, no se usa. (Los demás comandos
  del kit descargan contexto en sus hitos por su cuenta — eso es parte de su flujo.) — Qué hace cuando
  SÍ se invoca: gestiona el contexto de una tarea larga sin comprimir ni cerrar sesión. `offload`
  escribe a disco lo trabajado y suelta el detalle; `index` muestra qué hay descargado; `load` recupera
  una pieza concreta; `status` mide el contexto real y dice qué se guardó; `save` guarda ya lo
  importante de la sesión en el cerebro y el checkpoint y avisa cuándo es seguro hacer `/clear`; `close`
  limpia al terminar, tras consolidar a memoria.
argument-hint: "offload [qué] | index | load <archivo> | status | save | close"
disable-model-invocation: true
---

## Eden Context — trabajar largo sin comprimir

Argumento recibido: `$ARGUMENTS`

Una tarea de ocho horas no debería obligarte a compactar ni a abrir sesión nueva. La estrategia es
doble: **que el contexto no se llene** (todo lo grande se delega) y **que lo trabajado viva en disco**
(se descarga por hitos y se recarga por partes).

El protocolo completo está en `rules/eden-context-rules.md`. Esto es cómo se opera.

> **Honestidad sobre el alcance:** este skill **no controla la ventana de contexto** — eso es del
> harness de Claude Code: no puede compactar ni limpiar por ti. Lo que hace es que el llenado deje de
> importar: si todo el estado está en disco, limpiar o continuar en otra sesión no pierde nada.
>
> **El vigilante automático** (`hooks/eden_context.py`) hace lo mismo sin que lo pidas: al `save_at`
> (60 %) guarda la sesión en el cerebro y pide refrescar el checkpoint; al `warn_at` (80 %) avisa si ya
> es seguro hacer `/clear`; y tras `/clear` o `/compact` reinyecta el checkpoint y lo aprendido, para que
> la sesión nueva arranque limpia pero con todo. Este skill es su mando manual.

> **Idioma:** al dev, en español. Los archivos de `context/`, en inglés.

---

### `offload [qué]` — descargar a disco

El modo principal. Toma lo que está pesando en el contexto, lo escribe estructurado y deja un puntero.

**Qué se descarga bien:**

| Artefacto | Archivo | Se suelta porque |
|---|---|---|
| Design Spec de un nodo | `context/design-spec-{seccion}.md` | Se consulta al implementar, no todo el rato |
| Inventario de una sección | `context/inventory-{seccion}.md` | Ya cumplió su función: decidir el escalón |
| Hallazgos de QA | `context/findings-{fecha}.md` | Se van tachando; basta la lista de pendientes |
| Unidad de trabajo cerrada | `context/unit-{n}-{slug}.md` | Terminó: queda qué se hizo y dónde |
| Comentarios de Pastel procesados | `context/pastel-{fecha}.md` | Igual que los hallazgos |

**Formato de cada archivo** — en inglés, con lo que permite recargarlo sin releer el original:

```markdown
# {Qué es} — {sección/unidad}
Offloaded: {fecha} · Task: {ticket} · Unit: {n}

## Summary
{2–4 líneas: lo que alguien necesita saber sin abrir el resto}

## Detail
{el contenido completo}

## Still relevant?
{qué lo invalidaría — p.ej. "si cambia el Figma" o "si se toca sections/hero.liquid"}
```

Después de escribir, **actualiza `INDEX.md`** y dile al dev qué soltaste:

```
📤 DESCARGADO
   context/design-spec-hero.md      Design Spec del hero · 14 elementos · mobile+desktop
   context/unit-2-value-props.md    Unidad #2 cerrada · 3 archivos

En contexto queda: requerimiento, plan (unidad 3 de 5), decisiones, pendientes.
```

**Lo que nunca se descarga:** el requerimiento, el plan, las decisiones tomadas, lo pendiente y el
índice. Eso es lo que da coherencia; si se va, la sesión deja de saber qué hace.

---

### `index` — qué hay descargado

Lee `context/INDEX.md` y muéstralo. Formato del índice:

```markdown
# Context index — {task}

| File | What it is | From | Reload when |
|---|---|---|---|
| `design-spec-hero.md` | Hero measurements, both breakpoints | Unit 1 | Implementing or auditing the hero |
| `inventory-header.md` | Current header schema + blast radius | Unit 2 | Touching the header again |
```

La columna **Reload when** es la importante: evita abrir archivos "por si acaso".

---

### `load <archivo>` — recuperar una pieza

Lee **solo ese archivo**, no el directorio. Y antes de usarlo, la comprobación que evita el peor fallo:

**¿Sigue siendo válido?** Si el archivo dice que se invalida al tocar `sections/hero.liquid` y ese
archivo cambió después de la fecha de descarga, **está obsoleto**: se vuelve a medir y se reescribe.
Un spec viejo tratado como vigente produce trabajo que hay que rehacer.

```bash
git log -1 --format=%cd -- {archivo-que-invalidaria}
```

---

### `status` — cuánto contexto queda y qué está guardado

`python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_context.py" status` mide el contexto **real** de la sesión
(el porcentaje exacto de la barra de estado de Eden si está activa; si no, los tokens del último turno en
el transcript, contra la ventana del modelo) y dice si ya se guardó y si es seguro limpiar:

```
📊 CONTEXTO — {pct} % de {ventana} ({fuente: barra de estado | transcript})

Umbrales           guarda al {save_at} % · avisa al {warn_at} %
Guardado           {no todavía | al {pct} % a las {hora}}
   Cerebro         {notas escritas ✅ | destilando {n} tramo(s) ⏳ | sin cerebro}
   Checkpoint      {refrescado ✅ | pendiente ⏳}
Seguro hacer /clear: {sí ✅ | todavía no — {qué falta}}

Recomiendo soltar (si aún no toca limpiar)
   · {artefacto} — recuperable de {archivo}
```

### `save` — guardar ya lo importante

Sin esperar al umbral:

1. `python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_context.py" save` — guarda lo nuevo de la sesión en el
   cerebro (lo del proyecto se escribe solo; lo general va a la bandeja) y lanza el destilado.
2. **Refresca `.claude/checkpoint.md` como relevo**: tarea y objetivo, decisiones con su porqué, qué está
   hecho, qué falta, el siguiente paso exacto y punteros (rutas, ramas, commits). Es lo único que tendrá
   una sesión nueva del trabajo en curso: se escribe pensando en continuar sin esta conversación.
3. Comprueba con `status` y, cuando el cerebro terminó de destilar, díselo al dev:
   `✅ Guardado. Puedes hacer /clear: la sesión nueva arranca limpia y con todo.`
   Si aún destila, dilo y vuelve a mirar en el siguiente turno; **nunca digas "seguro" antes de tiempo**.

Si el dev quiere el consumo real de tokens de la sesión, el skill `token-monitor` que tiene instalado
lo desglosa por agente, modelo y herramienta — es mejor dato que cualquier estimación de aquí.

---

### `close` — limpiar al terminar

Al cerrar la tarea, **antes** de borrar nada:

1. **Consolidar a memoria** (`/eden:memory consolidate`): lo que servirá dentro de seis meses sale de
   `context/` y del checkpoint hacia `memory/`. Un gotcha, un hecho verificado, una receta.
2. **Lo que ya está en el repo o en `docs/`** no se guarda: se cita.
3. Recién entonces se limpia `context/` — es efímero, de la tarea.

`turnoff-task` lo invoca en su Paso 9. Nunca se borra `context/` sin haber consolidado: es tirar a la
basura lo aprendido.

---

## La regla de oro

**Nada se suelta sin haberlo escrito.** "Ya no lo necesito en contexto" solo es válido si quedó en
disco y en el índice. Descartar sin escribir es exactamente cómo se pierde una tarea larga.
