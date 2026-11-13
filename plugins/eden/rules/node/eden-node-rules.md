# Módulo Node — Eden (back-end)

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-code-style`,
`eden-quality`, `eden-testing`, `eden-security`). Aquí solo va lo que es propio de un back-end en Node.
Lo de cada sabor vive en `flavors/`:

| Sabor | Archivo | Qué es |
|---|---|---|
| **Node** | `flavors/node.md` | Node sin framework o con librerías pequeñas: servicios, workers, CLIs, APIs mínimas |
| **Express** | `flavors/express.md` | APIs y servidores con Express |
| **NestJS** | `flavors/nest.md` | APIs con NestJS: módulos, controladores, providers, guards, pipes |

**Next.js no es este stack** (es del stack `react`, con sus route handlers y Server Actions), ni una app
de Shopify (`shopify-app`). El sabor se declara en `.claude/project-config.json` → `node.flavor` (lo
escribe `/eden:node-setup`) o lo detecta `scripts/eden_stack.py detect`. Si no está claro, se pregunta.

> **La realidad del proyecto manda.** Si el proyecto organiza el código de otra forma coherente, se
> sigue el proyecto.

---

## Versiones — se verifican, no se recuerdan

Node publica una LTS al año (a partir de la 27, una versión al año) y los frameworks y ORMs cambian de
API entre mayores. **Antes de usar una API que no sea trivial, se comprueba con context7 contra la
versión instalada.**

Referencia **verificada el 2026-10-22** (punto de partida, no verdad):

| Herramienta | Versión | Lo que más importa |
|---|---|---|
| Node.js | 26 (LTS desde el 2026-10-28) · 24 (mantenimiento, fin 2028-04-30) · 22 (mantenimiento, fin 2027-04-30) | 20 y 25 ya sin soporte. Type stripping estable (`node archivo.ts`, solo sintaxis borrable, sin chequeo de tipos); `require(esm)` sin bandera; `node:test` estable; Corepack ya no viene desde la 25 |
| Express | 5 | Las promesas rechazadas llegan solas al middleware de errores; rutas comodín `/*splat`; métodos eliminados de la 4 |
| NestJS | 12 | Paquetes en ESM; proyectos ESM con Vitest por defecto (Jest debe ser 30); `StandardSchemaValidationPipe` (Zod, Valibot); el CLI exige Node 22.22+, 24.15+ o 26+ |
| Prisma | 7 (8 en release candidate) | `prisma.config.ts`, generador `prisma-client` con `output` obligatorio, driver adapter obligatorio, `.env` no se carga solo |
| Drizzle | 0.45 (1.0 en RC) · TypeORM 1 · Mongoose 9 | |
| Zod | 4 | `error` en vez de `message`; formatos de primer nivel (`z.email()`, `z.uuid()`) |
| Tests | Vitest 5 · Jest 30 · supertest 7 · `node:test` | |
| TypeScript | 7 (compilador nativo) | Algunas herramientas dependen de la API programática, que llega en 7.1: comprobar compatibilidad (typescript-eslint) |
| Lint | ESLint 10 (solo flat config) · typescript-eslint 8 · Biome/oxlint como alternativas | |

Un proyecto en una versión de Node **sin soporte** se reporta en el onboarding con su fecha de fin.
Actualizar es una tarea propia y la decide el dev.

---

## Cómo se escribe

- **TypeScript estricto** (`strict: true`) y **sin `any`**. Un `@ts-ignore` o `eslint-disable` nuevo se
  justifica en el PR o no entra.
- **ESM o CommonJS, lo que use el proyecto** (`"type"` en `package.json`), sin mezclar. En proyectos
  nuevos, ESM.
- **Capas:** el borde (ruta, controlador) recibe, valida, autoriza y responde; la lógica vive en
  servicios; el acceso a datos, en repositorios o en la capa que use el proyecto.
- **Configuración centralizada y validada al arrancar** (un esquema de config con Zod o `@nestjs/config`):
  si falta una variable, la app no arranca. Nada de `process.env` repartido por el código.
- **El event loop no se bloquea**: nada de `*Sync` de `fs`, bucles de CPU pesados ni JSON gigante en una
  petición; eso va a un worker o a una cola.
- **Logs estructurados** con el logger del proyecto (id de petición, nivel, sin datos personales ni
  secretos). `console.log` de depuración no entra.
- **Apagado limpio**: la app cierra el servidor, las conexiones y los workers al recibir `SIGTERM`.

## Reuse-first en Node

1. **Lo que ya hace Node, el framework o una dependencia instalada**, tal cual (`fetch`, `node:test`,
   pipes y guards de Nest, middleware de Express ya montado).
2. **Configuración** (opciones del framework, del ORM o de la dependencia).
3. **Extender sin cambiar lo existente**: un parámetro opcional con el comportamiento actual por
   defecto, un middleware o interceptor nuevo, un evento. Antes, blast radius (`eden:node-architect`).
4. **Código mínimo acotado** a la unidad.
5. **Módulo nuevo**: último recurso, con su lugar en la estructura del proyecto.

Una dependencia nueva se propone con su porqué (mantenimiento, descargas, avisos de seguridad, tamaño) y
la decide el dev. Lo que Node ya trae (`fetch`, `crypto.randomUUID`, `node:test`, `--env-file`) gana a
una dependencia.

## API: entrada, salida y errores

- **Toda entrada se valida en el borde** (body, params, query, headers) con el esquema del proyecto (Zod
  o DTOs con class-validator): tipos, formatos, rangos y longitudes. **Lo no declarado se rechaza o se
  descarta.**
- **Autenticación y autorización en cada ruta que no sea pública**: quién es y **si puede** sobre ese
  recurso. Sin IDOR.
- **La salida es un DTO**: nunca el registro de la base (contraseñas, tokens, campos internos).
- **Errores con un formato único** y códigos de estado reales; al cliente nunca le llega la pila ni el
  mensaje interno (van al log).
- **Contrato estable**: cambiar la forma de una respuesta que alguien consume es un breaking change; se
  versiona (`/v2`) o se añade, no se rompe.
- Paginación en listados, límite de frecuencia en lo público o caro, y tamaños máximos de cuerpo.

## Datos

- **Migraciones versionadas** con la herramienta del ORM, y el SQL generado **se revisa** antes de
  aplicarlo. Nada de `push` del esquema en proyectos que versionan migraciones.
- **Consultas parametrizadas siempre** (las plantillas seguras del ORM o parámetros); jamás interpolar
  entrada en SQL. En MongoDB, operadores que vengan del usuario se rechazan.
- **Índices** en claves foráneas y en lo que se filtra u ordena; restricciones en la base. Sin N+1.
- **Transacciones** en lo que debe ocurrir junto. **Jobs idempotentes** con reintentos y backoff.
- **Los datos de clientes no se tocan fuera de local o tests** (roster § Prohibiciones).

## Tests

Siguen `eden-testing-rules.md`: **el test se escribe antes** y debe fallar primero. Los escribe el rol
`tester` (`eden:node-tester`).

- **Integración HTTP** con supertest sobre la app (sin levantar el puerto: la app se exporta separada del
  `listen`), contra una **base de tests desechable** (SQLite, una base `_test` o un contenedor).
- **Siempre los casos de seguridad**: sin token (401), recurso ajeno (403/404), entrada inválida, campos
  extra, y que la respuesta no filtre campos internos.
- Unitarios para la lógica de los servicios; lo externo, simulado en el borde.
- La puerta de `turnoff-task`: lint, typecheck, tests, build y `npm audit` (o el del gestor).

## Entorno

- **Versión de Node fijada** (`engines` y `.nvmrc`) en una LTS con soporte.
- **Gestor de paquetes:** el del lockfile (npm, pnpm, yarn, bun), sin mezclar. Desde Node 25 Corepack no
  viene incluido: si el proyecto lo usa, se instala aparte.
- **TypeScript:** `node archivo.ts` sirve para scripts y servicios con sintaxis borrable (sin `enum`,
  sin decoradores, sin parameter properties); **NestJS y cualquier código con decoradores necesitan su
  paso de build**. El chequeo de tipos es siempre `tsc --noEmit` (o el `typecheck` del proyecto).
- **Scripts que el kit usa:** `dev`, `build`, `start`, `lint`, `typecheck`, `test` (`test:e2e` si hay).

## Seguridad

Aplica `eden-security-rules.md` (principios, checklist y severidad). Lo propio de Node:

| Severidad | En Node |
|---|---|
| **Crítica** | SQL o consulta de Mongo con entrada sin parametrizar; `child_process`/`eval`/`new Function` con entrada; un secreto en el código o en el repo; una ruta que escribe sin autenticación; JWT aceptado sin verificar la firma o con `alg: none`; versión de Node, del framework o de una dependencia con RCE conocida y parche disponible |
| **Alta** | IDOR; SSRF (el servidor pide una URL que controla el usuario); prototype pollution (merge de objetos del usuario); ruta de archivo construida con entrada (path traversal); CORS con `*` y credenciales; la pila de errores al cliente; autorización solo en un middleware que se puede saltar |
| **Media** | Sin límite de frecuencia en login o en lo caro; sin límite de tamaño de cuerpo; dependencia con aviso alto sin parche; datos personales en logs; cookies sin `HttpOnly`/`Secure`/`SameSite` |
| **Baja** | Cabeceras de seguridad ausentes; `x-powered-by` expuesto |

- **JWT:** algoritmo fijado al verificar, secreto largo (o clave asimétrica) desde la config, expiración
  corta, y nada sensible en el payload (no está cifrado).
- **`child_process`:** `execFile`/`spawn` con argumentos en array, nunca una cadena de shell con entrada.
- **Node también publica parches de seguridad**: en 2026 hubo releases de seguridad en marzo, junio,
  julio y octubre (esta última con una ejecución remota en el decodificador Brotli y bypasses de TLS).
  La versión de Node del proyecto se compara con el último release de seguridad de su línea.
- `npm audit` (o el del gestor) en el onboarding, en `security-check deps` y en cada `turnoff-task`.

## Blast radius en Node

```bash
grep -rn "{Nombre}\|{ruta}\|{tabla}" --include="*.ts" --include="*.js" --include="*.mjs" --include="*.cjs" src test
```

Más: en Nest, los módulos que importan el provider; en Express, los routers que montan el middleware;
los consumidores externos de la API (front, apps, integraciones); y `graphify affected`, que entiende
JS/TS y se suma al grep. **Un cambio de esquema afecta datos reales**: se declara qué tablas y cuántos
registros.

## Documentación vigente

- Node.js: https://nodejs.org/docs/latest/api/ · versiones: https://nodejs.org/en/about/previous-releases · seguridad: https://nodejs.org/en/blog/vulnerability
- Express: https://expressjs.com · migración a 5: https://expressjs.com/en/guide/migrating-5.html · seguridad: https://expressjs.com/en/advanced/best-practice-security.html
- NestJS: https://docs.nestjs.com · avisos: https://github.com/nestjs/nest/security/advisories
- Prisma: https://www.prisma.io/docs · Drizzle: https://orm.drizzle.team · TypeORM: https://typeorm.io · Mongoose: https://mongoosejs.com
- Zod: https://zod.dev · Vitest: https://vitest.dev · Jest: https://jestjs.io · supertest: https://github.com/ladjs/supertest
