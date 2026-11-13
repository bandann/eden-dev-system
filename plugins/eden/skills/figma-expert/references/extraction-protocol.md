# Extracción — qué se mide en Figma y cómo

Esta referencia cubre la **fase de extracción** de `/eden:figma-expert`. La regla que la sostiene es una:
**nada se estima**. Cada número sale de una medición real del nodo, por el MCP de Figma Console. Si algo
no se pudo medir, se reporta como no medido — **jamás se rellena con un valor plausible**, porque un
dato inventado convierte "1:1" en una frase vacía.

La ejecuta el `design-extractor` (rol, nivel `fast`; el agente lo asigna el roster del stack). La sesión principal recibe el Design Spec destilado, no el
volcado del árbol (`rules/eden-context-rules.md`).

---

## Antes de medir: los anchos

Los breakpoints salen de `.claude/project-config.json` → `breakpoints`, y esos salen de los **frames
reales del Figma**. No se asumen 320 / 375 / 768 / 1024 / 1440 porque sean los de siempre: si el
diseñador entregó 390 y 1512, esos son los anchos.

Si el proyecto no los tiene declarados, se leen del Figma y se propone escribirlos con
`/eden:create-fundaments`.

---

## Qué se extrae, por nodo

### Página / sección contenedora

- Dimensiones del frame.
- Contenedor de contenido y su ancho máximo.
- Fondo (color, gradiente, imagen).
- Grid y columnas, si el frame los define.
- Orden de las secciones y el espaciado **entre** ellas.
- Ritmo vertical: los paddings superior e inferior de cada bloque.

### Tipografía — de cada texto, sin resumir

| | |
|---|---|
| `font-family` | La familia real, y si es un estilo de texto de Figma, **su nombre** |
| `font-size` | |
| `font-weight` | El peso numérico, no "bold" |
| `line-height` | En px o en porcentaje, tal como lo define Figma |
| `letter-spacing` | Incluido cuando es negativo — es lo que más se pierde al implementar |
| `text-transform` | |
| `color` | Resuelto al **token** del proyecto, no al hex |
| `text-align` | |
| Restricción de ancho | Si el texto tiene ancho fijo o `max-width`, porque define dónde corta |

La tipografía es **estructural, no decorativa**: un tamaño mal medido cambia el alto del bloque, el
salto de línea y todo lo que viene debajo.

### Layout

`width` · `height` · `x` · `y` · `padding` (los cuatro lados, por separado) · `gap` · alineación ·
distribución · dirección del auto-layout · qué hijos son *hug* y cuáles *fill*.

El **hug vs fill** importa tanto como la medida: un elemento que en Figma llena el contenedor y en el
código está a contenido produce un layout desbalanceado que ninguna medida puntual explica.

### Visual

Fondos · gradientes (tipo, paradas, ángulo) · bordes (ancho, color, lado) · radios (los cuatro, por
separado) · sombras (offset, blur, spread, color, opacidad) · opacidad · blur · overlays · modos de
mezcla.

### Media

- Dimensiones del marco de la imagen y **aspect-ratio**.
- Cómo está encajada: `fill`, `fit`, `crop`, `tile` — eso es lo que se traduce a `object-fit`, y solo
  se usa `cover` **cuando el diseño lo dice**, no porque sea cómodo.
- Punto focal / posición del recorte → `object-position`.
- **La variante de cada breakpoint.** Mobile y desktop casi nunca comparten la misma imagen ni el mismo
  recorte; asumir que sí es uno de los fallos más caros.

### Componentes y estados

Qué nodos son instancias de un componente, sus variantes, y los estados que el diseño define: hover,
focus, activo, deshabilitado, cargando, vacío. Si el Figma no dibuja un estado accesible, se implementa
el comportamiento correcto **sin cambiar el diseño visual**.

---

## Assets

Si el asset existe en Figma, **se usa el asset real**. No se sustituye:

```
icono de Figma  →  carácter Unicode          ✗
icono de Figma  →  librería de iconos ajena   ✗
logo            →  texto                      ✗
imagen          →  placeholder                ✗
```

Formato por tipo:

| Tipo | Formato | Densidad |
|---|---|---|
| Iconos, logos, formas vectoriales | SVG | — |
| Fotografía | JPG/WebP (o lo que sirva la plataforma) | @2x |
| Ilustración con transparencia | PNG/WebP | @2x |

El lote completo lo baja `/eden:download-figma-img`, con su manifiesto que enlaza cada archivo a su node-id.
Para uno o dos assets puntuales, se exportan directo.

---

## Diferencias entre breakpoints

**Una diferencia entre mobile y desktop en Figma es un requerimiento, no un error del diseñador**
(`rules/eden-design-rules.md`). Cada una se anota explícitamente en el Design Spec, con los dos valores.

Y cuando el diseño pide un tamaño de texto distinto por breakpoint y el componente del proyecto solo
expone un control, eso es un **hueco de configuración**, no una excusa para un override CSS sobre algo
compartido: se propone la variante responsive con default neutro y se espera la confirmación del dev
(`rules/eden-component-strategy-rules.md`).

---

## Cuando el Figma se contradice

Pasa: dos frames del mismo componente con medidas distintas, un estilo aplicado a medias, un texto que
no coincide con el copy del ticket. **No se decide por criterio propio y no se promedia.** Se saca a la
luz, se le muestran al dev las dos versiones con sus node-ids, y se pide la decisión
(`rules/eden-workflow-rules.md`).
