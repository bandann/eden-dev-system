# El camino de vuelta: local → staging → producción

Subir es más peligroso que bajar, porque **arriba hay contenido real que el cliente ha creado mientras
tú trabajabas**. La regla que resuelve el 90% de los accidentes:

> **El código sube. La base de datos, no.**

El código viaja por git y por deploy. La base de datos de producción es del cliente: sus páginas, sus
pedidos, sus formularios. Sobrescribirla con la local **borra días de trabajo ajeno**.

## Qué sube y qué no

| Sube | No sube |
|---|---|
| Child theme | La base de datos entera |
| mu-plugins y plugins propios | `wp-config.php` |
| `theme.json`, patterns, bloques | `uploads/` local (salvo assets nuevos concretos) |
| `acf-json/` (definiciones de campos) | Usuarios, pedidos, comentarios locales |
| Migraciones/scripts declarados | Contenido de prueba |

**Las excepciones a "la DB no sube" existen y se tratan como excepción**, nunca como rutina:

- Un sitio **nuevo** que aún no está en producción: ahí sí sube entera, la primera vez.
- Cambios que **solo viven en la DB** (diseños de page builder, menús, opciones). Se suben con
  `wp export`/import acotado a esos posts, o se rehacen a mano en el destino con la lista de cambios
  del cierre. Ver `flavors/page-builder.md`.

## Autorización

- **Push a staging**: la autorización normal de la rama de trabajo.
- **Push a producción**: autorización **explícita del dev en el momento**, distinta de cualquier otra
  que haya dado antes (`eden-git-rules.md`). Un import hacia producción no se ejecuta "porque el ticket
  lo pedía".
- **Backup del destino antes de escribir**, siempre, y se dice dónde quedó:
  ```bash
  wp db export "backups/pre-deploy-$(date +%Y%m%d-%H%M).sql"
  ```

## Procedimiento

1. **Backup del destino** (arriba).
2. **Subir el código** por el mecanismo del proyecto: git pull en el servidor, CI/CD, o SFTP si no hay
   otra. El mecanismo se declara en `docs/wordpress-setup.md`; no se improvisa uno nuevo.
3. **Sincronizar dependencias** si el proyecto usa Composer o npm: `composer install --no-dev`,
   `npm ci && npm run build`. El `build/` compilado en local no siempre debe viajar — se sigue lo que el
   proyecto ya haga.
4. **Migraciones y activaciones**, si las hay (registrar un CPT nuevo, crear una tabla, `wp rewrite
   flush`). Se ejecutan a mano y se listan.
5. **Purgar cachés**: plugin de caché, OPcache, CDN. Si no, el cliente entra y "no cambió nada".
   ```bash
   wp cache flush
   wp rewrite flush
   ```
6. **Verificar en el destino**, no en local (ver abajo).

## Antes de que staging sea pública

- **Bloquear la indexación**: `wp option update blog_public 0`, y auth básica en el servidor. Una
  staging indexada compite con el sitio del cliente en Google y es un problema real de SEO.
- Correos y pagos en modo test, igual que en local.
- Datos: si staging es un clon de producción, tiene datos personales reales. Aplica lo mismo que en
  `from-production.md`.

## Verificación en el destino

```bash
wp option get home && wp option get siteurl
wp plugin list --status=active          # ¿coincide con lo esperado?
wp theme list --status=active
wp cron event list                      # ¿hay crons que no deberían correr en staging?
```

Y en el navegador: la home, **la página exacta del cambio**, el admin, y —si hay Woo— un producto y el
carrito. Sin errores de consola, sin PHP notices nuevos.

## El link de preview del cierre

El comentario de cierre lleva un link **a la página exacta del cambio**, nunca la home, y uno por página
tocada (`eden-workflow-rules.md`). En WordPress eso es la URL de staging de esa página:
`https://staging.cliente.com/{ruta-de-la-página}`. Si la staging está tras auth básica, se dice cómo
entrar en el mismo comentario — un reviewer que se topa con un login y no sabe la clave no revisa nada.

## Lo que nunca se hace

- Editar código directamente en el servidor de producción.
- Un `wp db import` sobre producción sin autorización explícita y sin backup verificado.
- Un search-replace sobre producción "para arreglar algo rápido". Si el dominio de producción está mal
  en la DB, eso es un incidente y se trata como tal, con backup y con el dev presente.
- Dejar `WP_DEBUG` encendido arriba.
