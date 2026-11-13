# Referencia — Cómo se mide el render real

El objetivo es obtener del navegador los mismos números que el Figma declara, para poder restarlos. Se
mide **lo computado**, no lo que dice el CSS fuente.

## 1. Preparar el viewport

```
browser_resize  → ancho EXACTO del frame de Figma (375, 768, 1440… el que sea)
browser_navigate → URL donde la sección está renderizada
```

El ancho sale de `.claude/project-config.json` → `breakpoints`. **Nunca uno aproximado**: 390 en vez de
375 mueve todo lo que sea fluido y produce diferencias que no existen.

## 2. Esperar a que esté realmente listo

Medir antes de tiempo produce datos falsos, y es el error más común:

- **Fuentes**: hasta que carguen, el navegador usa la de respaldo → tamaño, line-height y ancho de
  texto salen mal. Espera a `document.fonts.ready`.
- **Imágenes**: sin cargar, alto y aspect-ratio son otros. Espera a que las imágenes de la sección
  tengan `complete === true`.
- **Animaciones de entrada**: si la sección anima al aparecer, mide cuando terminó — no a mitad.
- **Lazy loading**: haz scroll hasta la sección antes de medir, o lo que está bajo el fold no se
  renderiza.

```js
await document.fonts.ready;
await Promise.all([...document.querySelectorAll('img')]
  .filter(i => !i.complete)
  .map(i => new Promise(r => { i.onload = i.onerror = r; })));
```

## 3. Extraer las medidas

Con `browser_evaluate`, por cada elemento de interés:

```js
const el = document.querySelector('{selector}');
const r  = el.getBoundingClientRect();
const s  = getComputedStyle(el);
({
  width: r.width, height: r.height,
  padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft],
  margin:  [s.marginTop, s.marginRight, s.marginBottom, s.marginLeft],
  gap: s.gap, display: s.display,
  font: { family: s.fontFamily, size: s.fontSize, weight: s.fontWeight,
          lineHeight: s.lineHeight, letterSpacing: s.letterSpacing,
          transform: s.textTransform, align: s.textAlign },
  color: s.color, background: s.backgroundColor,
  border: [s.borderWidth, s.borderColor, s.borderRadius],
  shadow: s.boxShadow,
})
```

Para el **contenedor** de la sección, además: su ancho máximo real y los márgenes laterales — es donde
más se acumulan las diferencias.

## 4. Emparejar elementos Figma ↔ DOM

No siempre hay correspondencia 1:1 entre nodos de Figma y nodos del DOM (un auto-layout puede ser un
solo `div`, o dos). Empareja por **rol visual y posición**, no por estructura:

- El título de la sección con el elemento de texto que hace de título.
- La tarjeta del Figma con el elemento que la representa, aunque el DOM tenga un wrapper extra.

Cuando un elemento del Figma **no existe** en el DOM (o al revés), eso **es el hallazgo** y se reporta
como tal: no se fuerza un emparejamiento que no existe.

## 5. Tolerancias

| Diferencia | Qué hacer |
|---|---|
| **< 1px** | Se ignora — redondeo de renderizado |
| **1–2px** | Se reporta como menor; suele ser un token cercano pero equivocado |
| **> 2px** | Se reporta |
| **Tipografía** | Cualquier diferencia de tamaño, peso o line-height se reporta, aunque sea 1px |
| **Color** | Cualquier diferencia se reporta, por pequeña que sea |

Casos que parecen diferencias y no lo son — verifícalos antes de reportar:

- **line-height** en Figma suele venir en px o %, y el navegador lo puede dar en px o `normal`.
  Conviértelo a la misma unidad antes de comparar.
- **letter-spacing** en Figma a veces es porcentaje del tamaño de fuente; el navegador lo da en px.
- **font-weight** puede venir como nombre (`Semi Bold`) y en CSS como número (600).
- Figma no aplica **colapso de márgenes**; el navegador sí. Si dos márgenes verticales colapsan, el
  espacio resultante puede ser correcto aunque los valores no coincidan — mídelo entre elementos.

## 6. Cotejo visual

`browser_take_screenshot` de la sección al mismo ancho del frame, junto a
`figma_capture_screenshot` del nodo. La comparación visual **no reemplaza la medición**: sirve para
cazar lo que los números no cuentan (un elemento fuera de lugar, un orden distinto, algo que no se
renderiza). Los números son la evidencia; la captura es el contexto.

## 7. Localizar el código responsable

Cada diferencia se reporta con su `archivo:línea`. Para encontrarlo:

```bash
grep -rn "{clase-del-elemento}" --include="*.liquid" --include="*.css" --include="*.js" .
```

Un hallazgo sin la ubicación del código obliga al dev a buscarla otra vez, y ahí se pierde la mitad del
valor del informe.
