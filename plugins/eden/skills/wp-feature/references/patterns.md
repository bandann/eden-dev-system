# Moldes de funcionalidad en WordPress

Todo esto vive en el **mu-plugin del sitio**, no en el tema. Los ejemplos usan `{Namespace}\Core` (`project.namespace`, p. ej. `Acme`) y el prefijo
`{prefix}_`: se sustituyen por los del proyecto (`project.prefix` / `wordpress.prefix`, `wordpress.text_domain`).

## Custom post type

```php
<?php
namespace {Namespace}\Core\PostTypes;

defined( 'ABSPATH' ) || exit;

add_action( 'init', __NAMESPACE__ . '\register_case_study' );
function register_case_study(): void {
    register_post_type(
        '{prefix}_case_study',                       // ≤ 20 caracteres, prefijado, singular
        array(
            'labels'       => array(
                'name'          => __( 'Case Studies', '{prefix}-core' ),
                'singular_name' => __( 'Case Study', '{prefix}-core' ),
            ),
            'public'       => true,
            'has_archive'  => true,
            'menu_icon'    => 'dashicons-portfolio',
            'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt', 'revisions' ),
            'rewrite'      => array( 'slug' => 'case-studies', 'with_front' => false ),
            'show_in_rest' => true,            // sin esto no existe para el editor ni para el front
        )
    );
}
```

Decisiones que hay que tomar a propósito, no por defecto:

- **`public` vs `publicly_queryable`**: si el contenido solo alimenta otra página (un slider, unos
  testimonios), **no debería tener URL propia** — una URL sin diseño es una página fea indexada por
  Google. `'public' => false, 'show_ui' => true, 'show_in_rest' => true`.
- **`has_archive`**: solo si de verdad va a existir una plantilla de archivo. Si no, es un 404 con
  contenido.
- **`supports`**: quitar lo que no se usa. Un editor de contenido en un CPT que solo tiene campos
  confunde al cliente y acaba con texto suelto que nadie renderiza.
- Tras registrar: **`wp rewrite flush`**, y anotarlo como paso de deploy.

## Taxonomía

```php
add_action( 'init', __NAMESPACE__ . '\register_industry' );
function register_industry(): void {
    register_taxonomy(
        '{prefix}_industry',
        array( '{prefix}_case_study' ),
        array(
            'labels'            => array( 'name' => __( 'Industries', '{prefix}-core' ) ),
            'hierarchical'      => true,      // true = categorías · false = etiquetas
            'show_admin_column' => true,
            'show_in_rest'      => true,
            'rewrite'           => array( 'slug' => 'industry' ),
        )
    );
}
```

**Una taxonomía casi siempre gana a un campo de selección**: trae archivo, filtrado, REST y UI gratis, y
el cliente puede añadir valores sin tocar código.

## Metadatos nativos

```php
add_action( 'init', __NAMESPACE__ . '\register_meta_fields' );
function register_meta_fields(): void {
    register_post_meta(
        '{prefix}_case_study',
        '{prefix}_client_name',
        array(
            'type'              => 'string',
            'single'            => true,
            'show_in_rest'      => true,
            'sanitize_callback' => 'sanitize_text_field',
            'auth_callback'     => static fn(): bool => current_user_can( 'edit_posts' ),
        )
    );
}
```

`register_post_meta` (y no `update_post_meta` a secas) es lo que hace que el campo exista para el
editor, para la REST y para las Block Bindings.

## Campos con ACF

- Se crean en el admin **y se versionan**: `acf-json/` con el sync activado, o registro en PHP.
- El directorio se declara desde el mu-plugin:
  ```php
  add_filter( 'acf/settings/save_json', fn() => __DIR__ . '/acf-json' );
  add_filter( 'acf/settings/load_json', fn( array $paths ) => array( __DIR__ . '/acf-json' ) );
  ```
- Al leer, **fallback siempre**: `get_field()` puede devolver `null`, `''`, `false` o un array vacío, y
  la plantilla no debe imprimir un contenedor vacío por eso.
