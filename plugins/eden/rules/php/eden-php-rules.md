# Módulo PHP — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-code-style`,
`eden-quality`, `eden-testing`, `eden-security`). Aquí solo va lo que es propio de PHP. Lo de cada sabor
vive en `flavors/`:

| Sabor | Archivo | Qué es |
|---|---|---|
| **PHP** | `flavors/php.md` | PHP sin framework o con librerías sueltas (un router, un micro-framework): APIs, servicios, scripts, sitios a medida |
| **Laravel** | `flavors/laravel.md` | Aplicaciones Laravel: Eloquent, Form Requests, Policies, colas, Blade, Livewire o Inertia |

**WordPress no es este stack**: tiene su módulo propio (`rules/wordpress/`). El sabor se declara en
`.claude/project-config.json` → `php.flavor` (lo escribe `/eden:php-setup`) o lo detecta
`scripts/eden_stack.py detect`. Si no está claro, se pregunta antes de escribir código.

> **La realidad del proyecto manda.** Si el proyecto organiza el código de otra forma coherente
> (Actions, Services, módulos), se sigue el proyecto.

---

## Versiones — se verifican, no se recuerdan

PHP y Laravel publican una versión mayor al año y retiran soporte con fechas fijas. **Antes de usar una
API que no sea trivial, se comprueba con context7 contra la versión instalada** (`composer.json`,
`composer.lock`, `php -v`).

Referencia **verificada el 2026-10-22** (es un punto de partida, no una verdad):

| Herramienta | Versión | Lo que más importa |
|---|---|---|
| PHP | 8.5 (8.4 con soporte activo hasta fin de 2026) | 8.2 solo recibe seguridad hasta el 31-12-2026: **no es objetivo para un proyecto nuevo**. 8.5 trae el operador `\|>` y `#[\NoDiscard]`; 8.4, property hooks y visibilidad asimétrica |
| Laravel | 13 (marzo 2026) | Requiere PHP 8.3–8.5; seguridad hasta marzo 2028. Laravel 11 ya no tiene soporte; 12, solo seguridad hasta febrero 2027 |
| Pest | 5 (PHP ≥ 8.4) · 4 (PHP 8.3) | Pest 4+ trae browser testing sobre Playwright |
| PHPUnit | 13 (PHP ≥ 8.4) · 12 (PHP 8.3) | |
| PHPStan | 2 (niveles 0–10) · Larastan 3 | Nivel 10 = `mixed` implícito; `--level max` es siempre el más alto |
| Pint | preinstalado en Laravel | Preset `laravel`; `per` para PHP sin framework |
| Estilo | **PER Coding Style 3.1** | Reemplaza a PSR-12 |

Un proyecto en una versión **sin soporte de seguridad** (PHP o Laravel) se reporta en el onboarding con
su fecha de fin de soporte. Actualizar es una tarea propia y la decide el dev.

---

## Cómo se escribe PHP

- **`declare(strict_types=1);`** en todo archivo nuevo si el proyecto lo usa (en PHP sin framework,
  siempre).
- **Tipos en todo**: parámetros, retornos y propiedades. `?Tipo` explícito para lo anulable (el nulable
  implícito `Tipo $x = null` está deprecado). Nada de propiedades dinámicas.
- **Clases pequeñas con una responsabilidad**, `final` por defecto si el proyecto lo hace, `readonly`
  para objetos de valor y DTOs, enums nativos en vez de constantes sueltas.
- **Estilo PER-CS** (o el del proyecto) aplicado por la herramienta (Pint o PHP-CS-Fixer), no a mano.
- **Autoload PSR-4** con Composer; nada de `require` de clases a mano.
- **Errores**: excepciones con significado, capturadas donde se pueden manejar. Nunca `@` para silenciar
  ni `catch` vacío.
- **Nada de debug en el diff**: `dd()`, `dump()`, `var_dump`, `print_r`, `ray()`, `die`.

## Reuse-first en PHP

1. **Lo que ya hace el lenguaje, el framework o un paquete instalado**, tal cual (validación, colas,
   paginación, autorización, notificaciones…).
2. **Configuración** (un archivo de `config/`, una opción del paquete).
3. **Extender sin cambiar lo que ya existe**: un parámetro opcional con el comportamiento actual por
   defecto, un evento, un listener, un macro, un decorador. Antes, blast radius (`eden:php-architect`).
4. **Código mínimo acotado** a la unidad.
5. **Clase o módulo nuevo**: último recurso, con su nombre y su lugar en la estructura del proyecto.

