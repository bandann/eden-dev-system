---
name: wp-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:wp-setup` o lo pide de forma explícita e inequívoca. NO lo actives porque el proyecto
  sea de WordPress, porque veas un `wp-content/` o porque se hable de arrancar un sitio: si no lo pidió
  por su nombre, no se usa. —
  Qué hace cuando SÍ se invoca: define CÓMO se va a desarrollar este proyecto de WordPress y deja la
  base lista. Pregunta el sabor (block theme / tema clásico / page builder / headless) y el entorno
  local (LocalWP / DDEV / wp-env / Docker) con una recomendación razonada para este caso, inventaría lo
  que ya existe, levanta el esqueleto que falte (child theme, mu-plugin del sitio, herramientas de
  validación, .gitignore) y escribe la decisión en `project-config.json`, en el `CLAUDE.md` y en
  `docs/`. Es el primer comando de todo proyecto WordPress: sin él, los demás preguntan.
argument-hint: "[ruta del sitio o del repo] [| lo que ya sepas: sabor, entorno, tema, cliente]"
disable-model-invocation: true
---

## WP Setup — decidir cómo se desarrolla este WordPress

Argumento recibido: `$ARGUMENTS`

WordPress no es una plataforma: son **cuatro formas distintas de construir**, con reglas, tokens y
"secciones" que no se parecen entre sí. El kit las soporta todas, pero **no las adivina**. Este skill
existe para tomar esa decisión una vez, por proyecto, y dejarla escrita donde el resto del kit la lea.

> **Idioma:** al dev, en español. Todo lo que quede escrito —código, nombres, docs, config— en inglés.

**Lo que NO hace:** commitear, pushear, instalar plugins sin permiso, tocar producción, ni importar un
sitio (eso es `/eden:wp-import`).

**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). El inventario del
sitio se delega a `eden:wp-explorer`; el scaffold, a `eden:wp-implementer`. La sesión principal decide,
pregunta y verifica.

**Reglas que aplican:** `rules/eden-stack-rules.md`, `rules/wordpress/eden-wordpress-rules.md` y, en cuanto
se decida, el sabor correspondiente de `rules/wordpress/flavors/`.

---

### Paso 0 — Memoria y estado actual

`/eden:memory recall wordpress {cliente}` — puede que ya hayamos trabajado este sitio, o que haya un
hecho semántico sobre cómo trabaja este cliente. Si el proyecto ya tiene
`.claude/project-config.json` con `wordpress.flavor` **relleno**, este skill **no vuelve a preguntar**:
muestra lo que hay y ofrece revisarlo o completarlo. Un setup que se rehace en silencio reescribe
decisiones que alguien ya tomó.

---

### Paso 1 — Inventariar lo que ya existe (antes de preguntar nada)

Delega a **`eden:wp-explorer`** un inventario de arranque. Preguntar sin haber mirado hace perder el
tiempo del dev: la mitad de las respuestas están en el repo.

Lo que hay que traer:

- ¿Hay una instalación de WP aquí, o el repo es solo el tema/plugin?
- Tema activo, si es child, cuál es el padre, y si tiene `theme.json`.
- Plugins presentes — y en particular si hay **page builder** (Elementor, Divi, WPBakery, Beaver),
  **ACF**, **WooCommerce**, **multisite**.
- Si hay indicios de headless: `WPGraphQL`, un front en otra carpeta del repo, `stacks[]` ya declarado.
- Qué entorno local hay: `.ddev/`, `.wp-env.json`, `docker-compose.yml`, un sitio de LocalWP.
- Versiones de PHP y WP, y si hay Composer / npm en el proyecto.
- Qué herramientas de validación existen ya (PHPCS, PHPStan, `wp-scripts`).

Del inventario sale una **hipótesis con evidencia**, no una conclusión: "parece un tema clásico con
Elementor encima, porque `{ruta}`". El dev confirma.

---

### Paso 2 — Las dos preguntas que definen el proyecto

Se preguntan **juntas, en una sola intervención**, con la hipótesis del inventario ya puesta encima y
**con una recomendación razonada**. No se pregunta en abstracto: se pregunta sobre este sitio.

```
🧭 CÓMO VAMOS A DESARROLLAR ESTE WORDPRESS

Lo que encontré: {hipótesis del inventario, con evidencia}

1 · SABOR — cómo se construye el front
   a) Block theme (FSE)     → theme.json + patterns + bloques propios
   b) Tema clásico PHP      → template hierarchy + partials + ACF
   c) Page builder          → {el que se detectó}: widgets propios + CSS acotado
   d) Headless              → WP solo expone datos; el front es {framework}

   Recomiendo {x} porque {razón basada en lo encontrado y en lo que pide el proyecto}.
   ⚠️ {si aplica: lo que se pierde o se gana con esa elección}

2 · ENTORNO LOCAL — dónde corre
   a) LocalWP    b) DDEV    c) wp-env    d) Docker propio    e) el que ya hay: {x}

   Recomiendo {x} porque {razón}.
