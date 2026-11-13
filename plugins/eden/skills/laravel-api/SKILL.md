---
name: laravel-api
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:laravel-api`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:php` o
  `/eden:go` con su confirmación. NO lo actives porque haya que crear un endpoint: si no lo pidió por su
  nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: diseña e implementa UNO o varios
  endpoints de una API en Laravel con un contrato estable: rutas versionadas, autenticación (Sanctum u
  otra del proyecto), autorización con Policies, validación con Form Requests, salida con API Resources,
  paginación, errores consistentes, límite de frecuencia y tests de contrato y de seguridad, test
  primero. Un cambio de forma en una respuesta existente se trata como breaking change. No commitea.
argument-hint: "<recurso o endpoint, p.ej. 'GET/POST /v1/orders'> [| url-ticket] [| consumidores] [| notas]"
disable-model-invocation: true
---

## Laravel API — endpoints con contrato

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una API**: endpoints que consume un front (el equipo React, una app móvil)
u otro sistema. Reglas: `rules/php/eden-php-rules.md` y **`rules/php/flavors/laravel.md`** § Rutas,
controladores y validación. Equipo: `teams/php/roster.md`.

> **Idioma:** al dev, en español. Código, tests, docs y el contrato de la API, en inglés.

### Paso 0 — ¿Es Laravel con API?

`eden_stack.py detect` debe dar `php` · `laravel`. ¿Existe `routes/api.php` (es decir, se ejecutó
`php artisan install:api`) y qué autenticación usa la API (Sanctum, Passport u otra)? Si no hay API
montada, **instalarla es una decisión del dev** (añade un paquete y rutas): se propone, no se hace solo.

### Paso 1 — Entender el contrato

- **Quién la consume** (front propio, app móvil, terceros) y cómo se autentica.
- **Recursos y operaciones**: método, ruta, parámetros, cuerpo, respuesta y códigos de estado.
- **Quién puede** hacer cada operación (dueño del recurso, rol).
- Si ya hay endpoints, **su convención** (versión en la URL, forma de los errores, paginación,
  envoltura `data`, JSON:API si el proyecto la usa): se sigue.

### Paso 2 — Lo que ya existe (delegado)

`eden:php-architect` → rutas de la API (`route:list --path=api`), Resources, Policies, Form Requests,
middleware de autenticación y de límite de frecuencia, y **quién consume** los endpoints que se van a
tocar (`blast-radius`: front, app, integraciones).

### Paso 3 — El plan

```
🐘 API — {recurso}  ·  Laravel {v} · auth {Sanctum | …} · versión {v1}

| Método | Ruta | Request | Policy | Respuesta | Códigos |
|---|---|---|---|---|---|
| GET | /v1/{x} | {filtros, paginación} | viewAny | {X}Resource::collection (paginada) | 200 · 401 |
| POST | /v1/{x} | Store{X}Request | create | {X}Resource | 201 · 401 · 403 · 422 |

Errores: {forma única: message + errors por campo; sin detalles internos}
Límite de frecuencia: {RateLimiter: n/min por usuario o IP}
Cambios en endpoints existentes: {ninguno | ⚠️ breaking: qué cambia y quién lo consume}
🛡️ Superficie: entra {…} · validado {Form Request} · quién {Policy} · sale {Resource — campos} · secretos {…}
Tests (primero): contrato (forma JSON) + sin token · sin permiso · inválido · paginación · rate limit
Queda fuera: {…}

¿Le doy?
```

Un **breaking change** en un endpoint que alguien consume no se hace sin el sí explícito del dev: lo
habitual es una versión nueva de la ruta o un campo nuevo, no cambiar uno que ya existe. Espera el sí.

### Paso 4 — Test primero, luego los endpoints

1. `eden:php-tester`: tests de contrato (`assertJsonStructure` / `assertExactJson` con la forma
   acordada), de autenticación (sin token → 401), autorización (recurso ajeno → 403), validación (422 con
   el campo), paginación y límite de frecuencia → rojo.
2. `eden:php-data-dev`: modelo, consultas sin N+1 y los **API Resources** (solo los campos acordados).
3. `eden:php-dev`: rutas versionadas con su middleware (`auth:sanctum`, `throttle`), Form Requests,
   Policies y controladores, hasta verde.

### Paso 5 — Verificar y reportar

`eden:php-qa-reviewer` y `eden:security-auditor` (siempre en una API: es superficie pública).

```
🐘 API — {recurso} — LISTA

Endpoints: {método · ruta · Policy · Resource}
Contrato: {estable | versión nueva v{n}} · consumidores avisados: {quién — lo avisa el dev}
Seguridad: auth ✅ · Policy ✅ · validación ✅ · rate limit ✅ · Resource sin campos internos ✅ | {hallazgos}
Tests: {n ✅} · Pint ✅ · PHPStan ✅ · composer audit {…}
No verificado: {…}

➜ Si la consume el front React: /eden:react-data con este contrato.
```

No commitea ni pushea.
