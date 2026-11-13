# Scaffold de un proyecto WordPress — qué se crea y por qué

Todo lo de aquí se **propone** antes de crearse, y **nada se pisa**: si el archivo existe, se reporta y
se pregunta. Los nombres van en inglés; `{prefix}` y `{cliente}` salen de `project-config.json`.

## 1. Child theme (si trabajamos sobre un tema padre)

```
wp-content/themes/{cliente}-child/
├── style.css
├── functions.php
├── theme.json          ← solo si el sabor es block-theme
└── screenshot.png
```

`style.css` — la cabecera es lo único que importa; **`Template:` debe ser el nombre exacto de la
carpeta del padre**, no su nombre bonito:

```css
/*
Theme Name: {Cliente} Child
Template: {carpeta-del-tema-padre}
Version: 1.0.0
Text Domain: {text-domain}
*/
```

`functions.php` — **solo enqueues y supports. Nunca lógica de negocio.**

```php
<?php
namespace {Namespace}\Theme;

defined( 'ABSPATH' ) || exit;

add_action( 'wp_enqueue_scripts', __NAMESPACE__ . '\enqueue_assets' );
function enqueue_assets(): void {
    $style = get_stylesheet_directory() . '/style.css';
    wp_enqueue_style(
        '{prefix}-child',
        get_stylesheet_uri(),
        array( 'parent-style-handle' ),
        file_exists( $style ) ? (string) filemtime( $style ) : null
    );
}
```

Dos detalles que causan la mitad de los bugs de arranque:

- **El handle del padre se averigua**, no se inventa (`grep -rn "wp_enqueue_style" {padre}`). Si se
  pone mal, el CSS del hijo carga antes que el del padre y nada se aplica.
- **La versión sale de `filemtime()`**, no de una constante que nadie actualiza. Sin eso, el cliente
  sigue viendo el CSS viejo y aparece un ticket de "no se aplicó el cambio".

`defined( 'ABSPATH' ) || exit;` va **en todos los archivos PHP**: evita que se ejecuten si alguien los
llama por URL directa.

## 2. mu-plugin del sitio — aquí vive la funcionalidad

```
wp-content/mu-plugins/
├── {cliente}-core.php          ← loader (los mu-plugins no cargan subcarpetas solos)
└── {cliente}-core/
    ├── plugin.php
    └── inc/
        ├── post-types.php
        ├── taxonomies.php
        ├── fields.php
        ├── rest.php
        └── hooks.php
```

El loader es obligatorio: **WordPress solo autocarga los `.php` que están en la raíz de
`mu-plugins/`**, no los de sus subcarpetas.

```php
<?php
// {cliente}-core.php
defined( 'ABSPATH' ) || exit;
require_once __DIR__ . '/{cliente}-core/plugin.php';
```

Por qué mu-plugin y no plugin normal: **no se puede desactivar por accidente desde el admin**. Los CPTs
y los campos del sitio no deberían poder apagarse con un click.

Por qué no en el tema: si mañana cambia el diseño y se cambia el tema, **el cliente pierde sus datos**.
La funcionalidad sobrevive al tema.

## 3. Validación

```bash
composer require --dev squizlabs/php_codesniffer wp-coding-standards/wpcs \
  dealerdirect/phpcodesniffer-composer-installer
```

`phpcs.xml.dist` acotado a **lo nuestro** — nunca al core ni a los plugins de terceros:

```xml
<?xml version="1.0"?>
<ruleset name="{Cliente}">
  <file>wp-content/themes/{cliente}-child</file>
  <file>wp-content/mu-plugins/{cliente}-core</file>
  <rule ref="WordPress"/>
  <config name="testVersion" value="{php}-"/>
  <arg name="extensions" value="php"/>
</ruleset>
```

Si hay bloques, `@wordpress/scripts` para el build y el lint de JS.

## 4. `.gitignore`

Lo que **no** se versiona nunca:

```gitignore
# WordPress core
/wp-admin/
/wp-includes/
/wp-*.php
!/wp-content/
/index.php
/license.txt
/readme.html

# Configuración y secretos
wp-config.php
.env

# Contenido y terceros
wp-content/uploads/
wp-content/upgrade/
wp-content/cache/
wp-content/plugins/*
wp-content/themes/*
wp-content/debug.log

# ...menos lo nuestro
!wp-content/mu-plugins/
!wp-content/plugins/{cliente}-*/
!wp-content/themes/{cliente}-child/

# Dumps y backups
*.sql
*.sql.gz
*.wpress

# Dependencias y build
node_modules/
vendor/
build/
```

**Se versiona lo nuestro; se ignora lo de otros.** La excepción es un proyecto con Composer/Bedrock, que
versiona el `composer.json` en vez de los plugins: si el proyecto va por ahí, esta plantilla cambia y se
declara.

Y un recordatorio que se paga caro una sola vez: **un `.sql` con datos reales de clientes no entra al
repo**, ni siquiera "un momentito para pasárselo a alguien".

## 5. Qué NO crea el scaffold

- No instala plugins. Eso se pregunta.
- No toca `wp-config.php` de un sitio existente.
- No crea CPTs ni campos "de ejemplo": se crean cuando una tarea los pida, con su nombre real.
- No importa nada — eso es `/eden:wp-import`.
