# Sabor: Next.js

React **con servidor**: el App Router, Server Components por defecto, Server Actions y route handlers.
Es el sabor que más cambia entre versiones — **las APIs de caché, de peticiones y de middleware se
comprueban con context7 contra la versión instalada antes de usarlas**. Lo de abajo está verificado
para Next 16 (2026-10-22).

## App Router o Pages Router

- **App Router (`app/`)** es el camino recomendado y el que asume este sabor.
- **Pages Router (`pages/`)** sigue existiendo: en un proyecto que lo usa, **se sigue usando**
  (`getServerSideProps`, `getStaticProps`, `pages/api`). Un proyecto con los dos está en migración: se
  declara y no se mueve nada de uno a otro como parte de otra tarea.

## Estructura (App Router)

```
app/
├── layout.tsx          layout raíz (blast radius de toda la app)
├── page.tsx            ruta /
├── (grupo)/            grupos de rutas: organizan sin cambiar la URL
├── dashboard/
│   ├── layout.tsx · page.tsx · loading.tsx · error.tsx · not-found.tsx
│   └── [id]/page.tsx   segmento dinámico
└── api/…/route.ts      route handlers
components/ · lib/ (lib/dal o similar: acceso a datos server-only)
proxy.ts                (antes middleware.ts) — se ejecuta antes de cada petición que encaja
next.config.ts
```

## Servidor y cliente — la frontera

- **Todo es Server Component por defecto.** Puede ser `async`, leer datos y secretos, y no envía su
  JS al navegador.
- **`'use client'` marca una frontera**: ese archivo y lo que importa van al navegador. Va en la
  **hoja** que necesita estado, efectos, eventos o APIs del navegador — nunca en un layout ni en una
  página entera "para que funcione".
- Lo que cruza la frontera (props de servidor → cliente) debe ser serializable y **no lleva nada
  sensible**: se pasan DTOs, no filas de la base de datos.
- **`import 'server-only'`** en todo módulo con secretos o acceso a datos: si alguien lo importa desde
  el cliente, el build falla. El patrón recomendado es una **capa de acceso a datos** (DAL) server-only
  que comprueba la autorización y devuelve DTOs; solo ella lee los secretos de `process.env`.

## APIs de petición — asíncronas

En Next 16 el acceso síncrono se eliminó: `await cookies()`, `await headers()`, `await draftMode()`,
`await params`, `await searchParams`. Los tipos de ayuda (`PageProps<'/ruta'>`, `LayoutProps`,
`RouteContext`) salen de `npx next typegen`.

## Caché y revalidación

Es la parte que más cambió. Hay dos modelos, y **se sigue el que tenga el proyecto** (`next.config.*`):

**Cache Components** (`cacheComponents: true`; lo activan los proyectos nuevos de 16.4 y será el
default en 17):

- Nada se cachea si no se pide. Se cachea con la directiva **`'use cache'`** en una función, un
  componente o un archivo, **siempre con su `cacheLife(...)`** (`'minutes'`, `'hours'`, `'days'`…) y
  etiquetado con `cacheTag(...)` para poder invalidarlo.
- Lo que depende de la petición (cookies, headers, `params`, `searchParams`, un `fetch` sin caché) va
  dentro de un **`<Suspense>`**, o el build lo marca como ruta bloqueante.
- Variantes: `'use cache: private'` (por usuario) y `'use cache: remote'`.
- **Invalidar:** en una Server Action, `updateTag(tag)` para que el usuario vea su propio cambio al
  instante; `revalidateTag(tag, perfil)` (el segundo argumento ya es obligatorio) para el resto;
  `refresh()` refresca el router del cliente. `revalidatePath` sigue existiendo.
- Las banderas antiguas (`experimental.ppr`, `dynamicIO`, `useCache`) ya no existen.

**Modelo anterior** (sin `cacheComponents`): `fetch` y los route handlers `GET` **no** se cachean por
defecto desde la 15; se opta con `cache: 'force-cache'`, `next: { revalidate }` o
`export const dynamic = 'force-static'`.

