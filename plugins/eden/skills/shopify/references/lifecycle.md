# Ciclo de vida — qué hace el equipo en cada tipo de trabajo

Cada fase dice **quién trabaja**, **qué skill es el playbook** y **dónde se para a preguntar**. Las
fases que declare el perfil (`phases`) aparecen entre paréntesis cuando el proyecto usa un perfil que las tiene.

Una fase se salta si su artefacto ya existe y está vigente (p. ej. `docs/design-system.md`), y se dice en
una línea. Nunca se salta en silencio.

---

## Proyecto nuevo (`new`)

| # | Fase | Especialistas | Playbook | Artefacto | Puerta del dev |
|---|---|---|---|---|---|
| 1 | **Discovery** (P2) | `eden:figma-extractor` (páginas y NODE-SECTION de alto nivel) | — | `.claude/context/discovery.md`: páginas, secciones, apps previstas, datos que hacen falta | Confirmar alcance y lo que queda fuera |
| 2 | **Setup** (P4) | `eden:shopify-devops` `setup` | `shopify-setup` | Repo, base del tema, `shopify.theme.toml`, Theme Check, bloque `shopify` en `project-config.json` | Base y versión del tema, tienda y entornos, rama base |
| 3 | **Fundamentos** (P4) | `eden:figma-extractor` → `eden:shopify-design-system` | `create-fundaments` | Tokens integrados, `docs/design-system.md` | Aprobar el mapeo; conflictos y huecos |
| 4 | **Sitemap** (P6) | `eden:shopify-architect` + `eden:figma-extractor` | `create-sitemap` | `docs/sitemap.md` con NODE-SECTION y estado | Aprobar el mapa |
| 5 | **Datos y catálogo** (P5) | `eden:shopify-data` `model` / `import` | — | Definiciones de metafields/metaobjects preparadas, CSV validado | **Todo lo que se crea en el Admin** |
| 6 | **Build** (P6) | `eden:shopify-theme-dev` · `eden:shopify-js-dev` · `eden:shopify-data` `connect` · `eden:design-auditor` en loop | `create-new-section` por sección, o `ignition-task` por ticket | Secciones, bloques, plantillas JSON, JS | Plan por lote de secciones; cada cambio compartido |
| 7 | **QA** (P7) | `eden:shopify-qa-reviewer` · `eden:design-auditor` · `eden:shopify-perf-seo-a11y` | `qa-pixel-perfect` por página, `pastel-sync` si hay comentarios | Hallazgos resueltos o declarados | Lo que tiene blast radius |
| 8 | **Revisiones del cliente** (P8) | Como Build, solo lo aprobado | `section-mod` | — | Cada revisión es una tarea |
| 9 | **Lanzamiento** (P9) | `eden:shopify-perf-seo-a11y` | `launch-check` | Checklist pre y post | **La subida y publicación del tema las hace el dev** |
| 10 | **Garantía** (P10) | Según el bug | `section-mod` / tarea | — | Solo bugs, no mejoras |

**Orden de dependencias que no se rompe:** Setup → Fundamentos → (Sitemap ∥ Datos) → Build → QA →
Lanzamiento. Dentro de Build, las secciones van en paralelo cuando sus archivos no se cruzan; los
componentes JS compartidos (carrito, drawer) se construyen **antes** que las secciones que los usan.

**Build por lotes.** En un proyecto nuevo, el Build no se planea entero de una vez: se toma del sitemap
un lote (una página o un grupo de secciones relacionadas), se planea, se ejecuta y se verifica. Luego el
siguiente. Así el plan que aprueba el dev es revisable y el checkpoint no crece sin control.

---

## Onboarding de un proyecto avanzado (`onboard`)

El objetivo es que el equipo pueda trabajar en el tema **sin romper lo que ya está en producción**.

| # | Fase | Especialistas | Artefacto | Puerta del dev |
|---|---|---|---|---|
| 1 | **Auditoría** | `eden:shopify-architect` `audit` (+ `eden:shopify-devops` `validate` en paralelo) | `.claude/context/audit-theme.md`: base y versión, personalizaciones, apps, datos, deuda con conteo, Theme Check | — |
| 2 | **Línea base de calidad** (si hay URL) | `eden:shopify-perf-seo-a11y` | `.claude/context/findings-quality-baseline.md` | — |
| 3 | **Informe al dev** | líder | Riesgos (qué no tocar sin cuidado), deuda priorizada, lo que falta para que el kit trabaje | El dev decide qué se prepara |
| 4 | **Entorno** | `eden:shopify-devops` `setup` en modo "solo lo que falta" | `shopify.theme.toml`, Theme Check, bloque `shopify` | Tienda y entornos |
| 5 | **Fundamentos sobre lo existente** | `create-fundaments` en modo auditoría: mapear los tokens que el tema ya tiene contra el Figma | `docs/design-system.md` | Conflictos: **nunca se cambia un esquema en uso sin el dev** |
| 6 | **Sitemap sobre lo existente** | `create-sitemap` marcando ✅ built / 🔧 needs-work / ♻️ reusable | `docs/sitemap.md` | Aprobar |
| 7 | **Cerebro** (opcional) | `/eden:brain init` si el dev lo quiere | — | Sí/no |

La deuda técnica **se reporta, no se arregla de paso**. Arreglarla es una tarea propia, aprobada.

---

## Tarea (`task`)

1. Si hay ticket: el playbook es `ignition-task`, que lee el ticket (`task.read`, ver `rules/eden-tracker-rules.md`) y Figma y arma el plan. El líder
   aporta el equipo: cada unidad sale con su especialista del roster.
2. Si es una sola sección: `section-mod` (existe) o `create-new-section` (no existe), con el mismo
   equipo.
3. Si es solo fidelidad a un nodo de Figma: `figma-expert`.
4. Siempre: `explorer`/`architect` para el blast radius antes de tocar algo compartido.
5. Al terminar: `/eden:turnoff-task`.

Precondiciones que se **avisan** (el dev decide si se preparan antes): sin fundamentos, sin sitemap, sin
bloque `shopify` en `project-config.json`.
