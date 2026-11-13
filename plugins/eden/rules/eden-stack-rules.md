# Stacks — Eden (núcleo agnóstico + módulos por plataforma)

El kit no es un kit de Shopify. Es un kit de **cómo trabajamos**, y encima se monta el módulo de la
plataforma en la que toca construir:

| Stack | Módulo | Sabores | Para | Estado |
|---|---|---|---|---|
| `shopify` | `rules/shopify/eden-shopify-rules.md` | — | Temas Liquid (Horizon y similares) | ✅ |
| `wordpress` | `rules/wordpress/eden-wordpress-rules.md` + `flavors/` | block-theme · classic-theme · page-builder · headless | Temas y plugins de WP | ✅ |
| `react` | `rules/react/eden-react-rules.md` + `flavors/` | spa · next | Front web con React; Next.js también tiene su parte de servidor | ✅ |
| `php` | `rules/php/eden-php-rules.md` + `flavors/` | php · laravel | Back en PHP (WordPress tiene su propio módulo) | ✅ |
| `node` | `rules/node/eden-node-rules.md` + `flavors/` | node · express · nest | Back en Node.js: APIs y servicios (Next.js es del stack `react`) | ✅ |
| `mobile` | `rules/mobile/eden-mobile-rules.md` + `flavors/` | react-native · ionic | Apps móviles (React Native con Expo o bare; Ionic con Capacitor) | ✅ |
| `shopify-app` | `rules/shopify-app/eden-shopify-app-rules.md` | — | Apps de Shopify: admin embebido, extensiones y funciones (separado del equipo de temas) | ✅ |

Un stack 🔜 todavía no tiene módulo: hasta que lo tenga, aplica "Qué pasa si el stack no tiene
módulo" (abajo). El **sabor** se declara en el bloque del stack en `project-config.json`
(`react.flavor`, `php.flavor`…); si no está y la detección no lo deja claro, se pregunta.

El núcleo (`eden-workflow`, `eden-component-strategy`, `eden-design`, `eden-code-style`, `eden-quality`,
`eden-git`, `eden-testing`, `eden-security`, `eden-memory`, `eden-context`, `eden-model-strategy`, `eden-profiles`, `eden-tracker`) **no sabe de
plataformas** y no cambia cuando se agrega una. La escalera reuse-first, el default neutro, "Figma
manda", el blast radius y la puerta de calidad valen igual en Liquid, en PHP o en un bloque de
Gutenberg. Lo que cambia es **cómo se expresan** en esa plataforma, y eso es exactamente lo que dice
un módulo.

## El archivo de instrucciones del proyecto

Eden corre en distintas herramientas de IA, y cada una lee su propio archivo de instrucciones del
proyecto: **`CLAUDE.md`** (Claude Code), **`AGENTS.md`** (Codex, OpenCode, Cursor, Kimi Code, Grok Build,
Crush), **`GEMINI.md`** (Gemini / Antigravity) o **`QWEN.md`** (Qwen Code). **Donde las reglas, los
skills y los agentes del kit dicen `CLAUDE.md`, se entiende ese archivo**:

