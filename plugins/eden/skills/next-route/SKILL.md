---
name: next-route
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:next-route`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:react` o
  `/eden:go` con su confirmación. NO lo actives porque el proyecto sea Next.js o haya que tocar una
  página: si no lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca:
  crea o modifica UNA ruta de Next.js (App Router): página, layout, loading/error/not-found, route
  handler o Server Action, con su carga de datos, la frontera server/client decidida, caché y
  revalidación según la versión instalada, metadata/SEO, y la seguridad de servidor (auth, validación,
  DTOs) desde el primer intento. Test primero. No commitea.
argument-hint: "<ruta, p.ej. /dashboard/[id] | api/orders> [| page | layout | route | action] [| url-ticket | url-figma] [| notas]"
disable-model-invocation: true
---

## Next Route — una ruta de Next.js

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una ruta** del App Router: una página con sus datos, un layout, un route
handler (`route.ts`) o una Server Action. Reglas: `rules/react/eden-react-rules.md` y
**`rules/react/flavors/next.md`**, que se lee entero antes de planear. Equipo: `teams/react/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 0 — ¿Es Next con App Router?

`eden_stack.py detect` debe dar `react` · `next`. Si el proyecto usa **Pages Router** para esa parte,
se sigue Pages Router (y el skill lo dice); si no es Next, se para y se propone `/eden:react-component`
o `/eden:go`. Se anota la **versión de Next instalada** y si tiene `cacheComponents`: las APIs de caché,
de peticiones y de `proxy` se comprueban con context7 para esa versión.

### Paso 1 — Entender el pedido

Qué ruta, qué tipo (página, layout, route handler, Server Action), qué datos lee y qué escribe, quién
puede acceder, y qué SEO necesita. Del ticket y del Figma si los hay. Si falta algo que cambia el
resultado, se pregunta una vez.

### Paso 2 — Lo que ya existe (delegado)

- `eden:react-architect` → `inventory` de la carpeta de la ruta y sus vecinas (layouts que la envuelven,
  `loading`/`error` heredados, la DAL o los clientes de datos que ya existen, cómo se autentica) +
  `blast-radius` si se toca un layout, un route handler usado por otros o la DAL.
- `eden:figma-extractor` si la ruta tiene UI con diseño (caché de diseño primero).

### Paso 3 — El plan

```
⚛️ RUTA — {/ruta}  ·  Next {versión} {· Cache Components}

Archivos: app/{…}/page.tsx · layout.tsx · loading.tsx · error.tsx · route.ts · actions.ts · {DAL}
Servidor / cliente: {qué es Server Component; qué hojas llevan 'use client' y por qué}
Datos: {qué se lee, de dónde (DAL), con qué caché: 'use cache' + cacheLife + cacheTag | sin caché + <Suspense>}
Escrituras: {Server Actions / route handlers} → invalidan {updateTag / revalidateTag / revalidatePath}
🛡️ Superficie: entra {params, searchParams, FormData…} · quién {sesión + propiedad del recurso} ·
              sale {DTO} · secretos {solo en la DAL, server-only} · terceros {…}
Metadata: {metadata | generateMetadata} · {robots / sitemap / JSON-LD si aplica}
Estados: loading · error · not-found · vacío
Tests: {unitarios: actions y utilidades · e2e: la ruta}
Queda fuera: {…}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego la ruta

1. `eden:react-tester`: tests unitarios de las Server Actions y utilidades (validación, autorización
   denegada, éxito) y un **e2e** de la ruta (los Server Components asíncronos se prueban así) → rojo.
2. `eden:react-data-dev`: DAL/`server-only`, Server Actions, route handlers, caché e invalidación —
   cada acción y handler comprueba **quién y si puede**, valida la entrada y devuelve un DTO.
3. `eden:react-ui-dev`: `page`/`layout`/`loading`/`error`/`not-found` y los componentes, con
   `'use client'` solo en las hojas acordadas.
4. Si hay Figma: `eden:design-auditor` en loop hasta 1:1.

### Paso 5 — Verificar y reportar

`eden:react-qa-reviewer` (lint, typecheck, tests, `build` — que no avise de rutas bloqueantes) y
`eden:security-auditor` sobre las Server Actions y route handlers nuevos.

```
⚛️ RUTA — {/ruta} — LISTA

Archivos: {…}
Servidor / cliente: {…} · Caché: {…}
Seguridad: {acciones y handlers con auth + validación ✅ | hallazgos}
Tests: unit {n ✅} · e2e {n ✅} · lint ✅ · typecheck ✅ · build ✅ {avisos: …}
SEO: {metadata ✅ · …}
No verificado: {…}
```

No commitea ni pushea.
