---
name: shopify-app-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:shopify-app-setup`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify-app` (que ya fue invocado por él y le pide confirmación antes). NO lo actives porque se
  hable de una app de Shopify o falte una herramienta: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: levanta el entorno de desarrollo de una app de Shopify: Node y Shopify CLI, la
  plantilla vigente con `shopify app init`, la base de datos de sesiones, la tienda de desarrollo, las
  configuraciones por entorno (`shopify.app.{entorno}.toml`) con scopes mínimos y la versión de la API
  vigente, tests, lint y `.env.example`, y la app abriendo en el admin con `shopify app dev`. En una app
  existente completa solo lo que falta y declara el bloque `shopify_app`. Nunca libera versiones, ni
  despliega, ni toca tiendas reales.
argument-hint: "[ruta del proyecto] [| tienda de desarrollo] [| nueva | existente]"
disable-model-invocation: true
---

## Shopify App Setup — el entorno de la app

Argumento recibido: `$ARGUMENTS`

Deja la app en el estado en el que cualquier skill del kit puede trabajar y verificar: la plantilla
vigente, la app abriendo en el admin de una **tienda de desarrollo**, configuraciones separadas por
entorno, y lo que el kit usa para verificar (lint, typecheck, tests, build).

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace `eden:shopify-app-devops`, con
`eden:shopify-app-architect` para el inventario si la app ya existe.

### Lo que NO hace — nunca

- **`shopify app deploy` / `release`**, ni desplegar el servidor.
- **Conectarse a tiendas reales** o a la app de producción para trabajar.
- **Login en la cuenta de partner ni crear la app**: el CLI abre el navegador y **lo hace el dev**; el
  skill le dice cuándo.
- Escribir secretos; instalar herramientas globales o dependencias sin el sí del dev.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.

---

### Paso 1 — Qué hay

`python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect {ruta}` y, si hay app, un `inventory` de
`eden:shopify-app-architect`:

- ¿`shopify.app*.toml`? ¿Qué plantilla (React Router, Remix, Express) y qué versiones?
- `node --version`, `shopify version`.
- ¿Base de datos de sesiones? ¿Tests, lint, typecheck? ¿`.env.example`?
- ¿Qué versión de la Admin API usa, y tiene soporte?
- ¿`.claude/project-config.json` con su bloque `shopify_app`?

Si es un **tema**, se para: su setup es `/eden:shopify-setup`.

### Paso 2 — Preguntar lo que falta, en una sola intervención

Antes, comprueba en la doc vigente de shopify.dev (context7 o el MCP de Shopify Dev) la versión del CLI,
la plantilla recomendada, el mínimo de Node y la versión estable de la Admin API: no se usan de memoria.

```
🧩 SETUP SHOPIFY APP — necesito:

Plantilla:        React Router (recomendada hoy — verificado: {…}) · otra que uses
Tipo de app:      pública (App Store) · personalizada (una tienda) · {la que digas}
Cuenta y app:     haces tú el login de partner y eliges o creas la app cuando el CLI lo pida
Tienda de dev:    {nombre}.myshopify.com — solo de desarrollo
Sesiones:         SQLite en local (por defecto) · producción: {la decides tú}
Admin API:        {versión estable vigente} · scopes iniciales: {mínimos para lo primero que se construye}
Polaris:          web components (lo actual de la plantilla — verificado) · React (si el proyecto ya lo usa)
Tests:            Vitest (recomendado) · lint ESLint · TypeScript estricto
Entornos:         shopify.app.toml (desarrollo) · shopify.app.{staging|production}.toml
Carpeta:          {ruta} {vacía ✅ | con archivos ⚠️}
Rama base:        {la que digas}
```

Para una app **existente** se pregunta solo lo que falta, con lo que se va a añadir y por qué.

### Paso 3 — Montarlo (delegado a `eden:shopify-app-devops`)

Con el encargo de cinco partes y el sí del dev explícito en él:

- **Nueva:** `shopify app init` con la plantilla elegida (cuando el CLI pida login o app, **se para y se
  le pasa al dev**); base de sesiones local; configuraciones por entorno con scopes mínimos, la versión
  de la API vigente y las suscripciones de webhooks (incluidos los de cumplimiento si es pública) en el
  TOML; tests, lint, typecheck, `.env.example`, `.gitignore`.
- **Existente:** solo los huecos aprobados.

### Paso 4 — Verificar y declarar

1. `install`, `lint`, `typecheck`, `test`, `build`: la salida real.
2. `shopify app dev` contra la tienda de desarrollo (con el sí del dev la primera vez): la app abre en el
   admin. Si no se pudo, se declara.
3. Escribe en `.claude/project-config.json`: `project.stack: "shopify-app"` y el bloque `shopify_app`
   (`client_id` **público**, `dev_store`). Nunca el secreto.
4. En el `CLAUDE.md` del proyecto, el marcador `<!-- eden-stack: shopify-app -->`.

### Paso 5 — Reporte

```
🧩 SETUP SHOPIFY APP — LISTO

Plantilla: {x} · CLI {v} · Node {v} · Admin API {v} (soporte hasta {fecha}) · Polaris {web components | React}
Herramientas: lint ✅ · typecheck ✅ · tests ✅ · build ✅
Abre en el admin de: {tienda de desarrollo} {✅ | no probado}
Entornos: {configuraciones} · scopes: {…}
Declarado: project-config.json (shopify_app) · CLAUDE.md
Pendiente del dev: secretos en .env, base de datos de producción, desplegar el servidor, liberar versiones

➜ Siguiente: /eden:shopify-app para la primera tarea, o /eden:shopify-app-admin para una pantalla.
```
