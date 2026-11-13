# Módulo WordPress — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-code-style`,
`eden-design`, `eden-quality`, `eden-testing`). Aquí solo va lo que es propio de WordPress.

WordPress no es una plataforma: son cuatro formas distintas de construir. **Cada proyecto declara la
suya y no se mezclan.** Este archivo es lo común a las cuatro; lo propio de cada una vive en
`flavors/`:

| Sabor | Archivo | Qué es una "sección" ahí |
|---|---|---|
| **Block theme (FSE)** | `flavors/block-theme.md` | Un block pattern, un bloque custom o un template part |
| **Tema clásico** | `flavors/classic-theme.md` | Un template part PHP (`get_template_part`) |
| **Page builder** | `flavors/page-builder.md` | Un widget/módulo del builder o una plantilla guardada |
| **Headless** | `flavors/headless.md` | Un componente del front; WP solo expone datos |

El sabor se decide con `/eden:wp-setup` al arrancar el proyecto y queda escrito en
`.claude/project-config.json` (`wordpress.flavor`) y en el `CLAUDE.md`. **Si no está declarado, se
pregunta antes de escribir código** — no se deduce del tema instalado, porque un sitio con un block
theme puede estar construido a mano con shortcodes.

---

## La regla que más veces salva el proyecto: dónde va el código

WordPress deja escribir en muchos sitios y casi todos están mal. En orden:

| Va aquí | Qué |
|---|---|
| **Child theme** | Todo lo que es presentación: plantillas, estilos, `theme.json`, patterns, partials |
| **mu-plugin propio del sitio** (`wp-content/mu-plugins/{cliente}-core/`) | Todo lo que es **funcionalidad**: CPTs, taxonomías, campos, endpoints, lógica de negocio, integraciones |
| **Plugin propio versionado** | Funcionalidad que se reutiliza entre sitios o que el cliente puede desactivar a propósito |

**Nunca, bajo ninguna circunstancia:**

- Editar el **core** de WordPress (`wp-admin/`, `wp-includes/`). Se pierde en la siguiente
  actualización y deja el sitio sin poder actualizarse.
- Editar un **plugin de terceros** o un **tema padre** directamente. Lo mismo. Si hay que cambiar su
  comportamiento, se hace por hook, filtro o sobrescritura desde el child theme.
- Escribir funcionalidad en el `functions.php` del tema **padre**.
- Usar el **editor de archivos del admin** (`DISALLOW_FILE_EDIT` debería estar en `true`).

**Por qué los CPTs y la lógica no van en el tema:** si mañana cambia el diseño y se cambia el tema, el
cliente pierde sus productos, sus testimonios y sus formularios. La funcionalidad sobrevive al tema.

---

## Seguridad — no es opcional, y es donde WP se rompe

Principios, checklist y severidad en `rules/eden-security-rules.md`; aquí lo propio de WordPress.

WordPress es el CMS más atacado del mundo. Estas cuatro reglas se aplican **siempre**, no cuando
"parece que hace falta":

### 1. Escapar en la SALIDA, siempre, en el punto de salida

```php
echo esc_html( $title );
echo esc_attr( $class );
echo esc_url( $link );
echo wp_kses_post( $rich_text );   // HTML de contenido permitido
```

**No se escapa "al guardar y ya".** Se escapa donde se imprime, cada vez, aunque el dato venga de un
campo propio. La función se elige por el contexto, no por costumbre: un `esc_html` dentro de un `href`
deja pasar `javascript:`.

### 2. Sanitizar en la ENTRADA

```php
$slug  = sanitize_text_field( wp_unslash( $_POST['slug'] ?? '' ) );
$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
$id    = absint( $_GET['id'] ?? 0 );
```

`wp_unslash()` antes de sanitizar: WordPress mete slashes en `$_POST` y sin quitarlos se guardan
escapes de más.

### 3. Nonce + capability en toda acción

Son dos cosas distintas y hacen falta las dos: el nonce prueba que la petición vino de tu formulario;
la capability prueba que **este usuario puede hacerlo**.

