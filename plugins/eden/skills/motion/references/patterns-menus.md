# Menús — drawer, mega menú, submenús

## Lo que tiene que cumplir siempre

- `aria-expanded` en el disparador, `Esc` cierra, el foco entra al abrir y **vuelve al disparador** al
  cerrar; en el drawer móvil el foco no sale del panel mientras está abierto (`inert` en el resto).
- Animan `transform` (deslizar) y `opacity`; el fondo oscuro, `opacity`. Nunca `left`/`width`.
- El scroll del body se bloquea sin saltos de layout (`scrollbar-gutter: stable` o compensar el ancho).
- Con `prefers-reduced-motion`: aparece y desaparece con un fundido corto o sin transición.

## Drawer móvil con `<dialog>` (escalón 1)

```css
.{prefix}-drawer { inset: 0 auto 0 0; height: 100dvh; max-height: none; margin: 0; width: min(88vw, 420px);
  transform: translateX(-100%); transition: transform var(--{prefix}-duration-base) var(--{prefix}-ease-out),
  display var(--{prefix}-duration-base) allow-discrete, overlay var(--{prefix}-duration-base) allow-discrete; }
.{prefix}-drawer[open] { transform: none; }
@starting-style { .{prefix}-drawer[open] { transform: translateX(-100%); } }
.{prefix}-drawer::backdrop { background: rgb(0 0 0 / .5); opacity: 0; transition: opacity var(--{prefix}-duration-base), display var(--{prefix}-duration-base) allow-discrete, overlay var(--{prefix}-duration-base) allow-discrete; }
.{prefix}-drawer[open]::backdrop { opacity: 1; }
@starting-style { .{prefix}-drawer[open]::backdrop { opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .{prefix}-drawer, .{prefix}-drawer::backdrop { transition-duration: 1ms; } }
```

`showModal()` da el foco atrapado, `Esc` y el `inert` del resto gratis. Al cerrar, devolver el foco al
botón que lo abrió.

## Mega menú en desktop

- Apertura por **clic** (y hover con intención: retraso de entrada ~150 ms y de salida ~300 ms para no
  cerrar al cruzar en diagonal), nunca solo hover: teclado y táctil también abren.
- Panel con `clip-path: inset(0 0 100% 0)` → `inset(0)` o `transform: translateY(-8px)` + `opacity`.
- Los ítems internos, escalonados con `transition-delay: calc(var(--i) * 30ms)` (máx. ~8 ítems; el resto
  sin retraso). En reduced-motion, sin escalonado.
- Imágenes del menú con `loading="lazy"` y tamaño reservado.

## Indicador del ítem activo

Un solo elemento que se mueve con `transform: translateX()` y `scaleX()` (o View Transitions con
`view-transition-name`) en vez de animar el `border` de cada ítem.