**Un `'use cache'` jamás envuelve datos de un usuario concreto** sin `'use cache: private'`: es la
forma de servirle a un usuario los datos de otro.

## Server Actions y route handlers — son endpoints públicos

- **Una Server Action se puede llamar con un POST directo**, aunque ningún componente la importe. La
  autorización de la página **no** la protege.
- En **cada** Server Action y **cada** route handler:
  1. **Quién pide** (sesión) **y si puede** (es suyo el recurso: sin IDOR).
  2. **Validar toda la entrada** (`FormData`, `params`, `searchParams`, headers) con el esquema del
     proyecto.
  3. **Devolver lo mínimo** (un DTO o un estado), nunca la fila de la base ni el error interno.
  4. Limitar la frecuencia de lo caro o lo que envía correo.
- Self-hosted con varias instancias: `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` fija; detrás de un proxy,
  `serverActions.allowedOrigins`.

## proxy.ts (antes middleware.ts)

- En Next 16, `middleware.ts` pasó a llamarse **`proxy.ts`** (exporta `proxy()`) y corre en Node.js;
  `middleware.ts` queda solo para el runtime edge. Hay un codemod (`middleware-to-proxy`), pero
  **migrar es una tarea aparte**.
- Sirve para redirecciones, reescrituras y cabeceras. **No es la autorización**: en 2025 un bypass del
  middleware (CVE-2025-29927) dejó pasar peticiones que solo protegía él. La comprobación de verdad
  vive en la DAL, la Server Action y el route handler.
- Su blast radius es toda la app: lo asigna el líder con encargo explícito.

## Metadata, imágenes y fuentes

- **Metadata API:** `export const metadata` o `generateMetadata()` por ruta; `robots`, `sitemap` y
  datos estructurados (JSON-LD) en las rutas que lo necesitan. Es SEO de primera: se mantiene en todo
  lo que se toca.
- **`next/image`:** `width`/`height` o `fill` con `sizes`, `alt` real, `priority` solo en la imagen LCP.
  Las imágenes remotas, con `images.remotePatterns` (no `images.domains`, deprecado).
- **`next/font`** para las fuentes del proyecto (autoalojadas, sin saltos de layout), conectadas a los
  tokens.

## Entorno

- **Turbopack** es el bundler por defecto en `dev` y en `build`. Una config de `webpack` propia hace
  fallar el build salvo con `--webpack`: no se añade sin el sí del dev.
- **`next lint` ya no existe** y `next build` no corre el lint: se usa el CLI de ESLint con
  `eslint-config-next` (flat config). El script `lint` del proyecto lo refleja.
- Variables: solo `NEXT_PUBLIC_*` llega al navegador (se incrusta al compilar). Leer una variable en
  tiempo de ejecución, en el servidor, con `await connection()` antes.
- Node mínimo: el que diga la doc vigente de la versión instalada (para la 16, ≥ 20.9).

## Seguridad — avisos recientes que hay que conocer

Next publica parches de seguridad con cadencia fija y fuera de ciclo. Además del aviso de React Server
Components de diciembre de 2025 (CVE-2025-55182 / CVE-2025-66478), en 2026 hubo RCE críticas en
`ImageResponse` (`next/og`), en funciones `'use cache'` y en la optimización de imágenes con SVG, y un
DoS en apps con Server Actions. **Regla:** la versión de Next del proyecto se compara con los avisos
vigentes (https://nextjs.org/blog) en el onboarding y en `security-check deps`; una versión afectada con
parche disponible es **Crítica**, y actualizar lo decide el dev.

## Tests

Vitest (o Jest) + Testing Library para Client Components, utilidades y Server Actions puras.
**Los Server Components asíncronos se prueban con e2e** (Playwright contra `next build && next start`
o `next dev`), porque las herramientas unitarias no los soportan bien.

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} run test && {pm} run build
```

`next build` también avisa de rutas bloqueantes con Cache Components: un aviso nuevo se resuelve, no se
ignora. Y en el navegador, sin errores de hidratación en consola.
