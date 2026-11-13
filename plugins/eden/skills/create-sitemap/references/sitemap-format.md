# Referencia — Formato de `docs/sitemap.md`

El artefacto se escribe **en inglés** (convención de `docs/`) y tiene que servir para dos cosas: que un
dev nuevo entienda la tienda en cinco minutos, y que cualquier tarea pueda anclarse a una sección sin
volver a explorar el Figma.

## Identidad de una sección: el NODE-SECTION

Cada sección del sitio se identifica por:

```
{page}/{section-slug}
```

y lleva su `node-id` de Figma **por breakpoint**. Ejemplo: `home/hero-banner` con
`mobile 12:340` y `desktop 12:118`.

Reglas:

- **Una sección = un NODE-SECTION**, aunque tenga un nodo por breakpoint. Mobile y desktop del mismo
  hero no son dos secciones.
- El `slug` sale del nombre en Figma, normalizado (minúsculas, guiones). Si el nombre en Figma es
  inútil (`Frame 231`), se propone uno descriptivo y **se anota que fue renombrado por nosotros**.
- Una sección que aparece en varias páginas se declara **una vez** en un bloque de secciones
  compartidas, y las páginas la referencian. Ahí es donde se ve el blast radius real.

## Estructura del documento

```markdown
# Sitemap — {project}

Sources: Figma {url} v{version} · theme {n} sections · tracker project {id} · generated {date}

## Overview

| | Count |
|---|---|
| Pages | {n} |
| Unique sections | {n} |
| ✅ built / 🔧 needs-work / ♻️ reusable / 🆕 to-build / 👻 orphan / ❓ undefined | {n}/{n}/{n}/{n}/{n}/{n} |

## Pages

### {Page name} — `{route}`

- **Template:** `templates/{file}.json`
- **Figma:** mobile `{node-id}` · desktop `{node-id}` {· tablet `{node-id}`}
- **Status:** {overall}

| # | Section (NODE-SECTION) | Figma (m / d) | Theme section | Status | Reuse | Ticket |
|---|---|---|---|---|---|---|
| 1 | `home/hero-banner` | 12:340 / 12:118 | `sections/hero.liquid` | ✅ built | — | — |
| 2 | `home/value-props` | 12:355 / 12:130 | — | 🆕 to-build | ♻️ base: `icon-row` (step 3: add settings) | CU-86ca17 |

**Specs**
- `home/value-props` — 3 columns desktop / 1 mobile; icon 48px; copy from tracker subtask #2.
  Figma annotation: "el icono cambia de color en hover".

**Gaps**
- `home/testimonials` — no mobile frame in Figma.

## Shared sections

Sections used on more than one page — changing them has blast radius.

| Section | Used on | Theme section | Status |
|---|---|---|---|
| `global/header` | all | `sections/header.liquid` | 🔧 needs-work |

## Findings

### 👻 Orphans — in the theme, not in the design
| Theme section | Used on | Note |

### ❓ Undefined — requested but not designed
| Section | Where it was requested | Question for design |

## Change log

| Date | Change | By |
|---|---|---|
| {date} | Initial sitemap | {dev} |

<!-- eden-sitemap: updated=YYYY-MM-DD figma={file_key} version={version_id} -->
```

## Reglas de escritura

- **El estado se justifica.** `♻️ reusable` sin decir qué sección es la base, o `🔧 needs-work` sin
  decir qué le falta, no sirve.
- **Los orphans no se borran.** Se reportan: puede ser código en uso que el diseño no cubrió, o basura.
  Lo decide el dev.
- **El change log no se pisa.** En `--refresh` se agrega una fila; no se reescribe la historia.
- El documento **no duplica el Design Spec** de cada sección. El sitemap dice *qué* y *dónde*; las
  medidas salen de Figma en cada tarea, con los fundamentos como base.
