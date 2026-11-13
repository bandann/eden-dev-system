# Dispatch — cómo reparte el líder Node

## 1. Partir en unidades

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Un campo validado más, un filtro en un listado | Un especialista (+ su test) |
| **M** | Un endpoint con su validación y autorización, un job | tester → data-dev → node-dev |
| **L** | Un recurso completo (CRUD) o un módulo de Nest con varios endpoints | Varias unidades M con dependencias |
| **XL** | Una API o un servicio entero | Lotes L por recurso o módulo |

Una unidad que cruza dueños **se parte**: test (tester) → esquema y repositorio (data-dev) → ruta,
DTO, validación y auth (node-dev).

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa | `eden:node-architect` |
| Rutas, controladores, módulos de Nest, middleware, guards, pipes, DTOs y validación, servicios | `eden:node-dev` |
| Esquema, migraciones, seeds, repositorios, jobs, eventos, clientes externos | `eden:node-data-dev` |
| Tests (primero) | `eden:node-tester` |
| Entorno, scripts, TypeScript, ESLint, config, Docker, CI | `eden:node-devops` |
| Revisar el diff; calidad | `eden:node-qa-reviewer` |
| Seguridad independiente | `eden:security-auditor` |

El punto de entrada (`main.ts`, `server.ts`, `app.ts`) y `AppModule`: el líder decide el dueño y lo
escribe en el plan.

## 3. Plantilla del plan (al dev, en español)

```
🟩 PLAN DEL EQUIPO NODE

Trabajo: {new | onboard | task} · {ticket / descripción} · sabor {node | express | nest}
Rama: {nombre} desde {base — preguntada}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | Tests de {x} | S | eden:node-tester | test/x.e2e-spec.ts | — | — |
| 2 | Esquema y repositorio | S | eden:node-data-dev | prisma/schema.prisma, src/x/x.repository.ts | 3 — {por qué} | 1 |
| 3 | Endpoint | M | eden:node-dev | src/x/x.controller.ts, src/x/dto/*.ts | 4 | 1, 2 |

Contrato: {método · ruta · entrada · salida · códigos} — breaking: {no | ⚠️ …}
Esquema: {tablas/colecciones · índices · ¿datos que mover?}
🛡️ Superficie: entra {…} · validado {Zod/DTO} · quién {guard/middleware + recurso} · sale {DTO} · secretos {…} · terceros {URLs salientes}
Verificación: reviewer + security-auditor al final
Paro a preguntarte en: {dependencias, esquema con datos, punto de entrada, .env}
Blast radius: {consumidores — de architect}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: flavor {node | express | nest} (rules/node/flavors/{x}.md) · Node {v} · ESM|CJS · ORM {x v} ·
      reuse step {n}: {why} · sibling pattern: {file} · consumers: {from architect} · tests to make green: {files}
ACCEPT WHEN: {tests green; lint + typecheck + build clean; migration reviewed and applied only on the test DB}
DO NOT: touch other files; add/remove/upgrade dependencies; migrate/seed outside the local/test DB; deploy;
        put secrets in code or .env.example; disable lint rules or tests; {unit-specific}
HANDOFF: teams/node/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

Solo unidades con **archivos disjuntos**, en un solo turno, como mucho 4 a la vez. Dos unidades que
tocan el esquema van en secuencia (las migraciones chocan en el orden).
