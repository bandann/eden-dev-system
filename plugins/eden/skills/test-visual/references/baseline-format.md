# Referencia — El baseline visual

El baseline es **el contrato del diseño en formato ejecutable**. Se deriva de Figma, se versiona y se
revisa en el PR igual que el código.

## Dónde vive

```
tests/visual/{section}.baseline.json
```

Si el proyecto ya tiene una carpeta de tests, **manda el proyecto**. Lo que no cambia: se versiona.

## Formato

```json
{
  "section": "hero-banner",
  "source": {
    "figma_file": "3HpB6uC6Pqexv8zQlwaK4w",
    "figma_version": "1234567890",
    "nodes": { "mobile": "12:340", "desktop": "12:118" },
    "derived": "2026-09-04"
  },
  "url": "/",
  "selector": ".hero-banner",

  "breakpoints": {
    "mobile": 375,
    "desktop": 1440
  },

  "nodes": [
    {
      "name": "container",
      "selector": ".hero-banner",
      "assert": {
        "mobile":  { "maxWidth": "343px", "padding": ["24px","16px","24px","16px"] },
        "desktop": { "maxWidth": "1200px", "padding": ["80px","40px","80px","40px"] }
      }
    },
    {
      "name": "title",
      "selector": ".hero-banner__title",
      "assert": {
        "mobile":  { "fontSize": "28px", "lineHeight": "34px" },
        "desktop": { "fontSize": "48px", "lineHeight": "56px" },
        "all": {
          "fontFamily": "var(--font-heading--family)",
          "fontWeight": "700",
          "letterSpacing": "-0.02em",
          "color": { "token": "--color-text-primary", "computed": "rgb(26, 26, 26)" }
        }
      }
    },
    {
      "name": "cta",
      "selector": ".hero-banner__cta",
      "assert": {
        "all": {
          "backgroundColor": { "token": "--color-primary" },
          "borderRadius": "8px",
          "transition": { "property": "background-color", "duration": "200ms", "easing": "ease-out" }
        },
        "states": {
          "hover": { "backgroundColor": { "token": "--color-primary-hover" } },
          "focus": { "outlineWidth": "2px" }
        },
        "reducedMotion": { "transition": "none" }
      }
    }
  ]
}
```

## Las claves del formato

**`all` vs. por breakpoint.** Lo que no cambia entre anchos va en `all`; lo que cambia, en su
breakpoint. Así el baseline documenta **qué es responsive y qué no** — y si algo debería cambiar y está
en `all`, se ve de un vistazo.

**Color con `token` y `computed`.** Los dos, y los dos se verifican:

- `computed` — que el color en pantalla sea el correcto.
- `token` — que **venga de la custom property**. Un color correcto pero hardcodeado **falla**: coincide
  hoy y se rompe cuando cambie el esquema.

**`states`.** Hover, focus, disabled, active. Se verifican con el elemento en ese estado, no leyendo la
regla CSS.

**`reducedMotion`.** Qué debe pasar con `prefers-reduced-motion: reduce`. Si el baseline declara una
animación y no declara su comportamiento reducido, **está incompleto**.

**`source`.** De qué nodo y de qué **versión** de Figma salió. Es lo que permite saber, meses después,
si el baseline sigue reflejando el diseño vigente.

## Cómo se deriva

1. El `design-extractor` (rol) sobre el nodo, por breakpoint (obligatorio delegarlo).
2. Cada propiedad medida → un aserto.
3. Los colores se buscan **primero como token del proyecto** (`docs/design-system.md`); solo si no hay
   token equivalente se escribe el valor crudo, **y se marca como hueco** para revisar con diseño.
4. Se anota la versión del archivo de Figma.

## Reglas

- **No se edita a mano para que pase un test.** Si el diseño cambió, se re-deriva desde Figma con
  `test-visual update` y se muestra el diff.
- **No se asevera lo que no se midió.** Un baseline con valores inventados es peor que no tenerlo:
  convierte el test en teatro.
- **Un nodo del diseño sin aserto es un hueco.** Si algo del Figma no se puede medir en el DOM, se
  anota en el baseline como `"skipped": "motivo"` — visible, no omitido en silencio.
- El baseline **se commitea**. Un contrato que solo existe en la máquina de un dev no es un contrato.