- Los grupos se nombran con prefijo, y sus claves (`field_...`) **no se editan a mano**.

## Endpoint REST

```php
add_action( 'rest_api_init', __NAMESPACE__ . '\register_routes' );
function register_routes(): void {
    register_rest_route(
        '{prefix}/v1',                                   // namespace propio y versionado
        '/subscribe',
        array(
            'methods'             => 'POST',
            'callback'            => __NAMESPACE__ . '\handle_subscribe',
            'permission_callback' => __NAMESPACE__ . '\can_subscribe',   // NUNCA __return_true al escribir
            'args'                => array(
                'email' => array(
                    'required'          => true,
                    'sanitize_callback' => 'sanitize_email',
                    'validate_callback' => static fn( $v ): bool => (bool) is_email( $v ),
                ),
            ),
        )
    );
}
```

- **La forma de la respuesta es un contrato.** Cambiarla rompe el front en producción: es un breaking
  change y se trata como tal. Por eso el namespace lleva versión.
- Se devuelve `WP_Error` con código y estado, no un `array( 'error' => ... )` con 200.
- Rate limiting o nonce en endpoints públicos que escriben: un formulario abierto sin freno es un
  formulario de spam.

## Acción del admin (formulario o AJAX)

Las cuatro guardas, siempre las cuatro:

```php
function handle_save(): void {
    // 1. nonce — la petición vino de nuestro formulario
    if ( ! wp_verify_nonce( wp_unslash( $_POST['_wpnonce'] ?? '' ), '{prefix}_save_x' ) ) {
        wp_die( esc_html__( 'Invalid request.', '{prefix}-core' ) );
    }
    // 2. capability — este usuario puede hacerlo
    if ( ! current_user_can( 'manage_options' ) ) {
        wp_die( esc_html__( 'Not allowed.', '{prefix}-core' ) );
    }
    // 3. sanitize a la entrada
    $value = sanitize_text_field( wp_unslash( $_POST['value'] ?? '' ) );
    // 4. escape a la salida, donde se imprima
    update_option( '{prefix}_x', $value );
}
```

Nonce y capability **no son lo mismo y no se sustituyen**: el nonce dice de dónde vino; la capability,
quién es.

## Consultas

```php
$query = new \WP_Query(
    array(
        'post_type'              => '{prefix}_case_study',
        'posts_per_page'         => 6,          // nunca -1 sin límite declarado
        'no_found_rows'          => true,       // si no se pagina
        'update_post_term_cache' => false,      // si no se usan sus términos
        'ignore_sticky_posts'    => true,
    )
);
// ... y wp_reset_postdata() al terminar, siempre
```

**Nunca una consulta dentro de un `foreach` sobre posts.** Si hace falta un dato de cada uno, se trae
en una consulta previa.

## WooCommerce

- Las plantillas se sobrescriben **copiándolas al child theme** en `woocommerce/{ruta-original}`. Nunca
  editando el plugin.
- **Antes de copiar una plantilla, mirar si hay un hook** (`woocommerce_before_shop_loop`,
  `woocommerce_single_product_summary`, …). Una plantilla copiada queda congelada y hay que revisarla en
  cada actualización de Woo; un hook no.
- Las plantillas copiadas llevan su versión en la cabecera: cuando Woo la actualiza, avisa en el panel
  de estado. **Ese aviso se atiende, no se silencia.**
- Los datos de producto se leen del objeto (`$product->get_price()`), no de la meta cruda.

## Lo que no se hace nunca

- Registrar CPTs, taxonomías o campos **desde el tema**. Cambia el tema → el cliente pierde sus datos.
- Crearlos con un plugin de UI: lo que solo existe en la DB no se revisa en un PR ni se despliega.
- Un `permission_callback => '__return_true'` en algo que escribe.
- SQL directo cuando `WP_Query` / `get_posts` / `get_terms` lo resuelven.
- Un slug sin prefijo, o cambiarlo después de que haya contenido publicado.
