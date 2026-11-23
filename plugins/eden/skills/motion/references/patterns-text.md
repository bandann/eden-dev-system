# Textos — división, revelado, tipografía cinética, marquesina

## Dividir texto sin romper la lectura

- El contenedor conserva el texto completo para los lectores de pantalla y las piezas visuales van con
  `aria-hidden="true"`:

```html
<h2 class="{prefix}-split" aria-label="Built for every screen">
  <span aria-hidden="true"><span class="w">Built</span> <span class="w">for</span> …</span>
</h2>
```

- Por **palabra** o por **línea** siempre que se pueda; por letra solo en titulares cortos (muchas piezas =
  muchas capas). Las piezas animan `transform`/`opacity`, con `display: inline-block`.
- El texto viene de las traducciones del proyecto (locales de Shopify, `__()` de WordPress, i18n de
  React): la división se hace sobre el texto traducido, en el render o en el cliente, nunca con texto fijo.
- SplitText de GSAP (escalón 4) si hace falta dividir por líneas reales que cambian con el ancho; con
  `autoSplit`/revert al redimensionar y su modo accesible.

## Revelado por palabra

```css
@media (prefers-reduced-motion: no-preference) {
  .{prefix}-split .w { display: inline-block; animation: {prefix}-rise var(--{prefix}-duration-slow) var(--{prefix}-ease-out) both;
    animation-delay: calc(var(--i) * 40ms); }
}
@keyframes {prefix}-rise { from { opacity: 0; transform: translateY(.4em); } }
```

Si es el titular LCP, revelar con `transform` solo (sin `opacity: 0`), ver `patterns-heroes.md`.

## Tipografía cinética (una idea por frase)

Pocas palabras a la vez, resaltado con el color de acento del proyecto (token), cambios cortos. Útil en
secciones de "manifiesto"; con reduced-motion se muestra la frase completa.

## Marquesina

- CSS: dos copias del contenido en una pista con `animation: {prefix}-marquee linear infinite` sobre
  `transform: translateX(-50%)`; la segunda copia `aria-hidden="true"`.
- **Pausa** con hover/foco y un botón visible (se mueve sola más de 5 s), y quieta con reduced-motion.
- Velocidad por token y proporcional al ancho, no fija en segundos para cualquier largo.

## Efecto de escritura (máquina de escribir)

Solo decorativo: el texto completo está en el HTML (y en `aria-label`); la animación con `steps()` en CSS
o un `requestAnimationFrame` que se detiene con reduced-motion. No para textos largos ni para contenido
que el usuario necesita leer ya.
