# Roster PHP — el equipo

Líder: **`/eden:php`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`) `eden:php-*`.
Reglas del stack: `rules/php/eden-php-rules.md` y el sabor del proyecto (`rules/php/flavors/php.md` o
`rules/php/flavors/laravel.md`). Contrato común: `rules/eden-team-rules.md`.

> **WordPress no es este stack.** Un proyecto WordPress es PHP, pero tiene su propio módulo y su propio
> equipo (`rules/wordpress/`, `teams/wordpress/roster.md`). La detección ya lo separa
> (`eden-stack-rules.md`).

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:php-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe: quién usa el modelo, la clase, la ruta o el job |
| `architect` | `eden:php-architect` (modo `audit` / `decide`) | Onboarding de un proyecto avanzado; decidir el escalón reuse-first y dónde vive cada cosa |
| `design-extractor` | `eden:figma-extractor` | Trabajo visual con Figma (vistas Blade, Livewire o el front de Inertia) |
| `design-system` | `eden:php-dev` | Tokens en el CSS del proyecto (Tailwind theme, CSS variables) con `create-fundaments` |
| `implementer` | `eden:php-dev` / `eden:php-data-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:php-data-dev` | Modelos, migraciones, factories y seeders, relaciones, colas y jobs, API Resources, integraciones |
| `tester` | `eden:php-tester` | Tests primero: Pest o PHPUnit, feature y unitarios, con factories |
| `devops` | `eden:php-devops` | Setup, versión de PHP, Composer, `.env.example`, entorno local (Herd, Sail, Docker), Pint, PHPStan, CI |
| `migrator` | `eden:php-data-dev` (modo `migrate`) | Migraciones de esquema y de datos, con backup y `--pretend` primero |
| `design-auditor` | `eden:design-auditor` | Loop medir → corregir → medir contra Figma |
| `reviewer` | `eden:php-qa-reviewer` | Revisión del diff + Pint, PHPStan y tests en verde |
| `quality-auditor` | `eden:php-qa-reviewer` (modo `quality`) | Rendimiento (N+1, índices, caché), accesibilidad y SEO de las vistas |
| `security-auditor` | `eden:security-auditor` | Mass assignment, escape en Blade, SQL crudo, autorización, CSRF, subidas; lee el módulo PHP |

## Propiedad de archivos (quién escribe qué)

Las rutas son las de Laravel; en PHP sin framework, **manda la estructura real del proyecto** y el
`php-architect` la confirma en el inventario.

| Archivos | Dueño |
|---|---|
| Rutas (`routes/web.php`, `routes/api.php`), controladores, Form Requests, Policies, middleware propio, servicios y acciones de la aplicación | `eden:php-dev` |
| Vistas: Blade (`resources/views/`), componentes Livewire, CSS y JS de las vistas (`resources/css`, `resources/js` sin framework de front) | `eden:php-dev` |
| Front de **Inertia con React** (`resources/js/Pages`, componentes React) | `eden:react-ui-dev` — el roster React manda sobre esos archivos; el líder coordina |
| Modelos, migraciones, factories, seeders, casts, scopes, observers | `eden:php-data-dev` |
| Jobs, eventos y listeners, notificaciones, API Resources, clientes de APIs externas, comandos y programación (`routes/console.php`) | `eden:php-data-dev` |
| Tests: `tests/Feature`, `tests/Unit`, `tests/Browser`, `Pest.php`, `phpunit.xml`, datos de prueba | `eden:php-tester` |
| `composer.json`, `composer.lock`, `package.json` de tooling, `config/*.php` del proyecto, `bootstrap/app.php`, `.env.example`, `pint.json`, `phpstan.neon*`, `rector.php`, `docker-compose.yml`, `.github/` | `eden:php-devops` |
| `bootstrap/app.php` (middleware, excepciones, enrutado) y `config/auth.php` | **Líder decide** — afecta a toda la app. Se asigna con encargo explícito |
| `.env` con valores reales | **Nadie** — los secretos los pone el dev; el kit solo mantiene `.env.example` sin valores |

Si una unidad cruza dueños, el líder la parte en unidades secuenciales (tester → data-dev → php-dev).
Nunca dos agentes sobre el mismo archivo en paralelo.

## Prohibiciones — no negociables

Ningún agente ni el líder las rompe, aunque el encargo lo pida:

| Nunca | Por qué |
|---|---|
| Desplegar (Forge, Vapor, Cloud, Envoyer, SSH a un servidor, push a la rama que despliega) | El deploy lo hace el dev |
| `migrate` contra una base que no sea local o de pruebas; `migrate:fresh`, `migrate:reset`, `db:wipe` o `db:seed` sobre datos que el dev no declaró desechables | Borra datos |
| Ejecutar SQL de escritura a mano en una base real | Es la base del cliente |
| Agregar, quitar o actualizar un paquete de Composer o npm sin el sí del dev | Es código de terceros en el proyecto del cliente |
| Escribir secretos en el código, en `config/` o en `.env.example`; dejar `APP_DEBUG=true` fuera de local | Se filtran |
| Desactivar una regla de PHPStan, un test o el CSRF para que algo pase | Se arregla la causa |
| Cambiar la versión mayor de PHP o de Laravel como parte de otra tarea | Una migración de versión es una tarea propia |

Sin riesgo y sin autorización: `composer install` con el lockfile tal cual, `php artisan test`,
`pint --test`, `phpstan analyse`, `route:list`, `migrate` y `migrate:fresh` **en la base local o de
tests** declarada desechable, `serve`.

## Formato de handoff (todos los especialistas)

```
🐘 {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {tests, Pint, PHPStan, migración en local… con el resultado real}
No verificado: {qué y por qué}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

| Fase | Especialistas |
|---|---|
| 1. Discovery | architect, design-extractor (si hay vistas con diseño) |
| 2. Setup | devops (`/eden:php-setup`) |
| 3. Modelo de datos | data-dev (migraciones y modelos), con su plan aprobado |
| 4. Build | tester (primero) → data-dev → php-dev, con design-auditor en loop en las vistas |
| 5. QA | reviewer, quality-auditor, security-auditor |
| 6. Entrega | `turnoff-task`. El deploy lo hace el dev |