```php
if ( ! wp_verify_nonce( wp_unslash( $_POST['_wpnonce'] ?? '' ), '{prefix}_save_x' ) ) {
    wp_die( esc_html__( 'Invalid request.', '{prefix}-core' ) );
}
if ( ! current_user_can( 'edit_post', $post_id ) ) {
    wp_die( esc_html__( 'Not allowed.', '{prefix}-core' ) );
}
```

Aplica igual a AJAX (`wp_ajax_*`, `check_ajax_referer`) y a rutas REST (`permission_callback` — **nunca
`__return_true`** en algo que escribe).

### 4. Consultas preparadas

```php
$wpdb->get_results( $wpdb->prepare( "SELECT ... WHERE id = %d", $id ) );
```

Y antes de escribir SQL: **preguntarse si `WP_Query` / `get_posts` / `get_terms` no lo resuelve ya**.
En el 95% de los casos sí, y además respeta caché, permisos y filtros.

### 5. Subidas de archivos

- El tipo se valida en el servidor con `wp_check_filetype_and_ext()`; **nunca** se confía en el MIME
  ni en la extensión que manda el cliente. Lista blanca de tipos y tamaño máximo.
- Se sube con `wp_handle_upload()` / `media_handle_upload()`, nunca con `move_uploaded_file()` a mano.
  Un PHP subido a `uploads/` es ejecución remota de código: **Crítica**.

### 6. Redirecciones

- Con un destino influido por el usuario (`redirect_to`, `return`, `next`), `wp_safe_redirect()` y no
  `wp_redirect()`. Es el open redirect de WP: **Alta**.

### 7. Formularios y endpoints públicos

- Todo formulario, acción AJAX `nopriv` o ruta REST pública que envía correo o crea registros lleva
  límite de frecuencia (transient por IP/huella, o el rate limit del WAF/CDN) además de honeypot o
  captcha. Sin él: Media.

### 8. Plugins de terceros — verificar antes de proponerlos

Complementa "Plugins de terceros" (más abajo). Antes de proponer uno, y como parte de la revisión de
dependencias:

- Última actualización y compatibilidad con la versión de WP del proyecto. **Un plugin abandonado
  (sin actualizar en más de 12 meses) es un riesgo**: se declara.
- CVEs conocidos en **WPScan DB** o **Patchstack**. Uno alto o crítico sin parche bloquea.
- En proyectos con Composer: `composer audit` y `osv-scanner scan source -r .`.

### 9. Endurecimiento — recomendaciones, no se aplican sin preguntar

`wp-config.php` y la configuración del servidor son del cliente: **el kit recomienda, el dev decide**.

- `DISALLOW_FILE_EDIT` en `true` (y `DISALLOW_FILE_MODS` si el flujo de despliegue lo permite).
- `xmlrpc.php`: si el sitio no lo usa, se recomienda bloquearlo.
- Enumeración de usuarios (`/?author=1`, `/wp-json/wp/v2/users`): se recomienda cerrarla para anónimos.
- Un hallazgo de este apartado es **Baja** o **Media**; nunca se cambia sin autorización.

---

## Traducciones

- **Ningún texto visible hardcodeado.** `__()`, `esc_html__()`, `_n()`, `_x()`.
- **Un text domain por paquete**, igual al slug de la carpeta, escrito como literal — nunca en una
  variable ni concatenado: las herramientas de extracción no lo resuelven.
- Strings con variables por `printf` y placeholders numerados cuando hay más de uno:
  `printf( esc_html__( '%1$s of %2$s', '{prefix}-core' ), $a, $b )`.
- **Nunca se concatenan frases** a partir de trozos traducidos: en otros idiomas el orden cambia.

## Hooks

- Toda integración con WordPress es por `add_action` / `add_filter`. **Nada de ejecutar al cargar el
  archivo**: se engancha y se ejecuta cuando toca.
- Se usa el hook correcto, no el primero que funciona: `init` para registros, `wp_enqueue_scripts`
  para assets, `after_setup_theme` para soportes, `rest_api_init` para endpoints.
