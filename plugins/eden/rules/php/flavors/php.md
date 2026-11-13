# Sabor: PHP sin framework

PHP con librerías sueltas o un micro-framework (un router, un contenedor, una librería de plantillas):
APIs pequeñas, servicios, sitios a medida, scripts. **Sin el framework, la seguridad que Laravel da por
defecto la escribe el proyecto**: por eso este sabor es más estricto con lo básico.

## Estructura habitual

```
public/index.php     ÚNICO punto de entrada expuesto por el servidor web
src/                 código de la aplicación (autoload PSR-4: "App\\": "src/")
templates/ · views/  plantillas
config/              configuración (lee variables de entorno; sin secretos en el repo)
tests/               Pest o PHPUnit
composer.json · composer.lock · .env.example · phpstan.neon · pint.json (preset per) o .php-cs-fixer.php
```

- **El servidor web apunta a `public/`**, nunca a la raíz del proyecto: `src/`, `vendor/`, `.env` y
  `config/` no deben ser accesibles por URL.
- **Manda la estructura real del proyecto.** Si ya tiene otra, se sigue y se señala lo que expone de más.

## Lo básico que aquí no viene gratis

| Qué | Cómo |
|---|---|
| **Base de datos** | PDO con `PDO::ERRMODE_EXCEPTION`, `PDO::ATTR_EMULATE_PREPARES => false` y **sentencias preparadas** siempre |
| **Salida HTML** | `htmlspecialchars($v, ENT_QUOTES \| ENT_SUBSTITUTE, 'UTF-8')` en cada salida, o el escape automático de la librería de plantillas (Twig, Plates…) |
| **CSRF** | Token por sesión en cada formulario que cambia estado, comprobado en el servidor con `hash_equals` |
| **Contraseñas** | `password_hash($p, PASSWORD_DEFAULT)` y `password_verify`; `password_needs_rehash` al iniciar sesión |
| **Sesión** | `session.cookie_httponly`, `session.cookie_secure`, `session.cookie_samesite=Lax` (o `Strict`), `session.use_strict_mode`, y `session_regenerate_id(true)` al iniciar sesión |
| **Entrada** | Validar y tipar todo lo que llega (`filter_var`, una librería de validación); rechazar por defecto |
| **Subidas** | Tipo real con `finfo`, tamaño máximo, nombre generado, guardadas **fuera de `public/`** |
| **Errores** | `display_errors=0` en producción; los errores al log, nunca a la respuesta |
| **Redirecciones** | Solo a rutas propias o a una lista blanca de dominios |

## Rutas y peticiones

- Un router (librería del proyecto, o un micro-framework como Slim) en vez de un `switch` creciendo en
  `index.php`. Antes de añadir uno, se pregunta: es una dependencia nueva.
- Métodos HTTP correctos: lo que cambia estado, nunca por `GET`.
- APIs: respuestas JSON con códigos de estado reales, errores sin detalles internos, y autenticación en
  cada endpoint que no sea público.

## Tests y calidad

- Pest o PHPUnit; tests de las rutas con peticiones simuladas y de la lógica pura en unitario.
- Pint con preset `per`, o PHP-CS-Fixer con `@PER-CS`; PHPStan con el nivel acordado.

## Validación propia de este sabor

```bash
composer validate && composer audit && vendor/bin/pest   # o vendor/bin/phpunit
vendor/bin/pint --test && vendor/bin/phpstan analyse
php -l {archivo}                                          # el mínimo indispensable
```
