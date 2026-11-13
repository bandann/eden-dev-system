# Fallos típicos de WordPress y su causa real

La regla que ahorra más tiempo: **leer el log antes de tocar nada**. Casi todo en WP deja rastro, y
probar cambios a ciegas convierte un problema de diez minutos en uno de dos horas.

```bash
tail -n 100 wp-content/debug.log
```

Si no hay `debug.log`, es que `WP_DEBUG_LOG` está apagado. Ese es el primer arreglo, no el último.

---

## Pantalla blanca (WSOD)

**Es un fatal de PHP.** No es un misterio: está en el log.

1. `tail -n 50 wp-content/debug.log` → el archivo y la línea vienen ahí.
2. Si el log está vacío, encender `WP_DEBUG_LOG` y recargar.
3. Si aun así nada, `php -l {archivo-que-se-tocó}` — un error de sintaxis impide que WP arranque, así
   que no puede ni escribir el log.
4. Solo si nada de lo anterior: desactivar plugins por CLI (`wp plugin deactivate --all`) y reactivar de
   a uno. **Este es el último paso, no el primero.**

Causa más frecuente en trabajo propio: una llamada a una función de un plugin que no está activo, o un
`require` con la ruta mal.

## "No se aplica mi CSS/JS"

Por orden de probabilidad:

1. **La versión del enqueue.** Sin `filemtime()` en `$ver`, el navegador sirve el archivo viejo. Es la
   causa nº 1.
2. **Un plugin de caché** activo en local. Se desactiva.
3. **El handle del padre está mal** en el child theme: el CSS del hijo carga antes que el del padre y
   queda pisado. Se comprueba con `grep -rn "wp_enqueue_style" {tema-padre}`.
4. **El archivo no se está encolando** en esa página (condicional que no se cumple, `has_block()` que da
   falso).
5. Se está editando **un archivo que WordPress no carga**: ver abajo.

Comprobación directa en el navegador: buscar el handle en el HTML y ver si el `<link>` está y con qué
`?ver=`.

## "Edito la plantilla y no cambia nada"

Se está editando un archivo que WordPress no usa para esa URL. La template hierarchy decide, no
nosotros:

```bash
wp eval 'echo get_page_template();'
```

O con Query Monitor, en el panel "Template". Sub-causas típicas: el archivo está en el tema padre y hay
un child activo (o al revés), o la página usa una plantilla asignada distinta, o el sabor es
page-builder y **el diseño no está en un archivo, está en la base de datos**.

## Permalinks 404

```bash
wp rewrite flush
```

Si vuelve a pasar tras registrar un CPT: falta el flush **después** del registro, y en producción hay
que ejecutarlo a propósito tras el deploy. Si sigue, es la config del servidor (nginx sin
`try_files`, o `.htaccess` no escribible).

## Error al establecer conexión con la base de datos

Credenciales de `wp-config.php` que no coinciden con el entorno, o el contenedor de DB caído.

```bash
ddev describe          # o docker compose ps
wp db check
```

En un sitio recién importado, casi siempre es que el `wp-config.php` vino de producción.

## El bloque se ve bien en el front y roto en el editor

Los estilos del bloque no están encolados para el editor. En `block.json`, `style` es front+editor y
`editorStyle` es solo editor. Un bloque que solo se ve bien en el front está a medio hacer: **el
cliente edita ahí**.

## "This block contains unexpected or invalid content"

Cambió el `save` de un bloque **estático** y el contenido publicado guarda el markup viejo. Se arregla
con una `deprecated` en el bloque, no pidiéndole al cliente que le dé a "recuperar".

Por eso el kit pide **bloques dinámicos (`render_callback`) por defecto**: el markup se genera al
renderizar y cambiarlo no rompe nada publicado.

## Campos ACF vacíos tras una importación

La serialización se rompió: el search-replace se hizo sin `--precise --recurse-objects`, o con `sed`
sobre el `.sql`. **No se arregla a mano.** Se restaura el backup y se repite bien.

## Cambios que aparecen y desaparecen

- Un plugin de caché de objetos (Redis/Memcached) sirviendo datos viejos: `wp cache flush`.
- Dos entornos apuntando a la misma DB.
- Un cron o una sincronización que sobrescribe lo que se guarda.

## El sitio va lentísimo en local

Con Query Monitor, mirar **número de queries y las más lentas**. Lo habitual: un `posts_per_page => -1`,
un N+1 dentro de un `foreach`, o un plugin haciendo llamadas HTTP externas en cada carga (`wp
transient delete --all` y ver si cambia).

## Correos que salen de verdad desde local

Pasa, y es un incidente. El sitio bajado de producción conserva su SMTP. Se desactiva el plugin de SMTP
**antes** de trabajar, o se instala un capturador local. Va en la lista de `up`.

## Un sitio heredado que "hace cosas raras"

Antes de investigar nada:

```bash
wp core verify-checksums
wp plugin verify-checksums --all
```

Muy a menudo alguien editó el core o un plugin directamente. Si es así, eso explica el
comportamiento — y también explica por qué el sitio no se puede actualizar. Se reporta al dev antes de
seguir: cambia el alcance de lo que se estaba haciendo.
