# Elegir el sabor de WordPress — criterios

El sabor **casi nunca es una elección libre**: lo impone el sitio que ya existe. Solo es una decisión
abierta en un proyecto desde cero. Este archivo dice cómo decidir en ambos casos, y qué se pierde con
cada opción.

## Cómo se detecta el sabor de un sitio que ya existe

| Señal | Sabor probable |
|---|---|
| `theme.json` en el tema activo + `templates/*.html` | **block-theme** |
| Plugin Elementor / Divi / WPBakery / Beaver activo **y con páginas armadas** | **page-builder** |
| Tema con `index.php`, `single.php`, `template-parts/` y sin `theme.json` | **classic-theme** |
| WPGraphQL o un front en otra carpeta consumiendo la REST | **headless** |

Comprobaciones que evitan el error clásico:

```bash
wp theme list --status=active --fields=name,version,parent
wp plugin list --status=active --fields=name,version
wp post list --post_type=elementor_library --format=count    # ¿el builder se usa de verdad?
wp db search "wp:paragraph" --stats                          # ¿hay contenido en bloques?
```

**Que un plugin esté instalado no significa que el sitio se construya así.** Un Elementor activo con 0
plantillas y todo el contenido en bloques es un block theme con un plugin de más. Se mide el
**contenido**, no la lista de plugins.

Si el sitio es **mixto** (lo normal en sitios viejos: páginas de Elementor + entradas en bloques), se
declara el sabor **de lo que vamos a construir**, y se anota el otro en el `CLAUDE.md` como territorio
que existe y no se toca sin avisar.

## Proyecto desde cero — cuál recomendar

| Si el proyecto… | Recomendar | Por qué |
|---|---|---|
| Es un sitio de marketing/contenido que el cliente va a editar mucho | **block-theme** | El editor nativo, sin licencias ni plugin de por medio; `theme.json` es un sistema de tokens de verdad |
| Tiene mucha lógica a medida, integraciones o plantillas muy específicas | **classic-theme** | Control total del markup; el más parecido a trabajar con Liquid |
| Lo va a mantener el cliente o un no-dev, y el diseño cambia seguido | **page-builder** | Autonomía real del cliente; el coste es performance y que el diseño vive en la DB |
| Ya hay un front en Next/Astro, o se necesita rendimiento y stack JS | **headless** | Cada lado con sus reglas; el coste es que previews, caché y contratos hay que resolverlos a mano |

## Qué se gana y qué se pierde — decirlo antes, no después

- **block-theme**: se gana un sistema de tokens nativo y edición sin plugins. Se pierde control fino
  del markup, y hay que cuidar que **el editor se vea como el front** (si no, el cliente edita a
  ciegas). Los bloques estáticos rompen contenido publicado al cambiar el `save`: por eso el kit pide
  bloques dinámicos por defecto.
- **classic-theme**: se gana control absoluto. Se pierde la edición visual — **todo lo que no sea un
  campo, el cliente no lo puede cambiar**, y eso vuelve como tickets. Por eso el kit insiste en que el
  contenido editable sea un campo, no un literal en la plantilla.
- **page-builder**: se gana autonomía del cliente. Se pierde el repo como fuente de verdad: **el
  diseño vive en la base de datos**, el PR no cuenta la historia completa y el blast radius se mide con
  `wp db search`. Además hay coste de performance que no está en nuestras manos del todo.
- **headless**: se gana el front. Se pierde la simplicidad: previews, invalidación de caché, imágenes
  y el contrato de la API son trabajo real que hay que estimar desde el principio, no descubrir a mitad.

## WooCommerce cruza los cuatro

Woo no es un sabor: se monta encima de cualquiera. Si el proyecto lo lleva, se declara
(`wordpress.woocommerce: true`) y se tiene en cuenta que:

- Sus plantillas se sobrescriben **copiándolas al child theme** en `woocommerce/{ruta}`, respetando la
  ruta original. Nunca editando el plugin.
- Muchas cosas se resuelven mejor con sus **hooks** (`woocommerce_before_shop_loop`, etc.) que
  sobrescribiendo la plantilla entera: una plantilla copiada queda congelada y hay que revisarla en cada
  actualización de Woo.
- Sus plantillas copiadas llevan la versión en la cabecera: cuando Woo la actualiza, avisa. Ese aviso se
  atiende, no se silencia.

## Qué se escribe al decidir

En `project-config.json` → `wordpress.flavor`, y `wordpress.builder` si es page-builder.
En el `CLAUDE.md` → el marcador `<!-- eden-wp: flavor=… -->`.
En `docs/wordpress-setup.md` → **el porqué**, incluida la opción que se descartó y su motivo. Dentro de
seis meses, alguien va a preguntar por qué no se hizo con bloques.
