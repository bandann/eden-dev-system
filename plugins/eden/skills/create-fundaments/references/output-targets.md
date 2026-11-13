# Referencia — Dónde se escriben los fundamentos

Los fundamentos existen en **cuatro artefactos** y los cuatro deben estar sincronizados. Si falta uno,
el proyecto no tiene fundamentos completos.

| # | Artefacto | Para quién |
|---|---|---|
| 1 | Tokens en código | El navegador — es la verdad de ejecución |
| 2 | `docs/design-system.md` | El equipo — la verdad consultable |
| 3 | `.claude/project-config.json` | Los skills y el `design-auditor` (rol) |
| 4 | Bloque en `CLAUDE.md` | Claude, cada sesión |

Todos terminan con el marcador:

```
<!-- eden-fundaments: updated=YYYY-MM-DD figma={file_key} version={figma_version_id} -->
```

---

## 1. Tokens en código — por stack

**Regla que manda sobre todo lo demás: si el proyecto ya tiene un lugar para los tokens, ese es el
lugar.** Lo de abajo es qué proponer cuando no lo hay — y se confirma con el dev antes de escribir.

### Shopify

**El procedimiento completo está en `shopify-integration.md` — síguelo, no improvises aquí.** Resumen:

- El tema **ya tiene** sistema de tokens (`settings_schema.json` → custom properties). Se llena el que
  existe; no se crea uno paralelo.
- La decisión por cada fundamento: **¿lo cambia el merchant?** Sí → setting del tema con default igual
  al valor del Figma. No → snippet propio del proyecto (`snippets/{prefix}-design-tokens.liquid`, prefijo
  `--{prefix}-`, renderizado después del snippet de variables del tema).
- Los esquemas de color del Figma se mapean **uno a uno** a los `color_scheme` del tema. Cambiar el
  valor de un esquema existente repinta todas las secciones: es conflicto, lo decide el dev.
- El snippet de variables del tema suele ser **autogenerado**: no se edita a mano.

### WordPress

**El procedimiento completo está en `wordpress-integration.md` — síguelo, no improvises aquí.** Dónde
se llena depende del **sabor** (`wordpress.flavor`), y equivocarse de sitio deja el proyecto con dos
sistemas de tokens compitiendo:

- **block-theme** → `settings` del `theme.json` del child theme. Es el sistema nativo: WordPress genera
  solo las variables `--wp--preset--*`, las clases y los controles del editor. La tipografía por
  breakpoint se resuelve con `fluid` (min/max), sin settings pareados.
- **classic-theme** → un único archivo de custom properties propias del child theme (prefijo `--{prefix}-`),
  encolado antes que todo lo demás. Lo que deba cambiar el cliente va al Customizer con default neutro.
- **page-builder** → los globales del builder (Global Colors/Fonts). Viven en la **base de datos**, así
  que `docs/design-system.md` es aquí el único registro revisable de qué valor tiene cada token.
- **headless** → los tokens son del front; WordPress no participa (ver el bloque de frameworks abajo).

⚠️ En los tres primeros, cambiar un token que ya está en uso **repinta páginas publicadas**. Es un
conflicto: lo decide el dev.

### Next / React / Astro / Vue

- El archivo de tokens que el proyecto ya use: `tokens.css`, `theme.css`, `globals.css`,
  configuración de Tailwind, o el archivo de tema del design system.
- Con Tailwind: los tokens van a la **configuración del tema**, no a clases arbitrarias sueltas.
- Si hay CSS-in-JS o un objeto de tema, los tokens van ahí — no en un `:root` paralelo que compita.

### WordPress

- `theme.json` cuando el tema lo soporte (es el mecanismo nativo); si no, el archivo de variables del
  tema.

### Genérico (sin convención previa)

Un único `:root` con custom properties, en el archivo de estilos base, cargado antes que todo lo demás:

```css
:root {
  /* Primitives */
  --color-brand-500: #…;

  /* Semantic */
  --color-text-primary: var(--color-brand-900);

  /* Typography */
  --font-body--family: …;
  --font-h1--size: …;

  /* Spacing */
  --spacing-md: …;

  /* Radius / shadow */
  --radius-md: …;
}
```

Primitivos y semánticos separados y comentados. Los componentes consumen **semánticos**.

---

## 2. `docs/design-system.md`

En **inglés** (convención de `docs/`). Estructura:

```markdown
# Design System — {project}

Source: Figma {url} · version {id} · extracted {date}

## Color
| Token | Value (light) | Value (dark) | Figma name | Use for |

## Typography
| Token | Family | Size (mobile) | Size (desktop) | Weight | Line-height | Letter-spacing | Use for |

## Spacing
| Token | Value | Notes |
(declared in Figma variables / inferred from N components)

## Breakpoints & grid
| Breakpoint | Width | Columns | Gutter | Margin | Max container |

## Radius · Shadows · Icons

## States
hover / focus / disabled / error / success

## Gaps
What the Figma design system does NOT define yet.

## Figma ↔ project equivalences
| Figma variable | Project token | Note |
```

La sección **Gaps** no es opcional: es la lista de preguntas abiertas para el diseñador.

---

## 3. `.claude/project-config.json`

Se rellenan, como mínimo:

```json
{
  "figma": { "file_key": "…", "url_desktop": "…", "url_mobile": "…" },
  "breakpoints": { "mobile": 375, "tablet": 768, "desktop": 1440 },
  "design_system": {
    "status": "installed",
    "tokens_path": "…",
    "doc_path": "docs/design-system.md",
    "figma_version": "…",
    "updated": "YYYY-MM-DD"
  }
}
```

Los **breakpoints son los anchos exactos de los frames de Figma**. El `design-auditor` mide con ellos:
un ancho mal copiado invalida todo el QA de diseño del proyecto.

---

## 4. Bloque en `CLAUDE.md`

Se rellena la sección "Sistema de diseño de este proyecto" de `CLAUDE.base.md` con **valores reales**,
no placeholders: URLs de Figma, breakpoints, familias de tokens, y si el proyecto es fluido o de escala
fija. Es lo que Claude lee cada sesión, así que va resumido — el detalle vive en
`docs/design-system.md`, enlazado desde ahí.

---

## Reglas de escritura

- **Aditivo, nunca destructivo.** Nada existente se borra ni se redefine sin aprobación explícita.
- **Instalar los fundamentos no debe cambiar nada visualmente.** Si al agregarlos el sitio se ve
  distinto, algo se pisó: revísalo antes de continuar.
- Se commitea en la rama de trabajo, nunca directo a una rama protegida.
- Si el proyecto no compila o el validador falla después de escribir, se revierte y se reporta.
