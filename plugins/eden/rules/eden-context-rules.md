# Contexto — Eden (no llenarlo, y descargarlo por hitos)

Una tarea larga no debería obligar a comprimir el contexto ni a cerrar la sesión. La forma de
conseguirlo no es "limitar" la ventana —eso no lo controla el kit— sino **que el contexto no se llene**
y que, cuando se llene, **no importe**: el estado vive en disco y se recarga por partes.

> Lo que el kit **no** puede hacer: interceptar la compactación, medir la ventana con exactitud o
> vaciarla a voluntad. Eso es del harness. Lo que sí puede: no meter basura, y sacar lo que ya no hace
> falta.

## Las tres reglas

### 1 · Lo que entra al contexto, entra destilado

**Toda lectura grande se delega a un agente (nivel `fast`), sin excepción.** La sesión principal no ve volcados:

| Trabajo | Agente | Lo que devuelve |
|---|---|---|
| Escanear el proyecto, inventariar, blast radius | `eden:explorer` | Conclusiones con rutas |
| Extraer un nodo de Figma | `eden:figma-extractor` | Design Spec destilado |
| Revisar un diff largo | `eden:qa-reviewer` | Hallazgos con `archivo:línea` |
| Medir implementación vs diseño | `eden:design-auditor` | Deltas, no capturas ni árboles |

Un árbol de Figma, un `git diff` de 40 archivos o el listado de un tema son miles de tokens de datos
crudos. **Si entran a la sesión, desplazan lo que de verdad hay que recordar**: el requerimiento, el
plan, lo ya decidido.

Lo que no es una lectura grande lo hace la sesión principal: un archivo concreto y acotado que se va a
modificar ahora mismo, o un cambio pequeño y claro (tabla de delegación proporcional en
`eden-model-strategy-rules.md`).

**Y antes de delegar, se pregunta al cerebro.** Si el proyecto tiene grafo
(`rules/eden-brain-rules.md`), el primer intento no es un agente: es una consulta acotada.

```bash
graphify query "{la pregunta}" --budget 2000
```

Responde en un presupuesto de tokens en vez de traer un volcado — que es exactamente lo que esta regla
persigue. **El orden es: grafo → vault → delegar la lectura.** Si el grafo no lo sabe, se delega como
siempre; no se fuerza una respuesta pobre por haber preguntado. Y si el grafo es más viejo que el
último commit que toca lo preguntado, **se dice y se verifica**: un grafo desactualizado responde con
seguridad sobre código que ya no existe.

### 2 · Punteros, no contenido

Una vez destilado algo, en el contexto se queda **la referencia**, no el cuerpo:

```
✅ Design Spec del hero → .claude/context/design-spec-hero.md (14 elementos, mobile+desktop)
❌ [los 14 elementos con todas sus medidas, otra vez]
```

Y **no se relee lo ya leído**. Si un archivo ya se procesó y su conclusión está en disco, se consulta la
conclusión.

### 3 · Descarga por hitos

En puntos definidos del flujo, lo trabajado se escribe a `.claude/context/` y **se suelta del
contexto activo**:

| Hito | Qué se descarga |
|---|---|
| Tras extraer Figma | El Design Spec completo por breakpoint |
| Tras inventariar una sección | El inventario y el blast radius |
| **Al cerrar cada unidad de trabajo** | Qué se hizo, qué archivos, qué decisiones, qué quedó |
| Tras una auditoría (QA o diseño) | Los hallazgos con su ubicación |
| Antes de lanzar varios agentes | El estado actual, por si la respuesta es larga |

Después de descargar, en el contexto vivo queda **una línea por artefacto**.

---

## Qué se queda SIEMPRE en contexto

Esto no se descarga nunca, porque es lo que da coherencia a la sesión:

- El **requerimiento** y los criterios de aceptación.
- El **plan aprobado** y en qué unidad vamos.
- Las **decisiones tomadas** y su porqué (no el razonamiento, la decisión).
- Lo que está **pendiente** y lo que quedó bloqueado.
- El **índice** de lo descargado.

Si esto se pierde, la sesión deja de saber qué está haciendo. Todo lo demás es recuperable de disco.

## La estructura

```
{proyecto}/.claude/
├── checkpoint.md          memoria de TRABAJO — el estado de la tarea
├── context/
│   ├── INDEX.md           qué hay descargado, de qué unidad, cuándo recargarlo
│   ├── design-spec-*.md
│   ├── inventory-*.md
│   └── findings-*.md
└── memory/                lo que sobrevive a la tarea (eden-memory-rules.md)
```

**`context/` es efímero**: pertenece a la tarea en curso y se limpia al cerrarla, después de consolidar
lo que valga la pena a `memory/`. `checkpoint.md` es el resumen vivo; `context/` es el detalle
archivado.

## Recargar

Cuando se necesita algo descargado, se lee **solo ese archivo**, no todo el directorio. `INDEX.md`
existe justo para eso: dice qué contiene cada archivo, para no tener que abrirlos a ver.

Si al recargar resulta que el archivo ya no refleja la realidad (el código cambió después), **gana la
realidad**: se vuelve a medir y se reescribe el archivo.

## Señales de que hay que descargar ya

- Acabas de cerrar una unidad de trabajo.
- Vas a lanzar un agente que puede devolver mucho.
- Llevas varias herramientas seguidas leyendo archivos.
- El dev pregunta por el estado y te cuesta resumirlo — señal de que hay demasiado suelto.
- La tarea lleva más de dos horas o más de tres unidades de trabajo.

## Lo que NO se hace

- **No se descarga lo que aún se está usando.** Descargar el plan a mitad de ejecutarlo obliga a
  releerlo: cuesta más de lo que ahorra.
- **No se resume lo que no se entendió.** Un resumen equivocado en disco es peor que un contexto lleno:
  el error se propaga a todo lo que venga después.
- **No se descarta información sin escribirla.** "Ya no la necesito" solo vale si quedó en disco.
- **No se convierte en burocracia.** Una tarea de veinte minutos no necesita nada de esto; el protocolo
  es para las largas.

---

## El vigilante de contexto (automático)

`hooks/eden_context.py` aplica esto sin que nadie lo pida:

| Cuándo | Qué hace |
|---|---|
| **Cada mensaje del dev** | Mide el contexto real: el porcentaje exacto de la barra de estado de Eden si está activa; si no, los tokens del último turno del transcript contra la ventana del modelo |
| **Al `save_at` (60 %)** | Guarda lo nuevo de la sesión en el cerebro (lo del proyecto solo; lo general a la bandeja) y pide a Claude refrescar `.claude/checkpoint.md` como relevo: tarea, decisiones y porqué, hecho, pendiente, siguiente paso, punteros |
| **Al `warn_at` (80 %)** | Avisa al dev. **"Seguro" solo cuando el cerebro terminó de escribir las notas y el checkpoint es posterior al guardado**; si no, dice qué falta |
| **Tras `/clear` o `/compact`** | Reinyecta el checkpoint y lo aprendido en la sesión anterior: la sesión nueva arranca limpia pero sabiendo dónde estaba |

La recomendación es **`/clear`** (contexto limpio + reinyección) antes que dejar llegar el autocompact. El
kit no puede limpiar ni compactar por el dev: avisa y deja todo listo. Se configura en `context` de
`eden-config.json` (`save_at`, `warn_at`, `window`, `enabled`) o por proyecto; `/eden:context save` y
`status` son su mando manual.