- **Para leer** (marcadores `<!-- eden-stack -->`, `<!-- eden-profile -->`, `<!-- eden-wp -->`, el
  bloque de fundamentos…): el primero que exista de `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `QWEN.md`.
- **Para escribir**: el que el proyecto ya tenga. Si tiene varios, el de la herramienta en la que se está
  trabajando; si no tiene ninguno, se crea el de esa herramienta. Nunca se duplica el bloque de Eden en
  dos archivos: si el dev usa varias herramientas, lo normal es que un archivo importe o enlace al otro,
  y eso lo decide él.

## Cómo se determina el stack de un proyecto

En este orden, y se para en el primero que responda:

1. **Lo que el dev diga en el momento.** Siempre gana.
2. **`.claude/project-config.json` → `project.stack`.** Es el declarado; es la fuente normal.
3. **El archivo de instrucciones del proyecto** — marcador `<!-- eden-stack: … -->`.
   (Compatibilidad: un `<!-- fl-stack: … -->` de un proyecto antiguo se lee como el `eden-` equivalente
   y se **propone** migrarlo; nunca se reescribe en silencio.)
4. **Detección por el repo**, solo si lo anterior no existe. La hace
   `python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect [ruta]` (sin adivinar: devuelve el
   stack, el sabor, la evidencia y si hay más de un candidato). **El orden importa**, porque una app de
   Shopify también es React y Laravel también es PHP; gana la primera regla que encaje:

   | # | Si el repo tiene… | Stack · sabor |
   |---|---|---|
   | 1 | `shopify.app.toml` (o `shopify.app.*.toml`) | `shopify-app` |
   | 2 | `sections/` + `snippets/` + `config/settings_schema.json` | `shopify` |
   | 3 | `wp-content/`, `wp-config.php` o `style.css` con `Theme Name:` | `wordpress` |
   | 4 | `composer.json` con `laravel/framework`, o `artisan` | `php` · `laravel` |
   | 5 | dependencia `expo` o `react-native` | `mobile` · `react-native` |
   | 6 | dependencia `@ionic/*` o `@capacitor/core`, o `ionic.config.json` / `capacitor.config.*` | `mobile` · `ionic` |
   | 7 | dependencia `next`, o `next.config.*` | `react` · `next` |
   | 8 | dependencia `@nestjs/core`, o `nest-cli.json` | `node` · `nest` |
   | 9 | dependencia `express` | `node` · `express` |
   | 10 | dependencia `react` | `react` · `spa` |
   | 11 | `composer.json` o archivos `*.php` en la raíz | `php` · `php` |
   | 12 | `package.json` sin nada de lo anterior | `node` · `node` |

   `astro.config.*` u otro framework sin módulo → se nombra tal cual (`astro`…) y aplica "sin módulo".
   Si encajan **dos stacks distintos** (un monorepo con `apps/web` en Next y `apps/api` en Nest), no se
   elige uno: es un proyecto con más de una plataforma (ver abajo) y se pregunta.

Si la detección es ambigua o no coincide con lo declarado, **se pregunta**: un stack mal supuesto hace
que todo lo demás —convenciones, blast radius, tests— se mida con la regla equivocada.

## Qué pasa si el stack no tiene módulo

El trabajo **no se bloquea**. Se aplica el núcleo, se leen las convenciones del propio proyecto
(que es lo que manda de todos modos) y **se declara en una línea**:

> `↪ Este proyecto es {stack} y el kit no tiene módulo para él; sigo el núcleo y las convenciones del repo.`

Un módulo se escribe cuando la plataforma se repite lo bastante como para que valga la pena; hasta
entonces, el núcleo alcanza.

## Precedencia completa

Cuando dos fuentes dicen cosas distintas, gana la de arriba:

1. **El dev, en el momento.**
2. **Las convenciones reales del proyecto** — cómo está construido hoy. Un módulo describe la buena
   práctica de la plataforma; **el proyecto describe la verdad**. Si el proyecto hace algo distinto y
   coherente, se sigue el proyecto y, si el desvío importa, se comenta una vez.
3. **El `CLAUDE.md` / `project-config.json` del proyecto.**
4. **El perfil de operación activo** (`eden-profiles-rules.md`).
5. **La config global del dev** (`~/.claude/eden-config.json`).
6. **El módulo de la plataforma.**
7. **El default del núcleo.**

## Prefijo del proyecto

El código **propio del cliente** lleva el prefijo del cliente, no el del kit: `{prefix}` =
`project.prefix` de `.claude/project-config.json`. Se usa en tokens CSS (`--{prefix}-*`), snippets
(`{prefix}-design-tokens`), funciones PHP (`{prefix}_*`), text domain y mu-plugin (`{prefix}-core`),
bloques (`{prefix}/*`) y rutas REST (`{prefix}/v1`).

- **El nombre del kit no entra nunca en el código del cliente.**
- Un proyecto que ya usa `--fl-*` declara `prefix: "fl"` y sigue como está; no se renombra por estética.
- Con el prefijo vacío, **se pregunta antes de escribir código con prefijo**: un prefijo adivinado se
  propaga a cientos de archivos.
- Los marcadores y artefactos antiguos del kit (`fl-fundaments`, `fl-sitemap`, `fl-figma-assets`) se
  leen como sus equivalentes `eden-` y se proponen para migrar; nunca se reescriben en silencio.

## Proyectos con más de una plataforma

Pasa: un Shopify con un blog en WordPress, o un WP headless con un front aparte. Cuando ocurre:

- El `project.stack` declara el **principal**, y `project.stacks[]` los demás con su ruta.
- **Cada tarea declara en qué stack trabaja** antes de planear. Una tarea no cruza dos plataformas sin
  decirlo: el blast radius de una no aplica a la otra.
- Las ramas y los tickets siguen siendo del núcleo, no del stack.

## Escribir un módulo nuevo

Un módulo de plataforma contiene **solo lo que es propio de ella**, nunca una copia del núcleo:

- Cómo se estructura el código y dónde va cada cosa.
- Cómo se expresa la **configuración** (lo que en Shopify es el schema y en WP son theme.json / ACF /
  Customizer) — porque de ahí sale el escalón 3 de la escalera reuse-first.
- Cómo se integran los **fundamentos de diseño** en el sistema de tokens que la plataforma ya tiene.
- Cómo se mide el **blast radius** (qué se grepea y dónde, incluida la base de datos si aplica).
- Qué **validador** hace de puerta (Theme Check, PHPCS, ESLint…).
- Los **enlaces a la documentación vigente**, con la advertencia de verificar por año.

Lo que **no** va en un módulo: reglas de calidad universales, decisiones que le tocan al dev, ni nada
que ya diga el núcleo con otras palabras.

## El equipo del stack

Un módulo de reglas dice **cómo se construye** en la plataforma; el **equipo** dice **quién** lo
construye. Cada stack puede tener un roster (`teams/{stack}/roster.md`), especialistas
(`agents/eden-{stack}-*.md`) y un líder (`skills/eden-{stack}/`). Sin roster, se usa el equipo genérico.
Detalle en `rules/eden-team-rules.md`.
