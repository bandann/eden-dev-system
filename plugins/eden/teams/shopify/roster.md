# Roster Shopify — el equipo

Líder: **`/eden:shopify`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`) `eden-shopify-*`.
Reglas del stack: `rules/shopify/eden-shopify-rules.md`. Contrato común: `rules/eden-team-rules.md`.

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:shopify-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe |
| `architect` | `eden:shopify-architect` (modo `audit` / `decide`) | Onboarding de un tema avanzado; decisión del escalón reuse-first |
| `design-extractor` | `eden:figma-extractor` | Todo trabajo visual con Figma |
| `web-extractor` | `eden:web-extractor` | `/eden:w2shopify`: medir un sitio en vivo con Playwright (solo lectura) |
| `design-system` | `eden:shopify-design-system` | Fundamentos: `settings_schema`, esquemas de color, tokens |
| `implementer` | `eden:shopify-theme-dev` / `eden:shopify-js-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:shopify-data` | Metafields, metaobjects, Admin GraphQL, apps, Markets, JSON-LD, import de producto |
| `devops` | `eden:shopify-devops` | Setup de proyecto, CLI, entornos, Theme Check, `theme pull` autorizado |
| `design-auditor` | `eden:design-auditor` | Loop medir → corregir → medir |
| `reviewer` | `eden:shopify-qa-reviewer` | Revisión del diff + Theme Check |
| `quality-auditor` | `eden:shopify-perf-seo-a11y` | Core Web Vitals, accesibilidad, SEO, analytics |
| `security-auditor` | `eden:security-auditor` | XSS en Liquid, secretos, scripts de terceros, apps; lee el módulo Shopify |
| `migrator` | `eden:shopify-data` (modo `import`) | Import o migración de producto y contenido |

## Propiedad de archivos (quién escribe qué)

| Archivos | Dueño |
|---|---|
| `sections/*.liquid`, `blocks/*.liquid`, `snippets/*.liquid` (incluido su `{% stylesheet %}` y `{% javascript %}` pequeño) | `eden:shopify-theme-dev` |
| `templates/*.json`, `sections/*.json` (grupos de secciones), `locales/*.json` | `eden:shopify-theme-dev` |
| `assets/*.js`, `assets/*.css` de componente, registro de custom elements | `eden:shopify-js-dev` |
| `config/settings_schema.json`, `snippets/{prefix}-design-tokens.liquid` o el snippet de tokens del proyecto | `eden:shopify-design-system` |
| Snippets de JSON-LD, archivos de definiciones de metafields/metaobjects (`.shopify/`, scripts de GraphQL, CSV de import) | `eden:shopify-data` |
| `shopify.theme.toml`, `.theme-check.yml`, `.shopifyignore`, `.gitignore`, `package.json` de tooling, `.github/` | `eden:shopify-devops` |
| `layout/theme.liquid` | **Líder decide** — es global. Se asigna a un dueño con encargo explícito |
| `config/settings_data.json` | **Nadie sin el sí del dev** — es de la tienda y cambia producción |

Si una unidad cruza dueños, el líder la parte en unidades secuenciales. Nunca dos agentes sobre el mismo
archivo en paralelo.

## Prohibiciones con la tienda — no negociables

Decisión del dev (2026-09-28). **Ningún agente ni el líder** las rompe, aunque el encargo lo pida:

| Nunca | Por qué |
|---|---|
| `shopify theme push`, **en ninguna circunstancia** ni contra ningún tema | Decisión del dev: la subida la hace él |
| `shopify theme publish`, `delete`, `rename`, `share` | Cambian la tienda |
| Tocar el **tema publicado** (live) de cualquier forma sin autorización explícita del dev en el momento | Es producción |
| Escribir `config/settings_data.json` sin el sí del dev | Repinta la tienda |
| Crear/editar definiciones de metafields, metaobjects, productos o apps en el Admin sin el sí del dev | Es la tienda del cliente |

Con autorización explícita del dev escrita en el encargo, y solo así:

- `shopify theme pull` (baja archivos; puede sobrescribir cambios locales: se revisa `git status` antes).
- `shopify theme dev` (sirve en local con un tema de desarrollo; el dev confirma porque sube archivos a
  ese tema de desarrollo).

Sin autorización y sin riesgo: `shopify theme check`, `shopify theme list`, `shopify theme info`,
`shopify version`, y todo lo local.

## Formato de handoff (todos los especialistas)

```
🧩 {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {Theme Check, render, grep de consumidores… con el resultado real}
No verificado: {qué y por qué}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

Alineadas con las fases que declare el perfil activo (`phases`), si las tiene.

| Fase del kit | Perfil | Especialistas |
|---|---|---|
| 1. Discovery | P2 | architect (si ya hay tema), design-extractor |
| 2. Setup | P4 | devops |
| 3. Fundamentos | P4 | design-extractor → design-system |
| 4. Sitemap | P6 | architect, design-extractor |
| 5. Datos y catálogo | P5 | data |
| 6. Build | P6 | theme-dev, js-dev, data — con design-auditor en loop |
| 7. QA | P7 | reviewer, design-auditor, quality-auditor |
| 8. Revisiones del cliente | P8 | igual que Build, solo lo aprobado |
| 9. Lanzamiento | P9 | `launch-check` + quality-auditor. El deploy lo hace el dev |
| 10. Garantía | P10 | Tareas normales, tipo bug |