```

**Cómo se recomienda** — los criterios están en `references/flavors.md` y `references/local-envs.md`.
En corto:

- El sabor **casi nunca se elige**: lo impone el sitio que ya existe. Solo es una elección abierta en
  un proyecto desde cero. Si el sitio tiene Elementor con 40 páginas armadas, el sabor es page-builder
  aunque no nos guste; proponer migrarlo es otro proyecto, no esta decisión.
- El entorno **sí se elige**: si ya hay uno funcionando, gana ese. Si no, DDEV para trabajo en equipo y
  sitios existentes, wp-env para desarrollo de bloques y temas, LocalWP si el dev prefiere GUI.

**No se avanza sin las dos respuestas.** Son la base de todo lo demás.

---

### Paso 3 — Confirmar los datos que el kit necesita

Con el sabor decidido, se completa lo que falte (lo que se pueda deducir del inventario se **propone
ya resuelto**, para que el dev solo confirme):

| Dato | Para qué |
|---|---|
| `theme_path` | El child theme que mantenemos |
| `parent_theme` | Qué se hereda y qué se rompe cuando el padre se actualice |
| `mu_plugin_path` | Dónde vive la funcionalidad — sobrevive al cambio de tema |
| `prefix` / `text_domain` | Funciones, hooks, clases y bloques propios |
| `site_url_local/staging/prod` | El search-replace de `/eden:wp-import` no funciona sin ellas |
| `acf` · `woocommerce` · `multisite` | Cambian qué reglas y qué QA aplican |
| Breakpoints | Los anchos exactos de los frames de Figma — la regla de medir del QA visual |

---

### Paso 4 — Proponer el scaffold (y esperar el OK)

Se **propone**, no se ejecuta. Solo lo que falte, y con el porqué de cada pieza:

- **Child theme**, si el proyecto trabaja sobre un tema padre y no existe: `style.css` con cabecera
  correcta, `functions.php` mínimo (solo enqueue del padre y del hijo), y —si el sabor es block
  theme— `theme.json` **vacío de decisiones**, listo para que `/eden:create-fundaments` lo llene.
- **mu-plugin del sitio** (`wp-content/mu-plugins/{cliente}-core/`): el loader y la estructura para
  CPTs, taxonomías, campos y endpoints. **Esto no es opcional**: si la funcionalidad vive en el tema, el
  día que cambie el diseño el cliente pierde sus datos.
- **Validación**: PHPCS + WPCS por Composer, y `wp-scripts` si hay bloques. Es la puerta de
  `/eden:test-code` y de `turnoff-task`; sin ella no hay cómo cerrar en verde.
- **`.gitignore`** de WordPress: core, `uploads/`, plugins de terceros, `wp-config.php`, dumps de DB.
  Ver `references/scaffold.md`.
- **Entorno local**: la config del que se eligió (`.ddev/config.yaml`, `.wp-env.json`,
  `docker-compose.yml`). El levantado y el día a día son de `/eden:wp-local`.

Se dice qué archivo se va a crear, dónde y por qué. Lo que ya exista **no se pisa**: se reporta y se
pregunta.

---

### Paso 5 — Escribir la decisión donde el kit la lee

Tres sitios, los tres, o la decisión se pierde:

1. **`.claude/project-config.json`** → bloque `wordpress{}` completo + `project.stack: "wordpress"`
   (y `project.stacks[]` si es headless). Ver `team/project-config.example.json`.
2. **`CLAUDE.md` del proyecto** → el bloque de WordPress con el marcador:
   ```
   <!-- eden-stack: wordpress -->
   <!-- eden-wp: flavor={x} env={y} theme={ruta} mu-plugin={ruta} updated=YYYY-MM-DD -->
   ```
   Más las tres o cuatro líneas que un dev nuevo necesita: qué es child de qué, dónde va la
   funcionalidad, qué plugins son parte del contrato y qué NO se toca.
3. **`docs/wordpress-setup.md`** → el detalle: el porqué de cada decisión, cómo se levanta el entorno,
   qué plugins hay y para qué, y qué queda pendiente. En inglés.

---

### Paso 6 — Fundamentos de diseño

Si el proyecto va a tener trabajo visual, los tokens del Figma se integran **en el sistema que la
plataforma ya tiene** — `theme.json` en block theme, custom properties propias en clásico, globales del
builder en page-builder. Eso lo hace `/eden:create-fundaments`
(ver `create-fundaments/references/wordpress-integration.md`).

Aquí solo se **propone encadenarlo** y se espera confirmación. `wp-setup` deja la base; no inventa
tokens.

---

### Paso 7 — Reporte

```
🧭 WP SETUP — {proyecto}

Sabor          {x} — {por qué}
Entorno local  {y} — {por qué}
Tema           {child} (padre: {parent})
Funcionalidad  {mu-plugin}
Prefijo        {prefix} · text domain {td}
Extras         ACF {sí/no} · WooCommerce {sí/no} · Multisite {sí/no}

Creado
  {ruta} — {qué es}

Ya existía (no se tocó)
  {ruta}

Escrito
  .claude/project-config.json · CLAUDE.md · docs/wordpress-setup.md

⚠️ Pendiente / a decidir
  {lo que quedó abierto, con quién lo decide}

Siguiente
  /eden:wp-local     levantar el entorno
  /eden:wp-import    bajar el sitio del cliente a local
  /eden:create-fundaments   integrar el design system del Figma
```

Al terminar, propón guardar en memoria lo no obvio de este cliente
(`/eden:memory save`): por qué se eligió ese sabor, qué plugins son intocables, qué trampa tiene el sitio.
