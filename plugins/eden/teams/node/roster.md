# Roster Node — el equipo

Líder: **`/eden:node`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`) `eden:node-*`.
Reglas del stack: `rules/node/eden-node-rules.md` y el sabor del proyecto (`rules/node/flavors/node.md`,
`express.md` o `nest.md`). Contrato común: `rules/eden-team-rules.md`.

> **Este stack es el back-end en Node.** Next.js (también corre en Node) es del stack `react`, con sus
> route handlers y Server Actions; una app de Shopify, del stack `shopify-app`. La detección ya lo separa
> (`eden-stack-rules.md`).

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:node-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe: quién usa el servicio, el módulo, la ruta o el esquema |
| `architect` | `eden:node-architect` (modo `audit` / `decide`) | Onboarding de un proyecto avanzado; decidir el escalón reuse-first y dónde vive cada cosa |
| `implementer` | `eden:node-dev` / `eden:node-data-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:node-data-dev` | Esquema y migraciones (Prisma, Drizzle, TypeORM, Mongoose), repositorios, colas y jobs, clientes de APIs externas |
| `tester` | `eden:node-tester` | Tests primero: unitarios e integración HTTP (Vitest, Jest o `node:test` + supertest), con base de tests |
| `devops` | `eden:node-devops` | Setup, versión de Node, gestor de paquetes, TypeScript, ESLint, scripts, `.env.example`, Docker local, CI |
| `migrator` | `eden:node-data-dev` (modo `migrate`) | Migraciones de esquema y de datos, en local o tests, revisando el SQL generado |
| `reviewer` | `eden:node-qa-reviewer` | Revisión del diff + lint, typecheck, tests y build en verde |
| `quality-auditor` | `eden:node-qa-reviewer` (modo `quality`) | Rendimiento (consultas, N+1, event loop bloqueado), logs y observabilidad |
| `security-auditor` | `eden:security-auditor` | Validación, autorización, inyección, SSRF, JWT, CORS, dependencias; lee el módulo Node |

`design-extractor`, `design-system` y `design-auditor` no aplican: este stack no tiene UI. Si la API
la consume un front con diseño, ese trabajo es del stack del front (React, móvil).

## Propiedad de archivos (quién escribe qué)

**Manda la estructura real del proyecto** (`src/routes`, `src/modules/*`, `src/services`…); el
`node-architect` la confirma en el inventario y el líder asigna por equivalencia.

| Archivos | Dueño |
|---|---|
| Rutas y routers (Express), controladores, módulos y controladores de Nest, middleware, guards, pipes, interceptors, filtros de errores, servicios de aplicación | `eden:node-dev` |
| Esquemas de validación y DTOs de entrada/salida (Zod, class-validator) | `eden:node-dev` |
| Esquema de datos (`schema.prisma`, `src/db/schema.ts`, entidades, modelos de Mongoose), migraciones, seeds, repositorios o capa de acceso a datos | `eden:node-data-dev` |
| Jobs y workers (BullMQ u otro), eventos, clientes de APIs externas, webhooks salientes | `eden:node-data-dev` |
| Tests: `*.test.*`, `*.spec.*`, `test/`, `__tests__/`, `*.e2e-spec.ts`, fixtures y factories | `eden:node-tester` |
| `package.json` (scripts y dependencias), lockfile, `tsconfig*.json`, `eslint.config.*`, `nest-cli.json`, `vitest.config.*`/`jest.config.*`, `prisma.config.*`/`drizzle.config.*`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `.github/` | `eden:node-devops` |
| Punto de entrada (`src/main.ts`, `src/server.ts`, `app.ts`) con middleware global, CORS, seguridad y `AppModule` | **Líder decide** — afecta a toda la API. Se asigna con encargo explícito |
| `.env` con valores reales | **Nadie** — los secretos los pone el dev; el kit solo mantiene `.env.example` sin valores |

Si una unidad cruza dueños, el líder la parte en unidades secuenciales (tester → data-dev → node-dev).
Nunca dos agentes sobre el mismo archivo en paralelo.

## Prohibiciones — no negociables

| Nunca | Por qué |
|---|---|
| Desplegar (cualquier proveedor, SSH, push a la rama que despliega) | El deploy lo hace el dev |
| Migrar, sembrar o resetear una base que no sea local o de tests (`prisma migrate deploy`/`reset`, `drizzle-kit push` contra producción…) | Borra o cambia datos reales |
| Ejecutar escrituras a mano en una base real | Es la base del cliente |
| Agregar, quitar o actualizar dependencias sin el sí del dev | Es código de terceros en el proyecto del cliente |
| Escribir secretos en el código, en `.env.example` o en logs | Se filtran |
| Desactivar una regla de lint, un check de TypeScript (`any`, `@ts-ignore`) o un test para que pase | Se arregla la causa |
| Cambiar la versión mayor de Node, Express, NestJS o del ORM como parte de otra tarea | Una migración de versión es una tarea propia |

Sin riesgo y sin autorización: `install` con el lockfile tal cual, `lint`, `typecheck`, `test`, `build`,
`dev` en local, y migraciones **en la base local o de tests** declarada desechable.

## Formato de handoff (todos los especialistas)

```
🟩 {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {tests, lint, typecheck, build, migración en local… con el resultado real}
No verificado: {qué y por qué}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

| Fase | Especialistas |
|---|---|
| 1. Discovery | architect |
| 2. Setup | devops (`/eden:node-setup`) |
| 3. Modelo de datos | data-dev (esquema y migraciones), con su plan aprobado |
| 4. Build | tester (primero) → data-dev → node-dev |
| 5. QA | reviewer, quality-auditor, security-auditor |
| 6. Entrega | `turnoff-task`. El deploy lo hace el dev |
