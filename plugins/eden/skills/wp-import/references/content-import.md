# Importar contenido: WXR y demo de tema

Dos casos que se parecen y no son lo mismo.

## Caso A — WXR (`.xml`, el exportador nativo de WordPress)

El WXR trae **posts, páginas, CPTs, taxonomías, comentarios y usuarios**. No trae: opciones del sitio,
widgets, menús asignados, configuración de plugins ni los archivos de `uploads/` (solo sus URLs).

```bash
wp plugin install wordpress-importer --activate
wp import content.xml --authors=create --skip=image_resize
```

- `--authors=create` crea los autores que falten; `--authors=mapping.csv` los mapea a usuarios
  existentes. **Sin uno de los dos, el import falla a mitad** y deja el contenido a medias.
- **Las imágenes se descargan desde el sitio de origen**, así que ese sitio tiene que seguir en pie
  mientras corre. Si ya no existe, las imágenes no llegan y hay que traer `uploads/` aparte.
- Es lento y **no es idempotente**: correrlo dos veces duplica contenido. Antes de reintentar,
  restaurar el backup.

Después:

```bash
wp media regenerate --yes         # thumbnails en los tamaños de ESTE tema
wp rewrite flush
```

## Caso B — Contenido demo de un tema comprado

Casi siempre viene con un importador propio del tema (One Click Demo Import o similar) que trae, además
del WXR, los **widgets, menús, opciones del Customizer y plantillas del builder**. Eso es lo que hace
que el sitio se vea como en la demo.

Reglas para no arrepentirse:

1. **Se importa en una instalación limpia, nunca sobre un sitio con contenido.** Un demo import
   sobrescribe opciones, menús y páginas de inicio. Si ya hay contenido del cliente, **se para y se
   pregunta**.
2. Backup antes, sí o sí.
3. El demo trae **imágenes con licencia del tema** — placeholders. No se entregan al cliente como parte
   del sitio final. Se anota en el reporte lo que hay que reemplazar.
4. El demo suele activar **plugins que no queremos** (sliders, form builders, "core" del tema). Se
   revisa qué quedó activo y se decide con el dev.
5. Tras importar: revisar la página de inicio asignada, los menús, los widgets y los permalinks. Casi
   siempre falta asignar algo a mano.

```bash
wp option get show_on_front && wp option get page_on_front
wp menu list
wp rewrite flush
```

## Trabajar con contenido de mentira

Si el trabajo es de maquetación y no hay contenido real todavía, es mejor **contenido de prueba
generado** que un demo entero:

```bash
wp post generate --count=20 --post_type=post
wp term generate --taxonomy=category --count=5
```

Y una advertencia que ahorra rehacer trabajo: **maquetar solo con contenido perfecto es una trampa**.
Se prueba con el título larguísimo, sin imagen destacada, con el texto vacío y con acentos y emojis.
Los estados vacíos y de desbordamiento son parte del diseño, no un extra.

## Verificación

- Conteo por tipo de contenido: `wp post list --post_type={x} --format=count`.
- ¿Las imágenes destacadas se asignaron? `wp post list --post_type=post --field=ID | head` y comprobar
  un par con `wp post meta get {id} _thumbnail_id`.
- Términos y jerarquías: `wp term list {taxonomia}`.
- Sin duplicados por un import repetido.
- Los medios existen en `uploads/` y no solo como fila en la DB.
