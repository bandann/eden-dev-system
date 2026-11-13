---
name: shopify-app-webhook
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:shopify-app-webhook`, lo pide de forma explícita e inequívoca, o encadenado desde
  `/eden:shopify-app` o `/eden:go` con su confirmación. NO lo actives porque se mencione un webhook: si no
  lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: añade o corrige UN
  webhook de una app de Shopify de punta a punta: la suscripción (en el TOML de la app o por tienda), el
  handler con verificación de HMAC sobre el cuerpo crudo, respuesta rápida con el trabajo en cola,
  idempotencia ante reintentos, y los de cumplimiento obligatorios cuando aplica; con tests de HMAC
  válido e inválido y de evento repetido, y probado con `shopify app webhook trigger`. No commitea.
argument-hint: "<tema del webhook, p.ej. orders/create> [| qué debe hacer] [| url-ticket]"
disable-model-invocation: true
---

## Shopify App Webhook — un webhook, sin perder ni repetir eventos

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **reaccionar a un evento de Shopify**. Un webhook mal hecho falla en silencio:
acepta eventos falsos (sin HMAC), pierde eventos (tarda y Shopify corta), o los procesa dos veces
(reintentos). Reglas: `rules/shopify-app/eden-shopify-app-rules.md` § Webhooks. Si el dev tiene el plugin
`smg-shopify-app`, su agente `webhook-builder` cubre lo mismo para los equipos de SMG: se puede usar en su
lugar si el dev lo prefiere.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué tema (`orders/create`, `products/update`, `app/uninstalled`…), qué tiene que hacer la app, cuánto
tarda eso, y si el tema necesita un scope que la app no tiene (lo decide el dev).

### Paso 2 — Lo que ya existe (delegado)

`eden:shopify-app-architect` → cómo se suscriben los webhooks (en el TOML de la app o por tienda), los
handlers existentes y cómo se autentican, si hay cola de trabajos, y si la app es pública (entonces los
webhooks de cumplimiento son obligatorios).

### Paso 3 — El plan

```
🧩 WEBHOOK — {tema}

Suscripción: {shopify.app.toml [webhooks] | por tienda} · versión de la API {v} · filtro {si aplica}
Scope: {ya lo tiene | nuevo: … — ⚠️ lo apruebas tú}
Handler: app/routes/webhooks.{…} · verificación: authenticate.webhook (HMAC sobre el cuerpo crudo)
Respuesta: inmediata · trabajo lento: {cola/job}
Idempotencia: {clave: id del evento / del recurso} · reintentos de Shopify: {cómo se manejan}
Cumplimiento: {customers/data_request · customers/redact · shop/redact — ✅ | n/a}
Tests (primero): HMAC inválido → 401 sin efectos · válido → efecto · repetido → una vez
Versión de la app: {liberar si cambia el TOML | solo servidor}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego el webhook

1. `eden:shopify-app-tester`: payload de ejemplo del tema, y los tres casos (HMAC inválido, válido,
   repetido) → rojo.
2. `eden:shopify-app-backend-dev`: suscripción (en el TOML, con el encargo del líder), handler con el
   helper de autenticación, cola e idempotencia, hasta verde.
3. Con el sí del dev: `shopify app webhook trigger --topic {tema}` contra la app de desarrollo.

### Paso 5 — Verificar y reportar

`eden:shopify-app-qa-reviewer` y `eden:security-auditor` (un webhook es una entrada pública).

```
🧩 WEBHOOK — {tema} — LISTO

Suscripción: {…} · Handler: {…}
HMAC: verificado ✅ · Respuesta rápida ✅ · Idempotente ✅ · Cumplimiento: {✅ | n/a}
Tests: {n ✅} · lint ✅ · typecheck ✅
Probado con webhook trigger: {✅ | no}
Versión de la app: {liberar | solo servidor}
```

No commitea ni pushea.
