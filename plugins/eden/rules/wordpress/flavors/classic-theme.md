# Sabor: Tema clásico PHP — WordPress

Template hierarchy, `functions.php`, `get_template_part()`, campos con ACF y estilos propios. Es el
sabor más cercano a trabajar con Liquid: **plantillas que renderizan datos, con partials reutilizables
y una capa de configuración por encima**.

## Estructura

```
{child-theme}/
├── style.css              cabecera (Template: {padre})
├── functions.php          SOLO enqueues, supports y requires — nada de lógica
├── inc/                   la lógica de presentación, en archivos por tema
├── template-parts/        los partials: sections/, components/, loops/
├── templates/             plantillas de página con cabecera Template Name
├── acf-json/              grupos de campos versionados (sync automático)
├── assets/{css,js,img}/
├── {archivos de la jerarquía}: front-page.php, single.php, page.php, archive.php, 404.php
└── partials propios
```

**`functions.php` no crece.** En cuanto pasa de encolar y declarar supports, se parte en `inc/` y se
incluye desde ahí. Un `functions.php` de 900 líneas es la señal más fiable de un tema que nadie quiere
tocar.

## La template hierarchy es la que manda

Antes de crear un archivo nuevo se comprueba **qué plantilla usa WordPress de verdad** para esa URL. La
mitad de los "no me toma el cambio" son un archivo editado que WordPress nunca carga.

```bash
wp eval 'echo get_page_template();'      # con Query Monitor activo se ve en el navegador
```

- Se sobrescribe una plantilla del padre **copiándola al child con la misma ruta**, no con hooks
  raros.
- Un template part se saca con `get_template_part( 'template-parts/sections/hero', null, $args )` —
  con `$args` (WP 5.5+), **nunca con variables globales**.
- Las plantillas de página con `Template Name:` se registran solas; no hace falta código.

## Escalera reuse-first en un tema clásico

1. **Un template part que ya existe, con sus `$args`.** Sin código nuevo.
2. **Extender ese partial con un argumento nuevo de default neutro** — el partial se ve exactamente
   igual donde ya se usa, y el valor distinto se pasa solo desde la plantilla que lo pide.
3. **Un campo de configuración** (grupo ACF, opción del Customizer) para que el cambio lo maneje el
   cliente en vez de estar fijo en el código.
4. **Código mínimo acotado** al partial que se está trabajando, con su CSS en BEM del bloque.
5. **Partial nuevo** — último recurso, con nombre propio, namespace de clases propio y su propio CSS.

## Datos y campos

- El contenido editable **no se hardcodea en la plantilla**: es un campo ACF, una opción o el propio
  contenido del post. Si el cliente no lo puede cambiar, en tres meses hay un ticket para cambiarlo.
- Los grupos ACF se versionan en `acf-json/` (sync activado) o se registran en PHP. **Un campo creado
  solo en el admin no existe para el resto del equipo.**
- Los campos se leen con su fallback pensado: `get_field()` puede devolver `null`, `''` o `false`, y la
  plantilla no debe imprimir un contenedor vacío por eso.
- Lo que es **funcionalidad** (CPTs, taxonomías, endpoints, integraciones) no va aquí: va al mu-plugin
  del sitio. Ver `../eden-wordpress-rules.md`.

## Estilos

- BEM acotado al partial, siguiendo `eden-code-style-rules.md`.
- Los tokens del proyecto viven en **custom properties propias**, en un único archivo del tema
  (p. ej. `assets/css/_tokens.css` o un `:root` generado desde el Customizer), y se cargan primero.
  Nunca un hex suelto en el CSS de una sección.
- Un archivo CSS por sección/componente, encolado **condicionalmente** cuando la sección se usa, si el
  proyecto lo permite. Si el proyecto compila a un bundle, se sigue el bundle: la convención del
  proyecto gana.
- Las clases que genera WordPress (`.entry-content`, `body_class()`, `post_class()`) se aprovechan; no
  se pelean.

## Loops

- El loop principal no se reemplaza con un `WP_Query` nuevo: se ajusta con `pre_get_posts`. Sustituirlo
  rompe la paginación, el `is_main_query()` de los plugins y el SEO.
- En loops secundarios, `wp_reset_postdata()` **siempre** después.
- Se pagina; `'posts_per_page' => -1` está prohibido salvo límite conocido y declarado.

## Fidelidad al Figma

- Mobile-first, con los breakpoints exactos del `project-config.json` (los anchos reales de los frames
  de Figma).
- Las imágenes por `wp_get_attachment_image()` con el `add_image_size` correcto — no un `<img>` a mano,
  y no escalando por CSS una imagen de 3000px.
- Si el Figma difiere entre mobile y desktop, se implementan ambos: es un requerimiento, no un error
  del diseñador.

## Validación propia de este sabor

```bash
php -l {archivo}
composer exec phpcs -- --standard=WordPress {rutas}
```

Y en el navegador, con **Query Monitor** activo: sin PHP notices, sin queries duplicadas, y la
plantilla que se está viendo es la que se cree que es.
