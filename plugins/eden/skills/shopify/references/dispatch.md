# Dispatch — cómo reparte el líder

## 1. Partir en unidades

Una unidad = **un encargo para un especialista**: un resultado observable, un dueño, una lista cerrada
de archivos.

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Un setting nuevo, un ajuste de estilos en una sección | Un especialista, sin loop de diseño si no es visual |
| **M** | Una sección nueva con sus bloques | theme-dev (+ js-dev si hay interacción) + design-auditor en loop |
| **L** | Una página, o un componente compartido (carrito, header) | Varias unidades M, con dependencias declaradas |
| **XL** | Un proyecto o un rediseño | Se parte en lotes L (ver `lifecycle.md` § Build por lotes) |

Una unidad que cruza dueños de archivos (roster § Propiedad) **se parte**: primero el markup y el
schema (theme-dev), después el JS (js-dev) con el contrato de atributos que dejó el primero.

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa | `eden:shopify-architect` |
| Tokens, esquemas de color, `settings_schema.json` | `eden:shopify-design-system` |
| Liquid, schema, bloques, plantillas JSON, locales, CSS de sección | `eden:shopify-theme-dev` |
| Web Components, carrito, variantes, Section Rendering API | `eden:shopify-js-dev` |
| Metafields, metaobjects, GraphQL, apps, Markets, JSON-LD, import | `eden:shopify-data` |
| Entorno, CLI, config, validación | `eden:shopify-devops` |
| Figma → Design Spec | `eden:figma-extractor` |
| Medir Figma vs render | `eden:design-auditor` |
| Revisar el diff | `eden:shopify-qa-reviewer` |
| Performance, accesibilidad, SEO, analytics | `eden:shopify-perf-seo-a11y` |

`layout/theme.liquid` y cualquier archivo global: el líder decide el dueño y lo escribe en el plan.

## 3. Plantilla del plan (al dev, en español)

```
🛍️ PLAN DEL EQUIPO SHOPIFY

Trabajo: {new | onboard | task} · {ticket / descripción}
Fase: {fase del ciclo} {(Pn del perfil)}
Rama: {nombre} desde {base — preguntada}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | … | M | eden:shopify-theme-dev | sections/x.liquid, locales/en.default.json | 3 — setting con default neutro | — |
| 2 | … | S | eden:shopify-js-dev | assets/x.js | 4 | 1 |

En paralelo: {1 ∥ 3} · En secuencia: {1 → 2}
Verificación: design-auditor en {unidades visuales} · reviewer + quality-auditor al final
Paro a preguntarte en: {cambios compartidos, Admin, theme dev/pull, settings_data}
Blast radius: {consumidores y páginas — de architect}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

Las cinco partes de `rules/eden-model-strategy-rules.md`, más el contexto del equipo:

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: Design Spec .claude/context/design-spec-{x}.md · tokens {…} · reuse step {n}: {why} ·
      sibling pattern to follow: {file} · consumers: {from architect}
ACCEPT WHEN: {verifiable: Theme Check 0 errors, renders X at 375/768/1440, default keeps current look}
DO NOT: touch other files; theme push (never); published theme; settings_data.json; Admin changes;
        {unit-specific temptations}
AUTHORIZED BY THE DEV: {none | e.g. "shopify theme dev --theme 1234" on 2026-09-28}
HANDOFF: teams/shopify/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

- Solo unidades con **archivos disjuntos**, lanzadas **en un solo turno**.
- Máximo razonable: 4 especialistas a la vez. Más que eso satura la revisión del líder, que es donde
  se atrapan los errores.
- En primer plano los que usan MCP (Figma, Playwright) o lanzan otros agentes; en segundo plano solo
  lecturas locales (ver `skills/go/SKILL.md` § Paso 6).

## 6. Al recibir un handoff

1. `git diff -- {archivos del encargo}`: ¿tocó solo lo suyo? ¿Coincide con lo que reporta?
2. ¿El default nuevo reproduce lo actual? ¿Hay texto hardcodeado, hex, `!important`?
3. `DECISIÓN PENDIENTE` → al dev, tal cual.
4. Visual → `eden:design-auditor` → el mismo dueño corrige → medir otra vez.
5. Checkpoint: unidad cerrada, archivos, decisiones.
