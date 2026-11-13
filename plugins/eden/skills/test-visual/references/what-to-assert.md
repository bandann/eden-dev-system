# Referencia — Qué se asevera y cómo medirlo

Siete grupos. Ninguno es opcional cuando el diseño lo define.

---

## 🎨 Color

```js
const s = getComputedStyle(el);
({ color: s.color, background: s.backgroundColor, border: s.borderColor })
```

**Doble aserto, siempre:**

1. **Valor computado** — que en pantalla sea el correcto.
2. **Procedencia** — que venga de una custom property. Se comprueba sobre la regla, no sobre el
   computado (el computado ya resolvió la variable):

```js
// ¿La declaración usa var()?
[...document.styleSheets].flatMap(sh => { try { return [...sh.cssRules] } catch { return [] } })
  .filter(r => r.selectorText && el.matches(r.selectorText))
  .map(r => r.style.color)   // "var(--color-text-primary)" vs "#1a1a1a"
```

**Un color correcto pero hardcodeado falla.** Es el hallazgo que el ojo nunca ve y que rompe el sistema
cuando cambia el esquema.

Comparar en el mismo espacio de color: el navegador devuelve `rgb()`/`rgba()`; Figma da hex con
opacidad. Se normaliza antes de comparar.

---

## 🔤 Tipografía

`fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `textTransform`, `textAlign`.

Trampas que producen falsos fallos — resuélvelas antes de reportar:

- **`line-height`**: Figma lo da en px o %; el navegador en px o `normal`. Convierte a la misma unidad.
- **`letter-spacing`**: Figma suele darlo en % del tamaño de fuente; el navegador en px.
- **`font-weight`**: Figma dice `Semi Bold`, el CSS dice `600`.
- **`font-family`**: el computado trae la pila completa. Compara **la primera familia efectiva**, y
  verifica que la fuente realmente cargó (`document.fonts.check()`), no solo que esté declarada.

**Sin esperar a `document.fonts.ready` todos estos valores son falsos.**

---

## 📐 Espaciado

`paddingTop/Right/Bottom/Left`, `marginTop/…`, `gap`, `rowGap`, `columnGap`.

- Figma **no colapsa márgenes**; el navegador sí. Si dos márgenes verticales colapsan, el espacio real
  entre elementos puede ser correcto aunque los valores no coincidan: **mide la distancia entre cajas**
  antes de reportar.
- El espaciado del auto-layout de Figma puede implementarse con `gap` o con `margin`. El baseline
  asevera **el resultado** (la separación real), y opcionalmente la propiedad si el diseño del código lo
  exige.

---

## 📏 Dimensiones

`getBoundingClientRect()` → `width`, `height`. Más `maxWidth` del contenedor y `aspectRatio`.

Tolerancia: **< 1px se ignora** (redondeo de renderizado). Todo lo demás se reporta.

Ojo con los elementos de altura automática: su alto depende del contenido. Si el baseline fija una
altura que en realidad es consecuencia del texto, el test fallará con cualquier copy distinto — asevera
lo que el diseño **impone**, no lo que resulta.

---

## 🎬 Animación

```js
const s = getComputedStyle(el);
({
  transitionProperty: s.transitionProperty,
  transitionDuration: s.transitionDuration,
  transitionTimingFunction: s.transitionTimingFunction,
  transitionDelay: s.transitionDelay,
  animationName: s.animationName,
  animationDuration: s.animationDuration,
})
```

Y el aserto que casi nadie escribe: **`prefers-reduced-motion`**. Se emula la preferencia y se verifica
que la animación se desactiva o se reduce:

```
browser_resize / emulación de prefers-reduced-motion: reduce
→ transitionDuration debe ser "0s" (o lo que declare el baseline)
```

Una animación sin salida para reduced-motion **falla el test**, aunque se vea preciosa. Es requisito de
accesibilidad, no preferencia.

Para animaciones de entrada (scroll, aparición): se mide **con la animación terminada**, no a mitad.

---

## 📱 Responsive

Todo lo anterior, **en cada breakpoint del baseline**. Si el perfil activo declara `qa.breakpoints`,
se prueban todos esos anchos.

Además del valor por breakpoint, dos asertos propios del responsive:

- **El reflujo**: que el orden y la disposición cambien como el diseño dice (3 columnas → 1, elementos
  que se ocultan, orden que se invierte).
- **Que no haya scroll horizontal** en ningún ancho: `document.body.scrollWidth <= window.innerWidth`.

---

## 🖼️ Imágenes

Presencia, tamaño renderizado, `aspect-ratio`, `object-fit`, `alt` presente y descriptivo, `width`/
`height` en el marcado (sin CLS) y `loading="lazy"` bajo el fold.

Una imagen del tamaño correcto sin `width`/`height` **falla**: pasa el ojo y falla en Core Web Vitals.

---

## Cómo se reporta un fallo

Con las tres cosas que permiten arreglarlo sin buscar:

```
❌ {nodo} · {propiedad}
   esperado {valor}  ← baseline, Figma {node-id}
   actual   {valor}
   Δ        {diferencia}
   dónde    {archivo:línea}
```

Sin `archivo:línea` el dev tiene que buscarlo otra vez, y ahí se pierde la mitad del valor del test.

## Lo que se reporta como "no medido"

- El nodo no existe en el DOM.
- Playwright no pudo cargar la página.
- La propiedad depende de un estado que no se pudo reproducir.

**Nunca se cuenta como verde.** Un test con huecos declarados es útil; uno que oculta los huecos, no.
