# Sabor: Laravel

Aplicaciones Laravel. El framework trae casi todo lo que la seguridad y el orden piden (validación,
autorización, CSRF, colas, migraciones); **el trabajo es usarlo bien, no reescribirlo**. Las APIs
cambian con cada versión mayor anual: **se comprueban con context7 contra la versión instalada**. Lo de
abajo está verificado para Laravel 13 (2026-10-22).

## Estructura

```
app/Http/Controllers · app/Http/Requests · app/Models · app/Policies · app/Jobs · app/Actions|Services
bootstrap/app.php        middleware, manejo de excepciones y registro de rutas (sin Http/Kernel)
routes/web.php           sesión, CSRF y cookies cifradas
routes/api.php           solo si el proyecto ejecutó `php artisan install:api` (Sanctum)
routes/console.php       comandos y tareas programadas
config/*.php             la única capa que lee env()
database/migrations · factories · seeders
resources/views (Blade) · resources/js (Inertia o JS) · resources/css
tests/Feature · tests/Unit · tests/Browser
```

Los directorios de `app/` aparecen al usarlos (`make:*`). Si el proyecto organiza por módulos o
dominios, se sigue.

## Proyecto nuevo

- `laravel new {app}` (instalador de Laravel, también incluido en Herd) con el **starter kit** que
  elija el dev: React, Vue o Svelte (con Inertia), o Livewire. Los starter kits traen la autenticación
  (Fortify) y **pasan a ser código del proyecto**: no se actualizan solos.
- SQLite es la base por defecto; `composer run dev` levanta servidor, cola y Vite a la vez.
- **Laravel Boost** (opcional, `composer require laravel/boost --dev`) da a los agentes un MCP con el
  esquema, los logs y la documentación de la versión instalada. Si el proyecto lo tiene, sus reglas
  (`.ai/rules/`) se respetan como convenciones del proyecto.

## Rutas, controladores y validación

- **Rutas con nombre** y agrupadas por middleware; `php artisan route:list` para ver lo que hay.
- **Controladores finos**: validan (Form Request), autorizan (Policy), delegan (Action/Service o el
  modelo) y responden.
- **Form Requests** para validar; en el controlador se usa `$request->validated()`, nunca `all()`.
- **Autorización con Policies y Gates** en cada acción (`$this->authorize`, `Gate::authorize`,
  `can` en rutas, o el atributo `#[Authorize]` en Laravel 13). El middleware `auth` no basta: dice quién
  es, no si puede.
- **API:** Sanctum para SPA y tokens (Passport solo si hace falta OAuth2 completo), **API Resources**
  para la salida (nunca el modelo entero) y límite de frecuencia (`RateLimiter::for`).

## Eloquent y datos

- `$fillable` explícito en los modelos con campos sensibles; `casts()` para fechas, enums, JSON y
  `encrypted`.
- Relaciones con `with()` en lo que se lista; `withCount`; `paginate`/`cursorPaginate`.
- Migraciones con `down()` real, índices en claves foráneas, y para cambiar columnas con datos, un plan
  de datos.
- `DB::raw`, `whereRaw`, `orderByRaw` **solo con bindings**.
- Factories para tests y seeders; nunca datos reales de clientes.

## Colas, eventos y tareas

- Lo lento (correo, APIs externas, procesar archivos) va a un **job**: idempotente, con `tries`,
  `backoff`, `timeout` y `failed()` pensados (en Laravel 13 también por atributos: `#[Tries]`,
  `#[Backoff]`, `#[Timeout]`).
- Tareas programadas en `routes/console.php`. Horizon si el proyecto usa Redis y ya lo tiene.

## Vistas

- **Blade:** `{{ }}` escapa; `{!! !!}` no, y solo se usa con HTML ya saneado. `@csrf` en formularios
  (el middleware de CSRF en Laravel 13 se llama `PreventRequestForgery` y además verifica el origen).
  Componentes de Blade existentes antes que markup nuevo.
- **Livewire:** propiedades públicas = datos que el usuario puede manipular; se validan y autorizan en
  cada acción, y las que no deben cambiar se bloquean (`#[Locked]`). **Livewire 3 por debajo de 3.6.4
  tiene una RCE sin autenticación explotada activamente (CVE-2025-54068)**: un proyecto así se reporta
  como Crítica.
- **Inertia con React:** el front sigue el módulo React (`rules/react/`) y lo escribe el equipo React
  (roster PHP § Propiedad).
- Tokens del proyecto (Tailwind theme o CSS variables) y accesibilidad como en cualquier stack.

## Configuración y entorno

- `env()` **solo dentro de `config/`**; en el código, `config('…')`. Con `config:cache`, un `env()`
  fuera de `config/` devuelve `null`.
- `APP_DEBUG=false` y `APP_ENV=production` en producción; `APP_KEY` nunca en el repo.
- Entorno local: Herd, Sail (Docker) o PHP del sistema, lo que use el proyecto.

## Seguridad — avisos recientes que hay que conocer

Además de Livewire (arriba), hay avisos en el propio framework y en paquetes oficiales: por ejemplo, una
inyección CRLF en la regla de validación `email` (CVE-2026-48019, corregida en 12.60.0 y 13.10.0) y una
RCE por deserialización en Laravel Reverb (CVE-2026-23524, corregida en 1.7.0). **Regla:** `composer
audit` en el onboarding, en `security-check deps` y en cada `turnoff-task`; una versión afectada con
parche disponible se reporta con su severidad, y actualizar lo decide el dev. Las cifras exactas se
confirman en el aviso (GitHub Advisories) antes de citarlas en un PR.

## Tests

- `php artisan test` (Pest o PHPUnit). `RefreshDatabase` en feature tests contra la base de tests.
- Fakes del framework para lo externo: `Queue::fake()`, `Mail::fake()`, `Notification::fake()`,
  `Event::fake()`, `Http::fake()`, `Storage::fake()`.
- Navegador: Pest 4+ con su plugin de browser testing (sobre Playwright). Dusk sigue existiendo, pero
  Laravel recomienda Pest para proyectos nuevos.

## Validación propia de este sabor

```bash
php artisan test && vendor/bin/pint --test && vendor/bin/phpstan analyse && composer audit
php artisan migrate --pretend          # la migración nueva, antes de correrla en la base local
php artisan route:list --except-vendor # las rutas nuevas, con su middleware
```
