# Entornos locales de WordPress — soportar los cuatro, recomendar uno

El kit soporta **LocalWP, DDEV, wp-env y Docker propio**. La regla de oro: **si el proyecto ya tiene
uno funcionando, gana ese.** Migrar un entorno que funciona no es trabajo del ticket.

## Detección

```bash
ls -d .ddev 2>/dev/null                  # DDEV
ls .wp-env.json 2>/dev/null              # wp-env
ls docker-compose.yml 2>/dev/null        # Docker propio
ls ~/Local\ Sites 2>/dev/null            # LocalWP (macOS/Windows)
wp --info 2>/dev/null                    # ¿hay WP-CLI y contra qué apunta?
```

## Comparación honesta

| | **LocalWP** | **DDEV** | **wp-env** | **Docker propio** |
|---|---|---|---|---|
| Se maneja con | GUI | CLI | CLI (npm) | CLI |
| Reproducible en el repo | No | **Sí** (`.ddev/`) | **Sí** (`.wp-env.json`) | Sí |
| Instalar es | Muy fácil | Fácil (requiere Docker) | Fácil (requiere Docker + npm) | Depende de ti |
| Importar un sitio grande | **Muy fácil** (arrastrar) | Fácil (`ddev import-db`) | Incómodo | Manual |
| Cambiar versión de PHP | GUI | Una línea | Una línea | Manual |
| Múltiples sitios a la vez | **Sí, cómodo** | Sí | Uno por proyecto | Sí |
| Ideal para | Clonar sitios de clientes | **Equipos y sitios existentes** | **Desarrollo de temas/bloques** | Casos raros |
| Punto flojo | No versionable; el equipo no comparte la config | Requiere Docker corriendo | Pensado para desarrollo, no para clonar producción | Lo mantienes tú |

## Recomendación por caso

- **Sitio de cliente que hay que clonar y mantener** → **DDEV**. Es reproducible, entra en el repo, y
  `ddev import-db` con un dump grande simplemente funciona. Que todo el equipo levante el mismo entorno
  con un comando vale más que la GUI.
- **Desarrollo de un tema de bloques o de bloques propios** → **wp-env**. Es el oficial de WordPress,
  arranca limpio, y `.wp-env.json` deja declarados los plugins y temas de prueba.
- **El dev prefiere GUI, o hay que malabarear seis sitios de clientes a la vez** → **LocalWP**. Perfecto
  para eso; solo hay que asumir que la config no viaja en el repo, así que lo que importe se documenta
  en `docs/wordpress-setup.md`.
- **Docker propio** → solo si el proyecto ya lo tiene o si hay un requisito raro (una versión concreta
  de MySQL, un servicio extra). No se monta desde cero "porque es más flexible".

## Requisito común: WP-CLI

Los tres primeros lo traen. **Todo lo que el kit automatiza pasa por WP-CLI** — importar, exportar,
search-replace, inventariar, buscar en la DB. Un entorno sin WP-CLI convierte cada operación en clicks
manuales, así que se comprueba en el setup y, si no está, se resuelve ahí.

Cómo se invoca según el entorno:

```bash
wp {comando}                 # LocalWP (desde su shell del sitio) o WP-CLI global
ddev wp {comando}            # DDEV
npx wp-env run cli wp {cmd}  # wp-env
docker compose exec wordpress wp {cmd} --allow-root   # Docker propio
```

**Se escribe en `docs/wordpress-setup.md` cuál es el prefijo de este proyecto**, y a partir de ahí
todos los comandos del kit lo usan. No se asume `wp` pelado.

## Config mínima que deja `wp-setup`

**DDEV** — `.ddev/config.yaml`:
```yaml
name: {proyecto}
type: wordpress
docroot: ""
php_version: "{la de producción}"
webserver_type: nginx-fpm
database:
  type: mariadb
  version: "{la de producción}"
```

**wp-env** — `.wp-env.json`:
```json
{
  "core": null,
  "themes": ["./wp-content/themes/{child}"],
  "plugins": ["./wp-content/mu-plugins/{cliente}-core"],
  "config": { "WP_DEBUG": true, "SCRIPT_DEBUG": true }
}
```

**La versión de PHP y de MySQL se copian de producción**, no se usa la última. Un sitio que en local
corre PHP 8.3 y en producción 7.4 falla justo donde nadie mira.

## Debug — se enciende en local y se apaga fuera

```php
define( 'WP_DEBUG', true );
define( 'WP_DEBUG_LOG', true );    // wp-content/debug.log
define( 'WP_DEBUG_DISPLAY', false );  // que no se cuele en el HTML
define( 'SCRIPT_DEBUG', true );
```

Más **Query Monitor** como plugin de desarrollo: notices, queries lentas, hooks, qué plantilla se está
usando. Es la herramienta que más tiempo ahorra en WP y no cuesta nada instalarla en local.

`WP_DEBUG` en `true` en producción es una **fuga de información**, no un descuido menor. Se verifica en
`/eden:launch-check`.
