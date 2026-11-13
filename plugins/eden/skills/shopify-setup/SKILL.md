---
name: shopify-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:shopify-setup`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify` (que ya fue invocado por él y le pide confirmación antes). NO lo actives porque el
  proyecto sea Shopify, porque falte un `shopify.theme.toml` o porque se hable de arrancar una tienda:
  si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: deja un proyecto Shopify
  listo para que el equipo trabaje. En un proyecto nuevo pregunta la base del tema (Horizon por
  defecto) y su versión, la tienda y los entornos, y levanta repo, tema base, `shopify.theme.toml`,
  Theme Check, `.shopifyignore`, `.gitignore` y el bloque `shopify` de `project-config.json`. En un
  proyecto avanzado completa solo lo que falta, sin tocar el tema. Nunca hace `shopify theme push` ni
  toca el tema publicado.
argument-hint: "[ruta del proyecto] [| tienda.myshopify.com] [| base y versión del tema] [| nuevo | existente]"
disable-model-invocation: true
---

## Shopify Setup — la base del proyecto

Argumento recibido: `$ARGUMENTS`

Deja el proyecto en el estado en el que cualquier skill del kit puede trabajar: el tema en el repo, el
CLI apuntando a los entornos correctos, la validación montada y la configuración declarada. Es la fase
**Setup** (la fase equivalente del perfil, si declara `phases`).

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace el `devops` (rol) del roster
Shopify, `eden:shopify-devops`, con el `architect` (rol) para el inventario si el proyecto ya existe. Ver
`rules/eden-team-rules.md`.

### Lo que NO hace — nunca

- **`shopify theme push`, contra ningún tema.** Decisión del dev: la subida la hace él.
- Tocar el **tema publicado**, `publish`, `delete`, `rename`, `share`.
- `shopify auth` / login: **la autenticación la hace el dev**. El skill le dice cuándo.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.
- Instalar herramientas globales sin preguntar.
- Guardar tokens o contraseñas de tienda en archivos del repo.

---

### Paso 1 — Qué hay

Delega al `architect` (rol) un inventario de arranque (`inventory` del directorio), o léelo tú si el
directorio está vacío:

- ¿Hay tema en el repo? (`layout/`, `sections/`, `config/settings_schema.json`). ¿Qué base y versión
  (`theme_info`)?
- ¿Hay git? ¿Qué ramas? ¿Hay remoto?
- ¿Existen `shopify.theme.toml`, `.theme-check.yml`, `.shopifyignore`, `.gitignore`,
  `.claude/project-config.json` (y su bloque `shopify`)?
- Herramientas: `node -v`, `shopify version`, `git --version`.

Con eso, clasifica: **nuevo** (no hay tema) o **existente** (hay tema: solo se completa lo que falta).

### Paso 2 — Preguntar lo que falta, en una sola intervención

```
🛍️ SETUP SHOPIFY — necesito:

1. Tienda: {xxx.myshopify.com}
2. Base del tema: Horizon (recomendado: theme blocks anidables, el estándar actual) · otra: {cuál}
   Versión: {última estable | la que diga el cliente}      ← solo si es nuevo
3. Entornos para shopify.theme.toml: development (theme ID) · staging (theme ID) · otros
   (los IDs salen de `shopify theme list`; si aún no hay sesión del CLI, haz `shopify auth` tú y me avisas)
4. Rama base para crear la rama de trabajo: {main | develop | …}
5. Perfil del proyecto: {nombre del perfil | ninguno}
```

No se avanza sin 1, 3 y 4. Lo que el dev no sepa aún (IDs de staging), queda como `TODO` explícito en
el archivo y en el reporte, nunca inventado.

### Paso 3 — Proponer

```
📋 ESTO VOY A DEJAR

Tipo: {nuevo | existente}
Base: {Horizon vX.Y desde github.com/Shopify/horizon | ya existe: {base} v{…}}
Archivos nuevos: {lista}
Archivos que se modifican: {lista — en existente, solo los de config}
project-config.json → bloque shopify: {resumen}
Rama: {tipo/ticket-slug} desde {base}
Para ti (el dev): {shopify auth, crear tema de desarrollo si no existe, …}

¿Lo levanto así?
```

Espera el sí.

### Paso 4 — Levantar (delegado a `eden:shopify-devops`, modo `setup`)

Encargo de cinco partes (`skills/shopify/references/dispatch.md` § 4) con: los datos del Paso 2, la
lista cerrada de archivos del Paso 3 y las prohibiciones del roster. El agente:

1. Base del tema (solo nuevo): del repositorio oficial y en la versión elegida.
2. `shopify.theme.toml` con los entornos. Sin secretos.
3. `.theme-check.yml` que extiende la config recomendada, sin desactivar checks para que pase.
4. `.shopifyignore` y `.gitignore` (`node_modules/`, `.env`, `.shopify/`, `.claude/checkpoint.md`,
   `.claude/context/`, `graphify-out/`).
5. Bloque `shopify` en `.claude/project-config.json` (ver `team/project-config.example.json`), y
   `project.stack: "shopify"` si no estaba.
6. La rama, local.

### Paso 5 — Verificar

- `shopify theme check` corre. En un tema base limpio: cero errores. En un existente: el número real,
  como línea base.
- `git status` muestra solo lo propuesto.
- `project-config.json` es JSON válido.

### Paso 6 — Reporte

```
✅ SETUP SHOPIFY

Tipo: {nuevo | existente} · Base: {…} · Tienda: {…}
Entornos: {development → ID · staging → ID | TODO}
Theme Check: {errores/avisos}
Rama: {…} (local, sin commitear)
Pendiente del dev: {shopify auth · IDs · subir el tema base a un tema de desarrollo — lo haces tú}

➜ Siguiente: /eden:create-fundaments (o /eden:shopify new para seguir el ciclo completo)
```

Si el proyecto no tiene `CLAUDE.md` con el bloque del kit, ofrece copiar `CLAUDE.base.md` con el
marcador `<!-- eden-stack: shopify -->`.
