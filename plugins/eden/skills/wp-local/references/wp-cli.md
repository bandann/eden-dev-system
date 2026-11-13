# WP-CLI — las tareas que se repiten

Todos los comandos van con el **prefijo del entorno** (`wp`, `ddev wp`, `npx wp-env run cli wp`,
`docker compose exec wordpress wp --allow-root`). Aquí se escriben con `wp` por brevedad.

## Inspección — sin riesgo, se corre libremente

```bash
wp core version --extra
wp option get home ; wp option get siteurl
wp theme list --fields=name,status,version,parent
wp plugin list --fields=name,status,version,update
wp post list --post_type=any --format=count
wp post-type list --fields=name,label,public
wp taxonomy list
wp user list --fields=ID,user_login,roles
wp cron event list
wp db size --tables --human-readable
```

## Buscar en la base de datos — el blast radius de WP

Lo que el `grep` del repo no ve. **Antes de renombrar un bloque, un shortcode o una clase:**

```bash
wp db search "{shortcode|clase|nombre-de-bloque}" --stats
wp db search "wp:{prefijo}/{bloque}" --stats
```

Si aparece en contenido publicado, renombrar **rompe esas páginas** y nadie va a revisarlas. O no se
renombra, o se migra el contenido a propósito.

## Contenido

```bash
wp post list --post_type=page --fields=ID,post_title,post_name
wp post get {id} --field=content
wp post meta list {id}
wp media regenerate --yes            # tras cambiar add_image_size
wp rewrite flush                     # tras tocar CPTs, taxonomías o permalinks
```

`wp rewrite flush` es la respuesta a la mitad de los 404 después de registrar un CPT. **Registrar un
CPT no refresca las reglas solo**, y en producción hay que hacerlo a propósito tras el deploy.

## Base de datos

```bash
wp db export "backups/$(date +%Y%m%d-%H%M).sql"   # antes de CUALQUIER cosa destructiva
wp db import archivo.sql
wp db check
wp db optimize
```

```bash
# search-replace: dry-run SIEMPRE primero
wp search-replace 'origen' 'destino' --all-tables-with-prefix --precise --recurse-objects --report-changed-only --dry-run
```

`--precise --recurse-objects` es lo que respeta los datos **serializados**. Sin eso se corrompen los
campos ACF, los widgets y los diseños del builder, y **no da ningún error**: simplemente desaparecen.

## Usuarios

```bash
wp user create dev-local dev@local.test --role=administrator
wp user update {id} --user_pass={x}
wp user list --role=administrator
```

En un sitio bajado de producción, **se crea un usuario propio en vez de cambiarle la contraseña a uno
del cliente**. Cambiar credenciales ajenas en un clon local es una costumbre que algún día se hace en
el entorno equivocado.

## Plugins y temas

```bash
wp plugin deactivate {slug}
wp plugin activate {slug}
wp plugin list --update=available
wp theme activate {slug}
```

**Instalar un plugin se pregunta antes** (`rules/wordpress/eden-wordpress-rules.md`). Actualizar plugins
tampoco es una tarea silenciosa: en un sitio de cliente, una actualización cambia el front. Se propone,
no se ejecuta de paso.

## Diagnóstico

```bash
wp core verify-checksums                 # ¿alguien editó el core?
wp plugin verify-checksums --all         # ¿alguien editó un plugin?
wp eval 'var_dump( WP_DEBUG );'
wp eval 'echo get_page_template();'      # qué plantilla usa esta URL de verdad
wp option get active_plugins --format=json
```

`verify-checksums` es la primera comprobación en un sitio heredado que "hace cosas raras": muy a menudo
alguien editó el core o un plugin, y por eso nada cuadra.

## Datos de prueba

```bash
wp post generate --count=20 --post_type=post
wp term generate --taxonomy=category --count=5
```

## Lo que exige confirmación y backup

`db reset` · `db import` · `db drop` · `post delete` · `plugin delete` · `theme delete` ·
`search-replace` sin `--dry-run` · `user delete` · cualquier `eval` que escriba.

La regla: **si cambia datos, se dice qué va a cambiar y cuántos registros afecta, y se espera el sí.**