Un paquete nuevo es código de terceros: se propone con su porqué (mantenimiento, descargas, avisos de
seguridad) y lo decide el dev.

## Datos y base de datos

- **Consultas preparadas siempre.** Ninguna variable concatenada en SQL, en ningún sabor.
- **Migraciones versionadas y reversibles**: el esquema vive en el repo, no en un cliente de base de
  datos. Una migración ya ejecutada en otro entorno no se edita: se escribe otra.
- **Índices** en claves foráneas y en lo que se filtra u ordena. Paginación en listados.
- **Nada de N+1**: las relaciones de lo que se lista se cargan de una vez.
- **Los datos de clientes no se tocan fuera de local o tests** (roster § Prohibiciones).

## Tests

Siguen `eden-testing-rules.md`: **el test se escribe antes** y debe fallar primero. Los escribe el rol
`tester` (`eden:php-tester`).

- El framework del proyecto (Pest o PHPUnit). Feature tests para el comportamiento de punta a punta y
  unitarios para la lógica pura.
- **Base de tests desechable** (SQLite en memoria o una base `_testing`). Si los tests apuntan a una base
  real, se para.
- **Los casos de seguridad tienen test**: sin sesión, sin permiso (recurso de otro), entrada inválida y
  campo protegido en mass assignment.
- La puerta de `turnoff-task`: tests, Pint (o el formateador), PHPStan sin errores nuevos y
  `composer audit` limpio.

## Entorno y calidad del código

- **Versión de PHP fijada** (`require.php` en `composer.json`, y `config.platform.php` si hace falta) y
  `composer.lock` versionado en aplicaciones.
- **Composer al día** en seguridad (en 2025 se corrigió una inyección de secuencias ANSI, CVE-2025-67746).
- **Análisis estático** con PHPStan (Larastan en Laravel). En un proyecto existente se empieza en un
  nivel alcanzable con baseline y se sube; no se baja el nivel para que algo pase.
- **Scripts de Composer** que el kit usa: `test`, `lint` (formateador en modo comprobación) y `analyse`.
  Si falta uno, se propone; no se inventa su resultado.

## Seguridad

Aplica `eden-security-rules.md` (principios, checklist y severidad). Lo propio de PHP:

| Severidad | En PHP |
|---|---|
| **Crítica** | SQL con variables concatenadas; un secreto en el código o en el repo; una acción que escribe sin comprobar quién pide; subida de archivos que permite ejecutar PHP; `unserialize()` de datos del usuario; `eval`/`system`/`exec` con entrada; una versión con RCE conocida y parche disponible |
| **Alta** | Salida sin escapar (XSS); IDOR (un id ajeno da acceso); mass assignment sobre campos sensibles; CSRF ausente en una acción que cambia estado; open redirect; modo debug en producción |
| **Media** | Validación débil de archivos; falta de límite de frecuencia en login o formularios; dependencia con aviso alto sin parche; datos personales en logs |
| **Baja** | Cabeceras de seguridad ausentes; mensajes de error demasiado detallados |

- **Escapar en la salida, según el contexto** (HTML, atributo, URL, JS). En Blade, `{{ }}`.
- **Contraseñas** con `password_hash` / el Hash del framework; nunca MD5, SHA-1 ni cifrado reversible.
- **Sesiones y cookies** `HttpOnly`, `Secure`, `SameSite`, con el id regenerado al iniciar sesión.
- **`composer audit`** en cada `turnoff-task` y en `security-check deps`.

## Blast radius en PHP

```bash
grep -rn "{Clase}\|{método}\|{tabla}\|{ruta}" --include="*.php" .
```

Excluyendo `vendor/`. Más los usos indirectos que el texto no ve: contenedor de dependencias, eventos y
listeners, observers, jobs, rutas con nombre y vistas. `graphify affected` sí entiende `.php` y se suma
al grep. **Un cambio de esquema afecta datos reales**: se declara qué tablas y cuántos registros.

## Documentación vigente

- PHP: https://www.php.net/manual · versiones con soporte: https://www.php.net/supported-versions.php
- Laravel: https://laravel.com/docs · notas de versión: https://laravel.com/docs/releases
- Pest: https://pestphp.com · PHPUnit: https://phpunit.de · PHPStan: https://phpstan.org · Larastan: https://github.com/larastan/larastan
- Pint: https://laravel.com/docs/pint · PER Coding Style: https://www.php-fig.org/per/coding-style/
- Avisos de seguridad: `composer audit` y https://github.com/advisories (ecosistema Composer)
