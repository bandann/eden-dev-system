---
name: node-data
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:node-data`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:node` o
  `/eden:go` con su confirmación. NO lo actives porque haya una tabla, un ORM o una cola: si no lo pidió
  por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: diseña e implementa la capa
  de datos de un back-end Node: el esquema y su migración con el ORM del proyecto (Prisma, Drizzle,
  TypeORM, Mongoose) revisando el SQL generado, índices y restricciones, repositorios o acceso a datos
  sin N+1, transacciones, y jobs o workers idempotentes con sus reintentos. Test primero. Nunca migra ni
  borra datos fuera de la base local o de tests. No commitea.
argument-hint: "<entidad, cambio de esquema o job> [| url-ticket] [| datos existentes] [| notas]"
disable-model-invocation: true
---

## Node Data — esquema, acceso a datos y colas

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **la capa de datos**: una entidad nueva, un cambio de esquema, un repositorio,
un job o un worker. Reglas: `rules/node/eden-node-rules.md` § Datos y el sabor. Equipo:
`teams/node/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué entidades y relaciones, qué consultas va a necesitar la aplicación (para los índices), **si hay
datos existentes** que el cambio afecta, y qué trabajo debe ir a una cola. Lo que cambia el resultado se
pregunta una vez.

### Paso 2 — Lo que ya existe (delegado)

`eden:node-architect` → ORM y versión, cómo se versionan las migraciones (o si se usa `push` sin
historial: dilo), el esquema relacionado, los repositorios y quién los usa (`blast-radius`), y el sistema
de colas si hay.

### Paso 3 — El plan

```
🟩 DATOS — {entidad o cambio}  ·  ORM {x v} · base {x}

Esquema: {tablas/colecciones · campos · tipos · relaciones · índices · únicos}
Datos existentes: {ninguno | n registros afectados — plan: default · backfill · en pasos}
Migración: {generada por el ORM · SQL revisado · reversible: sí | no — por qué}
Acceso a datos: {repositorio / funciones · consultas · paginación · transacciones}
Colas: {job · idempotencia · reintentos/backoff · qué pasa si falla}
🛡️ Superficie: {consultas parametrizadas · entrada que llega a filtros · datos sensibles: cifrados/no en logs}
Tests (primero): {repositorio contra la base de tests · job con sus fallos}
Pendiente del dev: migrar en cada entorno · {workers}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego los datos

1. `eden:node-tester`: tests del repositorio contra la base de tests (crear, leer, filtrar, paginar,
   restricciones que fallan) y del job (éxito, fallo, reintento, idempotencia) → rojo.
2. `eden:node-data-dev`: esquema, migración generada y revisada (aplicada y revertida o regenerada **en la
   base de tests**), repositorio y job, hasta verde.
3. Si hay endpoints que lo usan: `/eden:node-api` o `eden:node-dev` con el contrato del repositorio.

### Paso 5 — Verificar y reportar

`eden:node-qa-reviewer` (N+1, índices, migraciones) y `eden:security-auditor` si hay datos personales o
consultas con entrada del usuario.

```
🟩 DATOS — {entidad o cambio} — LISTO

Esquema: {…} · Migración: {archivo} — revisada ✅ · aplicada solo en local/tests ✅
Acceso: {repositorio} · Colas: {job}
Tests: {n ✅} · lint ✅ · typecheck ✅ · build ✅
Pendiente del dev: migrar en cada entorno · {workers, variables}
No verificado: {…}
```

No commitea ni pushea.
