---
name: shopify-app-extension
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:shopify-app-extension`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify-app` o `/eden:go` con su confirmación. NO lo actives porque se mencione el checkout, un
  app block o un descuento: si no lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando
  SÍ se invoca: crea o modifica UNA extensión de una app de Shopify (theme app extension con app blocks o
  app embeds, checkout UI, customer account UI, admin UI, Shopify Function, web pixel) con la API y la
  versión vigentes de esa superficie, dentro de sus límites, generada con el CLI, con tests primero y
  probada en la tienda de desarrollo. Avisa de que exige liberar una versión. No commitea.
argument-hint: "<qué extensión y para qué> [| superficie] [| url-ticket | url-figma]"
disable-model-invocation: true
---

## Shopify App Extension — una extensión

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una extensión**: lo que la app pone en la tienda, el checkout, la cuenta del
cliente o el admin, o la lógica que corre dentro de Shopify (Functions). Reglas:
`rules/shopify-app/eden-shopify-app-rules.md` § Extensiones. Equipo: `teams/shopify-app/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — ¿Qué superficie?

| Si el comerciante quiere… | Superficie |
|---|---|
| Algo en su tienda online sin editar el tema | Theme app extension (app block o app embed) |
| Algo en el checkout o la página de gracias | Checkout UI extension |
| Lógica de descuentos, envíos, pagos, validación del carrito o transformar el carrito | Shopify Function |
| Algo en la cuenta del cliente | Customer account UI extension |
| Una acción o bloque dentro del admin | Admin UI extension (action o block) |
| Medir eventos del cliente | Web pixel |

Si hay duda entre dos, se dice con sus pros y contras y decide el dev. Lo que pide el comerciante puede
existir ya como funcionalidad nativa de Shopify: se mira antes (escalón 1).

### Paso 2 — Lo que ya existe (delegado)

`eden:shopify-app-architect` → las extensiones de la app, su API y versión, y si ya hay una que se pueda
extender. La API de la superficie y sus límites, **verificados en la doc vigente** (context7 o el MCP de
Shopify Dev) para su versión.

### Paso 3 — El plan

```
🧩 EXTENSIÓN — {nombre}  ·  {superficie} · API {versión}

Escalón: {n} — {por qué no alcanza el anterior}
Se crea con: shopify app generate extension --template {x} {| ya existe: extensions/{x}}
Qué hace: {…} · configurable por el comerciante: {settings}
Límites: {tamaño, instrucciones, componentes disponibles — verificados}
Datos: {qué lee (consulta de entrada de la función, metafields) · scopes}
Rendimiento: {impacto en la tienda o el checkout}
Si falla: {qué ve el cliente — nunca bloquear el checkout}
Tests (primero): {entradas de ejemplo · estados}
Versión de la app: hay que liberar para que llegue a las tiendas

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego la extensión

1. `eden:shopify-app-tester`: tests de la función con entradas de ejemplo y casos límite, o de la UI de la
   extensión → rojo.
2. `eden:shopify-app-extension-dev`: genera (si es nueva) e implementa hasta verde, dentro de los límites.
3. Si necesita datos del servidor de la app: `eden:shopify-app-backend-dev`.
4. Con el sí del dev: probada en la tienda de desarrollo con `shopify app dev`.

### Paso 5 — Verificar y reportar

`eden:shopify-app-qa-reviewer` (y `quality` si afecta al rendimiento de la tienda).

```
🧩 EXTENSIÓN — {nombre} — LISTA

Superficie: {…} · API {v} · Archivos: extensions/{…}
Límites: {✅ dentro} · Rendimiento: {…}
Tests: {n ✅} · build ✅
Probada en la tienda de desarrollo: {✅ | no}
Versión de la app: hay que liberar → /eden:shopify-app-deploy
No verificado: {…}
```

No commitea ni pushea.