- Los callbacks son **funciones nombradas o métodos**, no closures, cuando algo pueda necesitar
  `remove_action` después. Un closure no se puede desenganchar.
- Prioridad por defecto (10) salvo motivo declarado. Una prioridad rara sin comentario es deuda.
- Todo lo propio va **prefijado** (`{prefix}_`, o el prefijo del cliente) o dentro de un **namespace**. El
  espacio de nombres de WP es global y plano: un `get_settings()` sin prefijo tumba el sitio.

## Assets

- **Siempre `wp_enqueue_style` / `wp_enqueue_script`.** Nunca un `<link>` o `<script>` escrito a mano en
  una plantilla.
- Versión real en el parámetro `$ver` (`filemtime()` en desarrollo) — sin eso, el navegador del cliente
  se queda con el CSS viejo y "no se ve el cambio".
- Dependencias declaradas de verdad en vez de confiar en el orden de carga.
- `defer`/`async` con `wp_script_add_data( $handle, 'strategy', 'defer' )` (WP 6.3+).
- **Solo se encola donde se usa**: condicional por plantilla, por `render_callback` del bloque o por
  `has_block()`. Cargar todo en todas las páginas es el problema de performance nº 1 de WP.
- Datos de PHP a JS con `wp_localize_script` o `wp_add_inline_script`, nunca con variables globales
  impresas en la plantilla.

## Datos, CPTs y campos

- **CPTs y taxonomías se registran en código**, en el mu-plugin del sitio, no con un plugin de UI. Lo
  que solo existe en la base de datos no se puede revisar en un PR ni desplegar.
- ACF (si el proyecto lo usa): los grupos de campos se versionan — **JSON sync** (`acf-json/`) o
  registro en PHP. Un campo creado solo en el admin de producción no existe para el resto del equipo.
- Los metadatos se registran con `register_post_meta` / `register_meta`, con `show_in_rest` cuando el
  bloque o el front los necesiten — así el editor y la API los conocen.
- **Cuidado con el `autoload` de las opciones.** Una opción grande con `autoload=yes` se carga en cada
  petición del sitio, para siempre.

## Performance

- `WP_Query` con lo mínimo: `'no_found_rows' => true` si no paginas,
  `'update_post_term_cache' / 'update_post_meta_cache' => false` si no los usas, `'fields' => 'ids'`
  cuando solo necesitas ids.
- **`'posts_per_page' => -1` está prohibido** salvo con un límite conocido y declarado.
- Nada de consultas dentro de un `foreach` sobre posts (N+1): se resuelve con una consulta previa.
- Lo caro se cachea en **transients**, con expiración y con la invalidación pensada.
- Imágenes por `wp_get_attachment_image()` — trae `srcset`, `sizes`, `width`, `height` y `loading` sin
  que haya que escribirlos. Tamaños propios con `add_image_size`, nunca escalando por CSS.

## CSS y JS

Valen las reglas del núcleo (`eden-code-style-rules.md`): BEM, mobile-first, tokens en vez de valores
hardcodeados, sin `!important`, sin IDs como selector. Lo propio de WP:

- Las clases que **genera WordPress** (`.wp-block-*`, `.alignwide`, `.has-*-color`, `.entry-content`) no
  se renombran ni se pelean: se aprovechan. Sobrescribirlas a la fuerza rompe el editor.
- Lo que se escribe debe verse igual **en el front y en el editor**. Un bloque que solo se ve bien en el
  front está a medio hacer.
- JS: Web Components en Light DOM, o los paquetes `@wordpress/*` según el sabor. **Sin jQuery en código
  nuevo**, aunque el tema lo cargue.

## Blast radius en WordPress — incluye la base de datos

Esta es la diferencia grande con Shopify: **en WP, parte del sitio vive en la base de datos**, no en el
repo. Antes de tocar algo compartido:

