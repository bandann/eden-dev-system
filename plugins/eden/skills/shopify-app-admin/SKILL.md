---
name: shopify-app-admin
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:shopify-app-admin`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify-app` o `/eden:go` con su confirmación. NO lo actives porque haya que tocar una pantalla
  de una app: si no lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca:
  construye o modifica UNA pantalla del admin embebido de una app de Shopify de punta a punta: la ruta
  con su loader y action autenticados, las consultas y mutaciones de Admin GraphQL validadas contra el
  esquema, la UI con Polaris y App Bridge con todos sus estados, los scopes que necesita, y los tests
  primero. No commitea.
argument-hint: "<pantalla o funcionalidad> [| url-figma | url-ticket] [| datos de Shopify que usa]"
disable-model-invocation: true
---

## Shopify App Admin — una pantalla del admin embebido

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una pantalla de la app dentro del admin de Shopify**: una lista, un detalle,
un formulario de configuración, un flujo. Reglas: `rules/shopify-app/eden-shopify-app-rules.md` § Admin
embebido y § Admin GraphQL. Equipo: `teams/shopify-app/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué ve y hace el comerciante, **qué datos de Shopify** lee o cambia (productos, pedidos, clientes,
metafields…), qué guarda la app en su base, y qué pasa en cada estado. Del ticket y del Figma si los hay.

### Paso 2 — Lo que ya existe (delegado)

En paralelo: `eden:shopify-app-architect` (rutas vecinas, cómo consulta el proyecto, Polaris que usa,
scopes actuales, `blast-radius`) y `eden:figma-extractor` si hay diseño (caché primero).

### Paso 3 — El plan

```
🧩 PANTALLA — {nombre}  ·  Admin API {v} · Polaris {web components | React}

Escalón: {n} — {¿un componente de Polaris o un patrón de App Bridge lo resuelve?}
Ruta: app/routes/{…} · loader {qué lee} · action {qué cambia}
GraphQL: {consultas y mutaciones — validadas contra {v}} · coste {…} · paginación {cursores}
Scopes: {usa: … | nuevo: … — ⚠️ cada tienda tendrá que aprobarlo}
Datos de la app: {tabla/modelo — o ninguno}
UI: {componentes de Polaris} · App Bridge: {title bar, modal, toast, save bar, resource picker}
Estados: carga · vacío · error (userErrors) · éxito
🛡️ Superficie: autenticado {authenticate.admin} · datos de clientes {…} · secretos {solo servidor}
Tests (primero): {loader/action con auth simulada · userErrors · UI}
Queda fuera: {…}

¿Le doy?
```

Espera el sí (y el de cualquier scope nuevo).

### Paso 4 — Test primero, luego la pantalla

1. `eden:shopify-app-tester`: tests del loader/action (sin sesión, `userErrors`, éxito) y de la UI → rojo.
2. `eden:shopify-app-backend-dev`: loader, action y consultas validadas, hasta verde.
3. `eden:shopify-app-admin-dev`: la UI con Polaris y App Bridge, con todos los estados.
4. Si hay Figma: `eden:design-auditor` en loop.

### Paso 5 — Verificar y reportar

`eden:shopify-app-qa-reviewer` y, si toca datos de clientes o scopes, `eden:security-auditor`.

```
🧩 PANTALLA — {nombre} — LISTA

Archivos: {…}
GraphQL: validado contra {v} ✅ · Scopes: {sin cambios | nuevos (aprobados)}
Tests: {n ✅} · lint ✅ · typecheck ✅ · build ✅
Probado en la tienda de desarrollo: {✅ | no}
Versión de la app: {solo servidor | hay que liberar — por {…}}
No verificado: {…}
```

No commitea ni pushea.
