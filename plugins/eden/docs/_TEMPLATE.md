# {Nombre del componente / feature}

> Plantilla de documentación de Eden. Se crea un doc por componente, sección o feature con
> configuración, campos de datos o lógica no obvia. Se escribe **en inglés** (convención del equipo
> para `docs/`).

**File(s):** `{path}`
**Ticket:** {url}
**Added:** {YYYY-MM-DD}

## What it does

{One paragraph: the purpose and where it is used.}

## Settings / props

| Name | Type | Default | What it does |
|---|---|---|---|
| `{name}` | `{type}` | `{default}` | {description — and note that the default reproduces the previous behavior} |

## Data / fields

| Namespace · Key | Type | Required | Fallback when empty |
|---|---|---|---|
| `{ns.key}` | `{type}` | yes/no | {what renders} |

{What the client/merchant must create in their admin, if anything.}

## Design

- **Figma:** {url}
- **Breakpoints:** mobile {x}px · tablet {x}px · desktop {x}px
- **Tokens used:** {list}
- **Responsive behavior:** {what changes between breakpoints}

## Dependencies

{Snippets, components, scripts or styles it relies on — and who else consumes them.}

## Gotchas

{Non-obvious behavior, known limitations, things that will bite the next dev.}

## How to test

1. {step}
2. {step}
3. Expected: {result}