```bash
# En código
grep -rn "{funcion|hook|clase|clase-css}" wp-content/themes/{child} wp-content/mu-plugins wp-content/plugins/{propios}

# En contenido — lo que el repo no ve
wp db search "{shortcode|clase|nombre-de-bloque}" --stats
wp post list --post_type=any --format=count
```

Qué se comprueba, sin excepción:

- **Quién más usa** la función, el hook, el shortcode, el bloque o la clase.
- **Cuántas entradas publicadas** ya lo tienen. Renombrar un bloque o un shortcode con contenido
  publicado **rompe páginas que nadie va a revisar**: el contenido guarda el nombre viejo.
- Si el cambio afecta a un **campo ACF con datos**, qué pasa con lo ya cargado.
- Si el tema es un **child**, qué hereda del padre y qué pasa cuando el padre se actualice.

**Toda opción nueva lleva default neutro**, igual que en el núcleo: un `theme.json` o un ajuste nuevo no
puede cambiar cómo se ve una página que ya está publicada.

## Plugins de terceros

- **Antes de instalar un plugin se pregunta al dev.** Un plugin es código de otro corriendo en el sitio
  del cliente, con su superficie de ataque, su performance y su licencia.
- Criterio: ¿está mantenido (última actualización, compatibilidad declarada), tiene instalaciones
  reales, hace **solo** lo que necesitamos? Un plugin de 300 funciones para usar una es un mal trato.
- Cinco líneas propias ganan a un plugin. Un motor de formularios, de SEO o de caché no se reescribe.
- Los plugins **no se editan**: se extienden por sus hooks. Si no tiene hooks, se envuelve o se
  reemplaza — no se parchea.
- Lo que se instale queda declarado en el `CLAUDE.md` del proyecto y, si el proyecto usa Composer, en
  el `composer.json`.

## Qué NO se versiona

`wp-config.php` con credenciales, `wp-content/uploads/`, el core de WordPress, los plugins de terceros
(salvo que el proyecto use Composer/Bedrock a propósito), `.env`, y dumps de base de datos con datos
reales de clientes. Se versiona **lo nuestro**: child theme, mu-plugins propios, plugins propios y la
configuración del entorno local.

## Validación — la puerta

Antes de cerrar cualquier tarea, sobre **lo que se tocó**:

```bash
composer exec phpcs -- --standard=WordPress {rutas}    # WordPress Coding Standards
composer exec phpstan -- analyse {rutas}               # si el proyecto lo tiene
npx wp-scripts lint-js {rutas}                         # bloques / JS de WP
php -l {archivo}                                       # el mínimo indispensable
```

Errores en cero; los warnings se le explican al dev en español. Si el proyecto no tiene PHPCS montado,
se **propone** montarlo (`squizlabs/php_codesniffer` + `wp-coding-standards/wpcs`) y mientras tanto se
usa `php -l` como piso — **nunca se cierra sin ninguna validación**.

## Documentación de WordPress — verificar por año

WordPress cambia rápido, sobre todo en el editor de bloques. Ante duda o error se consulta la
documentación **vigente** (o context7) y se contrasta con cómo lo hace **este** proyecto — nunca de
memoria:

- Theme Handbook: https://developer.wordpress.org/themes/
- Block Editor Handbook: https://developer.wordpress.org/block-editor/
- Plugin Handbook: https://developer.wordpress.org/plugins/
- Referencia de funciones y hooks: https://developer.wordpress.org/reference/
- Coding Standards: https://developer.wordpress.org/coding-standards/
- WP-CLI: https://developer.wordpress.org/cli/commands/
- REST API: https://developer.wordpress.org/rest-api/
- WooCommerce: https://developer.woocommerce.com/docs/
- Novedades por versión: https://make.wordpress.org/core/

> Dirección reciente (2025–2026): consolidación de FSE y `theme.json` (v3), Interactivity API para el
> front, Block Bindings API para conectar bloques con metadatos sin crear un bloque custom,
> `wp_script_add_data` para estrategias de carga, y patterns registrados desde `patterns/` con cabecera
> PHP. Trátalos como punteros: confirma la firma exacta en la doc vigente antes de usarlos.
