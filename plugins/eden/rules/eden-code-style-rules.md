# Reglas de estilo de código — Eden

Aplica a cualquier stack. Lo específico de Shopify está en `shopify/eden-shopify-rules.md`.

> **Regla cero: sigue el proyecto.** Si el proyecto ya tiene una convención distinta a la de abajo, gana
> el proyecto. La consistencia vale más que la preferencia.

---

## CSS — metodología BEM

### Nomenclatura

`bloque__elemento--modificador`

- **Bloque**: componente independiente (`header`, `card`, `product-grid`).
- **Elemento**: parte de un bloque (`header__logo`, `card__title`).
- **Modificador**: variación (`card--featured`, `card__title--large`).

### Formato

- Indentación de 2 espacios, una propiedad por línea.
- **Mobile-first**: estilos base para mobile, `@media` para arriba.
- Orden de propiedades: posicionamiento → box model → tipografía → visual → resto.

### Variables

- **Nunca hardcodear colores ni valores de fuente**: siempre custom properties del proyecto.
- Los nombres propios del cliente (tokens, funciones, bloques) llevan el prefijo del proyecto
  (`project.prefix`), nunca el del kit. Ver "Prefijo del proyecto" en `eden-stack-rules.md`.
- Los estilos viven donde el proyecto los pone (acotados al componente, o en su archivo por
  componente). No inventes una tercera ubicación.

### Prohibido

- `!important` (salvo para pisar código de terceros).
- IDs como selector de estilo.
- Anidar más de 3 niveles.
- Selectores de etiqueta para estilar (`div {}`, `p {}`, `a {}`).
- Estilos inline.
- Clases genéricas (`.container`, `.wrapper`) sin prefijo del bloque.

### Alcance de los cambios

**Solo se formatea o arregla el código que nosotros escribimos o modificamos.** Si un archivo tiene
formato inconsistente heredado, se deja como está salvo que estemos trabajando en ese bloque. Nuestro
código queda limpio aunque el de alrededor no lo esté.

```css
/* ========================================
   Product Card
   ======================================== */

.product-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.product-card__title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.product-card--featured {
  border: 2px solid var(--color-accent);
}

@media (min-width: 750px) {
  .product-card {
    flex-direction: row;
  }
}
```

---

## JavaScript

### Arquitectura

- Web Components nativos (Custom Elements) para UI interactiva, cuando el proyecto lo permita.
- **Light DOM únicamente — nada de Shadow DOM.** Rompe el renderizado de plantillas y los estilos BEM
  globales.
- Un componente = una clase que extiende `HTMLElement`, registrada con `customElements.define`.
- El nombre del componente lleva guion: `product-card`, `cart-drawer`.
- **Sigue los patrones de JS que el proyecto ya usa.**

### Datos desde la plantilla al componente

Un `<script type="application/json">` dentro del componente para traducciones, settings o datos
dinámicos; se lee en `connectedCallback`. Nunca datos incrustados en atributos ilegibles ni variables
globales.

### Estructura

- Un archivo por componente, con nombre que coincida con el componente.
- Utilidades compartidas en un módulo común.

### Prohibido

- jQuery.
- `var` (usa `const`, y `let` cuando haga falta).
- `console.log` o `debugger` en código que se sube.
- Handlers inline (`onclick=""`).
- Shadow DOM.
- Dejar listeners sin limpiar al desmontar.

### Plantilla

```javascript
class ProductCard extends HTMLElement {
  constructor() {
    super();
    // cachear referencias del DOM y parsear el JSON de datos
  }

  connectedCallback() {
    this.init();
  }

  disconnectedCallback() {
    // limpiar listeners y observers
  }

  init() {
    // lógica del componente
  }
}

customElements.define('product-card', ProductCard);
```

---

## Plantillas / markup

- HTML semántico: `header`, `nav`, `main`, `section`, `article`, `aside`, `footer`. **No un `div` para
  todo.**
- Jerarquía de encabezados sin saltos.
- Todo texto visible pasa por el sistema de traducciones del proyecto. **Nunca hardcodeado.**
- Contenido generado por usuarios siempre escapado.
- La lógica pesada no va en la plantilla: se mueve a donde el proyecto ponga la lógica.

---

## Reutilizar antes de crear

Antes de crear cualquier componente, revisa si ya existe uno que haga lo necesario. Si existe, se
reutiliza y se ajusta por configuración. Solo se crea algo nuevo cuando nada existente sirve.
Ver `eden-component-strategy-rules.md`.
