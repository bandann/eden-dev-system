# Referencia — Lo que solo se ve mirando la página entera

Una sección puede estar 1:1 y la página seguir sin parecerse al Figma. Estas comprobaciones **no
existen** al revisar secciones por separado, y son la razón de ser de este skill.

---

## 1 · El orden y la presencia de las secciones

Lo primero, antes de medir un solo píxel:

- ¿Están **todas** las secciones que el Figma define para esta página?
- ¿Están **en el mismo orden vertical**?
- ¿Hay alguna en la página que **no** esté en el diseño?

```js
[...document.querySelectorAll('main > *, .shopify-section')]
  .map(el => ({ id: el.id || el.className, top: el.getBoundingClientRect().top }))
```

Una sección de más, de menos o fuera de orden **invalida el resto del informe**: se reporta primero y se
resuelve antes de seguir midiendo, porque puede que esté midiendo la sección equivocada.

---

## 2 · El espaciado ENTRE secciones

El fallo más común de una página que "está bien por partes". Cada sección puede tener su padding
correcto y aun así el ritmo vertical de la página estar mal, porque entre ellas hay margen colapsado,
un margen extra del tema, o falta el `gap` del contenedor.

Se mide la **distancia real entre cajas**, no la suma de paddings:

```js
const secs = [...document.querySelectorAll('main > *')];
secs.slice(0, -1).map((el, i) => {
  const a = el.getBoundingClientRect(), b = secs[i + 1].getBoundingClientRect();
  return { entre: `${el.className} → ${secs[i+1].className}`, gap: Math.round(b.top - a.bottom) };
})
```

Y se compara con la separación entre los frames correspondientes en Figma. **Figma no colapsa márgenes;
el navegador sí** — por eso se mide la distancia resultante y no los valores declarados.

---

## 3 · El contenedor y la alineación global

Todas las secciones que no son a sangre completa deben **compartir el mismo ancho de contenido y
alinear sus bordes**. Una sección con 16px más de padding lateral rompe la línea vertical de toda la
página, y eso se ve aunque cada sección pase su test por separado.

- Ancho de contenido real de cada sección (no el declarado).
- Que los bordes izquierdo y derecho **coincidan** entre secciones.
- Que las `alignfull` / a sangre completa sean exactamente las que el diseño marca.

---

## 4 · Header y footer

Se revisan **en la página**, no como componentes sueltos:

- Altura del header y si es sticky, cuándo se fija y cuánto ocupa entonces.
- Si el contenido de arriba queda **tapado** por el header al cargar o al anclar.
- Footer: separación con la última sección, y que no quede flotando en páginas cortas.

---

## 5 · Coherencia de tokens entre secciones

El hallazgo que solo aparece en el barrido completo: **dos secciones que usan valores distintos para lo
mismo**.

- Dos títulos del mismo nivel con tamaños diferentes sin que el diseño lo pida.
- El mismo gris con dos valores distintos en dos secciones.
- Un botón con radio de 8px en una sección y 6px en otra.

Cada caso es una de dos cosas, y hay que decir cuál: **una sección está mal**, o **el sistema de tokens
tiene un hueco**. La segunda es 🟡 (afecta a todo el proyecto) y la decide el dev.

---

## 6 · Scroll horizontal

En **cada** breakpoint. No hay excepción válida:

```js
({ overflow: document.documentElement.scrollWidth > window.innerWidth,
   por: [...document.querySelectorAll('*')]
     .filter(el => el.getBoundingClientRect().right > window.innerWidth + 1)
     .slice(0, 5).map(el => el.className) })
```

Se reporta **qué elemento** se sale, no solo que hay scroll. Aparece casi siempre en 375 y en 1280, que
son justo los anchos que más se saltan.

---

## 7 · La página en movimiento

Cosas que una captura estática no ve:

- **Al cargar**: saltos de layout (CLS) cuando entran fuentes e imágenes.
- **Al hacer scroll**: las animaciones de entrada disparan donde deben, y el header se comporta.
- **Entre breakpoints**: redimensionar de 1440 a 375 sin recargar — el reflujo coincide con el diseño y
  nada se rompe a mitad de camino.
- **Con `prefers-reduced-motion`**: la página sigue siendo usable y las animaciones se desactivan.

---

## 8 · Estados de la página, no solo del componente

El diseño suele definirlos y casi nunca se revisan en conjunto:

- La página con **contenido real largo** (títulos de dos líneas, descripciones extensas).
- La página con **contenido mínimo** (una colección con tres productos en vez de doce).
- **Sin imágenes** cargadas todavía.

Si el diseño define estos casos y la página se rompe en ellos, es una discrepancia como cualquier otra.

---

## Cómo se reporta esto

Aparte de las discrepancias por sección, porque tiene otra naturaleza y otro responsable:

```
📄 NIVEL PÁGINA

Orden y presencia    ✅ {n} secciones, en orden
Espaciado entre      ❌ hero → value-props: 48px · Figma 80px   (Δ -32px)
Contenedor           ✅ todas alinean a {n}px
Header / footer      ⚠️ el header sticky tapa 24px del hero al anclar
Coherencia tokens    ⚠️ 2 grises distintos para el mismo rol (§5)
Scroll horizontal    ❌ en 375: `.product-carousel__track` se sale 12px
Movimiento           ✅ sin CLS · reduced-motion respetado
```
