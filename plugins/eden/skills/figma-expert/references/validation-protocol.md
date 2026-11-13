# Validación — cómo se prueba que el código coincide con el diseño

Playwright no es un preview: es **la fuente autorizada de lo que el código realmente renderiza**. El CSS
escrito y el CSS computado no son lo mismo, así que **leer el código no reemplaza medir el render**.

La ejecuta el `design-auditor` (rol, nivel `fast`; el agente lo asigna el roster del stack). La sesión principal recibe los deltas, no las capturas ni los
árboles.

---

## Preparar

- El **viewport de Playwright es exactamente el del frame de Figma**. Figma 1440×900 → Playwright
  1440×900. Ni 1440×1080 "porque da igual": el alto cambia qué entra en el fold y cómo se comportan las
  alturas relativas.
- Se espera a que **las fuentes hayan cargado** antes de medir. Medir durante el swap de una webfont da
  números que no se repiten.
- Un viewport no se marca como validado hasta haberlo **inspeccionado**, no solo abierto.

---

## Los seis niveles, en orden

El orden importa: un fallo de nivel 2 explica veinte "fallos" de nivel 4.

### 1 · Layout global
Ancho y alto de página, contenedor principal, alineación horizontal, posición de cada sección,
espaciado entre secciones. Y que **no haya scroll horizontal** en ningún ancho.

### 2 · Tipografía — el nivel que hay que resolver primero
Familia **computada** (no la declarada), carga real de la fuente, tamaño, peso, line-height,
letter-spacing, dónde cortan las líneas.

Si Figma dice `Inter` y el navegador computa `Arial`, la implementación está mal **y todas las medidas
de abajo son ruido**: una fuente equivocada cambia anchos de texto, saltos de línea, altura de los
botones, alto de las secciones y el ritmo vertical entero. Se arregla la carga de la fuente **antes** de
tocar un solo espaciado.

### 3 · Componentes
Uno por uno: header, hero, tarjetas, botones, formularios, navegación, footer. Cada uno con sus estados.

### 4 · Espaciado
Padding, margin, gap, espaciado entre secciones y entre elementos. Los cuatro lados, por separado.

### 5 · Propiedades visuales
Colores (**y que vengan del token**, no hardcodeados — un color correcto pero hardcodeado falla el
test), bordes, radios, sombras, gradientes, opacidad, fondos.

### 6 · Media
Tamaño de la imagen, recorte, `object-position`, aspect-ratio, dimensiones de los SVG, iconos.

---

## Cómo se mide de verdad

Las capturas por sí solas no bastan. Para cada elemento relevante:

```javascript
const box = await element.boundingBox();          // x, y, width, height reales
const cs  = await element.evaluate(el => {
  const s = getComputedStyle(el);
  return {
    fontFamily: s.fontFamily, fontSize: s.fontSize, fontWeight: s.fontWeight,
    lineHeight: s.lineHeight, letterSpacing: s.letterSpacing,
    padding: s.padding, margin: s.margin, gap: s.gap,
    color: s.color, backgroundColor: s.backgroundColor,
    borderRadius: s.borderRadius, boxShadow: s.boxShadow,
    objectFit: s.objectFit, objectPosition: s.objectPosition,
  };
});
```

Y se compara **esperado (Design Spec) vs medido (navegador)**:

```
Figma      width 1200 · height 400 · x 120 · y 200
Navegador  width 1184 · height 400 · x 128 · y 200
                  ^ -16              ^ +8
```

Eso es una discrepancia. **No se ignora.** Se investiga su causa — aquí, casi con seguridad, un padding
del contenedor que no está en el spec.

---

## Clasificar antes de tocar

Toda diferencia se etiqueta antes de intentar arreglarla:

```
POSITION · SIZE · SPACING · TYPOGRAPHY · COLOR · BORDER · RADIUS
SHADOW · IMAGE · RESPONSIVE · CONTENT · INTERACTION
```

```
Problema    El título del hero está 12px más abajo que en Figma
Categoría   POSITION
Esperado    y = 184
Medido      y = 196
Delta       +12
Causa raíz  margin-top heredado del h1 del tema, no reseteado en el bloque
```

Sin causa raíz no se corrige: cambiar el `margin-top` del título cuando el problema era el padding del
contenedor deja el número bien y el bloque mal.

---

## Un cambio a la vez

1. Identificar la discrepancia.
2. Identificar la causa raíz probable.
3. Cambiar **la propiedad mínima necesaria**.
4. Volver a medir.
5. Confirmar que mejoró — y que no empeoró nada más.
6. Seguir.

Tocar cinco propiedades y ver si el conjunto mejora no es depurar: es perder la trazabilidad de qué
arregló qué.

---

## Volver a medir lo que se pudo mover

Después de cada corrección se revalida:

- el propio elemento,
- **lo que está encima y debajo** — corregir un padding desplaza todo lo que sigue,
- **todos los breakpoints** — arreglar desktop sin verificar mobile es como se arregla una cosa y se
  rompen dos.

---

## Comparación de imagen y overlay

Cuando se quiera precisión por encima de la inspección subjetiva:

- Captura de Playwright **en el tamaño exacto del frame** de Figma.
- Captura del nodo de Figma (`figma_take_screenshot` / `figma_capture_screenshot`).
- Superposición con transparencia, o imagen de diferencia.

El overlay revela lo que la mirada perdona: desalineaciones, espaciados de más, desplazamientos
tipográficos, recortes de imagen equivocados, alturas de sección que no cierran.

---

## Tolerancia

**Objetivo: 0 desviación intencional.**

Puede haber diferencias sub-pixel por rasterización o antialiasing. Lo que **no** puede haber es un CSS
incorrecto justificado como "así renderiza el navegador". Si la diferencia la causa la implementación,
se corrige.

---

## Matrices — no se marca lo que no se inspeccionó

| Viewport | Figma | Playwright | Estado |
|---|---|---|---|
| Desktop | 1440×900 | 1440×900 | ⬜ |
| Tablet | 768×1024 | 768×1024 | ⬜ |
| Mobile | 390×844 | 390×844 | ⬜ |

| Componente | Desktop | Tablet | Mobile |
|---|---|---|---|
| Header | ⬜ | ⬜ | ⬜ |
| Hero | ⬜ | ⬜ | ⬜ |
| Cards | ⬜ | ⬜ | ⬜ |
| CTA | ⬜ | ⬜ | ⬜ |
| Footer | ⬜ | ⬜ | ⬜ |

---

## Cómo se cierra

De dos formas, nunca de una tercera:

- ✅ **1:1 en todos los breakpoints medidos**, diciendo **cuántos elementos** se midieron y adjuntando
  las capturas finales. Una validación sin captura no se declara hecha.
- ⚠️ **Declarado**: qué no coincide, por qué, y qué haría falta para resolverlo. No se aproxima y no se
  redondea a "quedó bien".

Si Playwright no responde, **se dice y se detiene la validación**. No se sustituye por una lectura del
código.
