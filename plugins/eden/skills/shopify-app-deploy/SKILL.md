---
name: shopify-app-deploy
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:shopify-app-deploy`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify-app` con su confirmación. NO lo actives porque se hable de desplegar o de la App Store:
  si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: PREPARA una versión de una app
  de Shopify: qué cambia (configuración, scopes, extensiones, servidor), en qué orden se despliega el
  servidor y se libera la versión, la checklist de la App Store (scopes mínimos, webhooks de
  cumplimiento, datos protegidos, rendimiento), las notas y los comandos exactos. NUNCA ejecuta `shopify
  app deploy` ni `release` ni despliega el servidor: eso lo hace el dev.
argument-hint: "[entorno, p.ej. production] [| notas]"
disable-model-invocation: true
---

## Shopify App Deploy — preparar la versión (libera el dev)

Argumento recibido: `$ARGUMENTS`

`shopify app deploy` **crea una versión de la app y, salvo que se diga lo contrario, la libera para todas
las tiendas que la tienen instalada**: configuración, scopes y extensiones cambian para todos a la vez.
Por eso este skill **solo prepara**. Reglas: `rules/shopify-app/eden-shopify-app-rules.md` § Entorno y
versiones.

> **Idioma:** al dev, en español. Notas de la versión en inglés salvo que el dev pida otro idioma.

### Paso 1 — Qué cambia en esta versión

`eden:shopify-app-architect` compara con la última versión liberada (`shopify app versions list` y la
etiqueta o rama que diga el dev):

| Cambia | Llega a las tiendas al… | Riesgo |
|---|---|---|
| Código del servidor | desplegar el servidor | Las tiendas usan el código nuevo al instante |
| `shopify.app*.toml` (URLs, suscripciones, app proxy) | liberar la versión | Para todas a la vez |
| **Scopes nuevos** | liberar la versión | **Cada tienda tiene que aprobarlos**; hasta entonces, lo que los usa falla |
| Extensiones y funciones | liberar la versión | Para todas a la vez |

### Paso 2 — Checklist (requisitos vigentes, no de memoria)

```
🧩 VERSIÓN {entorno} — CHECKLIST

Configuración: shopify.app.{entorno}.toml {✅} · API {v} con soporte {✅ hasta {fecha}}
Scopes: {sin cambios | nuevos: … — el servidor tolera que una tienda aún no los apruebe ✅ | ❌}
Webhooks: suscripciones {…} · cumplimiento (customers/data_request, customers/redact, shop/redact) {✅ | n/a}
Datos protegidos de clientes: {nivel solicitado y aprobado | no usa}
Extensiones: {lista · build ✅ · dentro de límites ✅}
Servidor: {migraciones de base pendientes · variables de entorno nuevas}
Calidad: tests ✅ · lint ✅ · typecheck ✅ · build ✅ · security-check deps {…}
App Store: {requisitos de revisión que aplican — verificados en shopify.dev}
Notas: {borrador}
```

Lo que no se puede comprobar en local se marca como **no verificado**, con cómo verificarlo.

### Paso 3 — El orden seguro

Si hay scopes o configuración nueva que el código necesita, **primero el servidor tolerante** (que
funcione con y sin el cambio), después liberar la versión, y al final limpiar lo provisional. Si el
código del servidor depende de algo que solo existe tras liberar, se dice y se ordena.

### Paso 4 — Entregar al dev

```
🧩 VERSIÓN {entorno} — LISTA PARA LIBERAR

Checklist: {✅ todo | ⚠️ pendientes: …}
Orden (lo ejecutas tú):
  1. {desplegar el servidor — tu proveedor}             {+ migraciones de base}
  2. shopify app deploy --config {entorno} --no-release   ← crea la versión sin liberarla (sin --no-release, se libera a todas las tiendas)
  3. {shopify app release --version {x} — si la creaste sin liberar}
Después: {verificar en una tienda de desarrollo con la versión liberada}
No verificado: {…}
```

El trabajo queda en la rama **sin commitear**. Desplegar y liberar es del dev.
