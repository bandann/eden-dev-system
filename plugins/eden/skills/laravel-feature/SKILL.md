---
name: laravel-feature
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:laravel-feature`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:php` o
  `/eden:go` con su confirmación. NO lo actives porque el proyecto sea Laravel o haya que crear un
  modelo: si no lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca:
  construye UNA funcionalidad de Laravel de punta a punta, reuse-first y test primero: el esquema
  (migración reversible con índices), el modelo con su mass assignment y casts, factories, el Form
  Request, la Policy, las rutas, el controlador o la acción, las vistas (Blade o Livewire) y, si hace
  falta, jobs y eventos, con la autorización, la validación y el N+1 resueltos. Nunca migra fuera de la
  base local o de tests. No commitea.
argument-hint: "<funcionalidad, p.ej. 'pedidos de un cliente'> [| url-ticket | url-figma] [| qué NO tocar]"
disable-model-invocation: true
---

## Laravel Feature — una funcionalidad completa

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una funcionalidad** de una app Laravel: un recurso con su CRUD, un flujo con
su formulario, una pantalla con sus datos. Reglas: `rules/php/eden-php-rules.md` y
**`rules/php/flavors/laravel.md`**. Equipo: `teams/php/roster.md`. Si la funcionalidad es solo una API
(sin vistas), el skill es `/eden:laravel-api`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 0 — ¿Es Laravel?

`eden_stack.py detect` debe dar `php` · `laravel`. Se anotan las versiones de Laravel y PHP instaladas
(las APIs se comprueban con context7 para esa versión) y qué capa de vistas usa (Blade, Livewire o
Inertia). Si el front es Inertia con React, esa parte la hace el equipo React.

### Paso 1 — Entender el pedido

Qué datos (entidades, relaciones, quién es dueño de qué), qué acciones (crear, ver, editar, borrar,
otras), **quién puede hacer cada una**, qué vistas y qué efectos secundarios (correos, notificaciones,
colas). Del ticket y del Figma si los hay. Lo que cambia el resultado se pregunta una vez.

### Paso 2 — Lo que ya existe (delegado)

- `eden:php-architect` → `inventory` de los modelos, tablas, Policies, rutas y vistas relacionados, y
  `blast-radius` de lo que se va a tocar. Qué del framework o de un paquete ya instalado lo resuelve.
- `eden:figma-extractor` si hay vistas con diseño (caché de diseño primero).

### Paso 3 — El plan

```
🐘 FUNCIONALIDAD — {nombre}  ·  Laravel {v} · PHP {v} · vistas {Blade | Livewire | Inertia}

Escalón: {n} — {por qué no alcanza el anterior}
Esquema: {tablas · columnas · tipos · índices · claves foráneas} — migración reversible · ¿datos existentes?
Modelo: {$fillable · casts · relaciones · scopes}
Acciones: {ruta (nombre) → controlador/acción → Form Request → Policy::método}
Vistas: {archivos · componentes existentes que se reutilizan}
Efectos: {jobs · eventos · notificaciones}
🛡️ Superficie: entra {campos} · validado {Form Request} · quién {Policy: dueño/rol} · sale {vista/Resource} · terceros {…}
Rendimiento: {with() en listados · paginación · índices}
Tests (primero): feature por acción + sin sesión · sin permiso · inválido · mass assignment
Queda fuera: {…}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego la funcionalidad

1. `eden:php-tester`: feature tests de cada acción, con los casos de seguridad (401/redirect, 403 sobre
   un recurso ajeno, 422 con el campo, campo protegido que no cambia) y los fakes de lo externo → rojo.
2. `eden:php-data-dev`: migración (sube y baja en la base de tests), modelo, factory, jobs y eventos.
3. `eden:php-dev`: Form Request, Policy, rutas con nombre y middleware, controlador o acción, vistas con
   los tokens del proyecto, hasta verde.
4. Vistas con Figma: `eden:design-auditor` en loop hasta 1:1.

### Paso 5 — Verificar y reportar

`eden:php-qa-reviewer` (tests, Pint, PHPStan, `composer audit`, N+1) y `eden:security-auditor` sobre las
rutas que escriben.

```
🐘 FUNCIONALIDAD — {nombre} — LISTA

Archivos: {…}
Esquema: {migraciones} — sube ✅ · baja ✅ (base de tests)
Seguridad: Policy en cada acción ✅ · Form Request ✅ · mass assignment ✅ | {hallazgos}
Tests: {n ✅} · Pint ✅ · PHPStan ✅ · composer audit {…}
Pendiente del dev: migrar en cada entorno · {colas, .env}
No verificado: {…}
```

No commitea ni pushea.
