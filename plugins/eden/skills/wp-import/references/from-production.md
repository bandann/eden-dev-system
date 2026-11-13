# Bajar un sitio de producción a local

La ruta más usada y la que más veces se hace mal. Tres caminos, según qué acceso haya.

## Elegir el camino

| Acceso disponible | Camino | Cuándo |
|---|---|---|
| SSH + WP-CLI en el servidor | **WP-CLI** | El mejor. Rápido, verificable, sin plugins |
| Solo wp-admin | **Plugin de migración** | Hosting compartido sin SSH |
| SFTP + phpMyAdmin | **Manual** | El último recurso |

### A · WP-CLI (preferido)

```bash
# En el servidor
wp db export /tmp/prod.sql --add-drop-table
tar -czf /tmp/uploads.tar.gz wp-content/uploads

# En local
scp usuario@servidor:/tmp/prod.sql .
scp usuario@servidor:/tmp/uploads.tar.gz .

wp db reset --yes            # ⚠️ borra la DB local — el backup ya está hecho (Paso 0)
wp db import prod.sql
tar -xzf uploads.tar.gz -C wp-content/
```

Y **borrar los archivos del servidor** al terminar: un `prod.sql` accesible por URL es una filtración
completa de la base de datos del cliente. Si el dump quedó dentro del docroot, es urgente.

### B · Plugin de migración

- **All-in-One WP Migration**: exporta a `.wpress`, hace el search-replace solo. Cómodo, pero la
  versión gratuita **limita el tamaño de importación** — en sitios grandes se atasca a la mitad.
- **Duplicator**: genera un instalador + archivo. Funciona bien y da control del reemplazo.
- **WP Migrate (DB)**: el más limpio si el cliente ya tiene licencia; hace push/pull de DB y uploads.

Con cualquiera de ellos, **igual se verifica el search-replace después** (Paso 3 del skill). Que el
plugin diga "success" no prueba que la serialización quedó bien.

### C · Manual (SFTP + phpMyAdmin)

Solo si no hay otra. Se baja el `.sql` por phpMyAdmin y los archivos por SFTP, se importa la DB con
`wp db import` (**no** por phpMyAdmin, que suele morir con dumps grandes) y el search-replace se hace
con WP-CLI en local. **Nunca con el buscar/reemplazar de phpMyAdmin**: no respeta la serialización.

## El search-replace, con sus cuatro variantes

```bash
wp search-replace 'https://cliente.com' 'https://cliente.ddev.site' --all-tables-with-prefix --precise --recurse-objects --report-changed-only --dry-run
wp search-replace 'http://cliente.com'  'https://cliente.ddev.site' --all-tables-with-prefix --precise --recurse-objects --report-changed-only --dry-run
wp search-replace '//cliente.com'       '//cliente.ddev.site'       --all-tables-with-prefix --precise --recurse-objects --report-changed-only --dry-run
```

Y, aparte, las **rutas absolutas del sistema de archivos**, que casi siempre se olvidan y rompen los
diseños de los builders:

```bash
wp db search "/var/www/" --stats
wp search-replace '/var/www/html/wp-content' '/{ruta-local}/wp-content' --precise --recurse-objects --dry-run
```

`--dry-run` primero, siempre. Se lee el reporte y **solo entonces** se repite sin él.

## Multisite

Es otra operación, no una variante:

```bash
wp site list --field=url
wp search-replace 'origen' 'destino' --network --url={url-del-sitio} --precise --recurse-objects --dry-run
```

Además hay que actualizar `wp-config.php` (`DOMAIN_CURRENT_SITE`) y la tabla `wp_blogs`. Si el sitio es
multisite y no se sabía, **se para y se replantea**: el tiempo estimado cambia.

## Desactivar lo que puede tocar el mundo real

Un sitio recién bajado sigue configurado para producción. **Antes de trabajar en él**, se apaga lo que
puede mandar correos, cobrar o sincronizar de verdad:

```bash
wp plugin deactivate {smtp} {pasarela-de-pago} {automatizaciones} {crm} {caché} {cdn} {backups} {seguridad}
wp option update blog_public 0        # no indexar
wp user create dev-local dev@local.test --role=administrator
```

En WooCommerce, además: pasarelas a modo test o desactivadas, y los correos de pedido apagados. **Un
sitio de local mandando correos de pedido a clientes reales es un incidente**, y ha pasado.

Las claves de API de producción se sustituyen por las de test o se vacían. Nunca se dejan las reales en
un entorno local.

## Licencias atadas al dominio

Temas y plugins de pago suelen activar la licencia contra el dominio. En local puede que no activen —
**eso es normal y no se arregla desactivando la comprobación ni parcheando el plugin**. Se anota en el
reporte y, si bloquea el trabajo, se le pide al cliente una licencia de desarrollo.

## Verificación específica de esta ruta

Además de la lista del skill:

- Comparar el conteo de posts por tipo entre origen y destino:
  `wp post list --post_type=any --format=count` en los dos.
- `wp db search "{dominio-origen}" --stats` → debería dar cero, salvo en logs históricos.
- Abrir una página armada con el **builder** o con muchos **campos ACF**: es donde se ve si la
  serialización sobrevivió.
- `wp rewrite flush` y probar un permalink profundo.
