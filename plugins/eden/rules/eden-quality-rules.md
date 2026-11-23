# Reglas de calidad — Eden (performance, accesibilidad y SEO)

No son un pulido final: son requisitos de construcción. Se cumplen en el primer intento, no en una
pasada posterior.

## Imágenes

- Usa el sistema de imágenes del proyecto (helpers/CDN), no `<img src>` crudo con rutas fijas.
- **Siempre** `srcset` para imágenes responsive.
- **Siempre** `loading="lazy"` en lo que está bajo el fold. Nunca todo eager.
- **Siempre** `width` y `height` para evitar saltos de layout (CLS).
- **Siempre** `alt` descriptivo. Vacío (`alt=""`) solo si la imagen es puramente decorativa.
- Formatos modernos (WebP/AVIF) cuando la plataforma los sirva.

## Scripts

- `defer` en todo lo no crítico; `type="module"` para componentes.
- Nunca un script en `<head>` sin `defer` o `async`.
- Carga diferida para componentes que no están en el viewport inicial.
- Cada script externo bloquea render: se agrega solo si es imprescindible.
- Nunca `document.write()`.

## Fuentes

- Precargar las fuentes críticas (`rel="preload" as="font" crossorigin`).
- Máximo 2–3 familias.
- `font-display: swap`.

## CSS

- CSS crítico inline para el contenido sobre el fold, cuando la plataforma lo permita.
- Archivos pequeños, divididos por componente.
- Nada de CSS global sin que la tarea lo pida.

## Accesibilidad (WCAG AA)

- Contraste suficiente en texto y UI significativa, **en todos los esquemas de color**.
- Todo interactivo es accesible por teclado: `<button>` y `<a>` reales, nunca divs clicables. Estado de
  foco visible.
- Todo input tiene su `<label>` asociado.
- ARIA solo cuando la semántica nativa no alcanza (`<details>`, `<dialog>` primero). Widgets propios con
  `aria-expanded`/`aria-controls`/`aria-label`; actualizaciones dinámicas con `aria-live`.
- `prefers-reduced-motion` respetado en toda animación. Todo lo demás de movimiento (técnica, rendimiento,
  tokens, accesibilidad): `eden-motion-rules.md`.
- Estados de foco, hover, disabled, carga y vacío existen y están diseñados.

## SEO

Los proyectos viven del tráfico orgánico. El SEO es requisito de build, no un extra:

- Jerarquía de encabezados correcta e ininterrumpida. El estilo se aplica con clases, nunca eligiendo un
  nivel equivocado.
- Texto real por encima de texto dentro de imágenes.
- Links rastreables (`<a href>`), nunca navegación solo por JS.
- **Los Core Web Vitals son factor de ranking**: las reglas de performance de arriba *son* las reglas de
  SEO.
- Los datos estructurados (JSON-LD) del proyecto se mantienen y se extienden — nunca se eliminan ni se
  duplican.
- El copy editable vive en configuración/traducciones para que se pueda ajustar sin tocar código.

## Nunca

- Saltarse el `alt` de una imagen.
- Saltarse el `label` de un input.
- Cargar todas las imágenes en eager.
- Introducir una animación sin salida para `prefers-reduced-motion`.
- Romper la jerarquía de encabezados por estética.
