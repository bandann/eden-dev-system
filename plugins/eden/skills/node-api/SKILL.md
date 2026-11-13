---
name: node-api
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:node-api`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:node` o `/eden:go`
  con su confirmación. NO lo actives porque haya que crear un endpoint: si no lo pidió por su nombre, se
  trabaja de forma normal. — Qué hace cuando SÍ se invoca: diseña e implementa UNO o varios endpoints de
  un back-end Node (una ruta de Express o un módulo de NestJS) con un contrato estable: validación de
  toda la entrada (Zod o DTOs), autenticación y autorización por recurso, salida con DTOs, errores
  consistentes, paginación, límite de frecuencia y tests de contrato y de seguridad, test primero. Un
  cambio de forma en un endpoint existente es un breaking change. No commitea.
argument-hint: "<recurso o endpoint, p.ej. 'GET/POST /v1/orders'> [| url-ticket] [| consumidores] [| notas]"
disable-model-invocation: true
---

## Node API — endpoints con contrato

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una API** en un back-end Node: endpoints que consume un front (el equipo
React), una app móvil u otro sistema. Reglas: `rules/node/eden-node-rules.md` y el sabor
(`flavors/express.md`, `flavors/nest.md` o `flavors/node.md`). Equipo: `teams/node/roster.md`.

> **Idioma:** al dev, en español. Código, tests, docs y el contrato de la API, en inglés.

### Paso 0 — ¿Es el stack Node?

`eden_stack.py detect` debe dar `node` (sabor `express`, `nest` o `node`). Un route handler de Next.js
es `/eden:next-route`; uno de Laravel, `/eden:laravel-api`. Se anota la versión del framework: Express 5
y NestJS cambiaron APIs (rutas comodín, manejo de errores asíncronos), y se comprueban con context7.

### Paso 1 — Entender el contrato

- **Quién la consume** y cómo se autentica (JWT, sesión, API key).
- **Recursos y operaciones**: método, ruta, parámetros, cuerpo, respuesta y códigos de estado.
- **Quién puede** hacer cada operación (dueño del recurso, rol).
- Si ya hay endpoints, **su convención** (versión en la URL, forma de errores, paginación, envoltura de
  la respuesta): se sigue.

### Paso 2 — Lo que ya existe (delegado)

`eden:node-architect` → rutas o módulos existentes, cómo se valida y se autoriza, el formato de errores,
y **quién consume** los endpoints que se van a tocar (`blast-radius`).

### Paso 3 — El plan

```
🟩 API — {recurso}  ·  {express | nest | node} {v} · auth {JWT | sesión | …} · versión {v1}

| Método | Ruta | Entrada (esquema/DTO) | Quién puede | Salida (DTO) | Códigos |
|---|---|---|---|---|---|
| GET | /v1/{x} | query: paginación, filtros | autenticado · solo los suyos | {X}[] paginado | 200 · 401 |
| POST | /v1/{x} | body: Create{X} | autenticado | {X} | 201 · 400/422 · 401 · 403 |

Validación: {Zod | DTO + ValidationPipe whitelist} · campos no declarados: rechazados
Errores: {forma única, sin pila ni mensajes internos}
Límite de frecuencia: {n/min por usuario o IP}
Cambios en endpoints existentes: {ninguno | ⚠️ breaking: qué cambia y quién lo consume}
🛡️ Superficie: entra {…} · quién {…} · sale {DTO — campos} · secretos {…} · terceros/URLs salientes {…}
Tests (primero): contrato + sin token · sin permiso · inválido · campos extra · paginación · rate limit
Queda fuera: {…}

¿Le doy?
```

Un **breaking change** en un endpoint que alguien consume no se hace sin el sí explícito del dev: lo
habitual es una versión nueva o un campo nuevo. Espera el sí.

### Paso 4 — Test primero, luego los endpoints

1. `eden:node-tester`: tests de integración con supertest (forma del contrato, 401, 403 sobre un recurso
   ajeno, 400/422 con el campo, campos extra rechazados, la respuesta no filtra campos internos,
   paginación, límite de frecuencia) → rojo.
2. `eden:node-data-dev`: esquema y repositorio si hacen falta, consultas sin N+1.
3. `eden:node-dev`: ruta o módulo, esquema de validación o DTOs, guard o middleware de auth, servicio y
   DTO de salida, hasta verde.

### Paso 5 — Verificar y reportar

`eden:node-qa-reviewer` y `eden:security-auditor` (siempre en una API: es superficie pública).

```
🟩 API — {recurso} — LISTA

Endpoints: {método · ruta · auth · DTO}
Contrato: {estable | versión nueva v{n}} · consumidores: {quién — lo avisa el dev}
Seguridad: validación ✅ · auth + recurso ✅ · rate limit ✅ · salida sin campos internos ✅ | {hallazgos}
Tests: {n ✅} · lint ✅ · typecheck ✅ · build ✅ · npm audit {…}
No verificado: {…}

➜ Si la consume el front React: /eden:react-data con este contrato.
```

No commitea ni pushea.
