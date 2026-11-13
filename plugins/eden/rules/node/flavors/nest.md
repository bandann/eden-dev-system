# Sabor: NestJS

APIs con NestJS: módulos, controladores, providers con inyección de dependencias, guards, pipes,
interceptors y filtros. Este sabor está verificado para **NestJS 12** (2026-10-22); un proyecto en 11 o
anterior sigue en su versión, y la migración (con `nest upgrade` y la guía oficial) es una tarea propia.

## Estructura

```
src/
├── main.ts                      bootstrap: pipes, filtros e interceptors globales, CORS, Helmet, apagado
├── app.module.ts                módulo raíz (blast radius de toda la app)
├── config/                      @nestjs/config + validación del entorno
├── common/                      guards, pipes, interceptors, filtros y decoradores compartidos
└── {recurso}/
    ├── {recurso}.module.ts · .controller.ts · .service.ts
    ├── dto/                     entrada y salida
    └── entities/ · repositories/
test/                            e2e (*.e2e-spec.ts)
```

`nest generate {resource|module|controller|service}` respeta la estructura; se usa si el proyecto lo hace.

## NestJS 12 — lo que cambió

- Los paquetes del core se publican en **ESM**; un proyecto CommonJS sigue funcionando gracias a
  `require(esm)` de Node.
- Proyectos nuevos: ESM o CommonJS a elegir; **los ESM usan Vitest por defecto** y oxlint como linter. Con
  Jest, tiene que ser **Jest 30**.
- **`StandardSchemaValidationPipe`** valida con Zod, Valibot o ArkType, y convive con `ValidationPipe`.
- Requisitos: la app corre en Node 20.19+ o 22.12+; el CLI (`nest new`, `nest generate`, `nest upgrade`)
  pide Node 22.22+, 24.15+ o 26+.
- Otros cambios (orden de los hooks de ciclo de vida, `@Optional()` ya no se hereda, Webpack deprecado
  en favor de Rspack): se consultan en la guía de migración antes de tocar esas piezas.

## Validación

- **`ValidationPipe` global** con `whitelist: true`, `forbidNonWhitelisted: true` y `transform: true` (o
  el pipe de esquemas que use el proyecto). Sin `whitelist`, cualquier campo extra del body llega al
  servicio.
- DTOs de entrada con class-validator (o esquemas Zod), uno por operación; DTOs de salida o
  serialización (`ClassSerializerInterceptor`, `@Exclude`) para no devolver campos internos.

## Auth y autorización

- **Guards** para autenticación (JWT, sesión; con Passport si el proyecto lo usa) y para roles o
  permisos. La autorización **por recurso** (¿es suyo?) se comprueba en el servicio o en un guard que
  carga el recurso: un guard de roles no evita un IDOR.
- **No se confía solo en middleware para proteger rutas**: en 2025–2026 NestJS publicó varios avisos
  altos de bypass de middleware (codificación de URL, peticiones `HEAD`, barra final y destinos en forma
  absoluta, sobre todo con el adaptador Fastify), y uno crítico de CSRF → RCE en la integración de
  devtools (2025-08-01). La protección de una ruta va en **guards**, y la versión de Nest se mantiene al
  día con los avisos (https://github.com/nestjs/nest/security/advisories).
- El módulo de devtools nunca se habilita fuera de local.

## Errores, interceptors y config

- Excepciones HTTP de Nest (`NotFoundException`, `ForbiddenException`…) y un **filtro global** con formato
  único, sin pila al cliente.
- `@nestjs/config` con validación del entorno al arrancar; los valores se inyectan con `ConfigService`,
  no con `process.env`.
- `app.enableShutdownHooks()` para cerrar conexiones al recibir `SIGTERM`.

## Adaptador

Express por defecto; Fastify (`@nestjs/platform-fastify`) si el proyecto lo usa. No se cambia de
adaptador como parte de otra tarea.

## Tests

`@nestjs/testing` (`Test.createTestingModule`) para unitarios con providers simulados, y **e2e** con
supertest sobre `app.getHttpServer()` contra la base de tests. El runner es el del proyecto (Vitest o
Jest 30).

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} test && {pm} run test:e2e && {pm} run build && {pm} audit
```
