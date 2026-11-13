# Módulo Shopify App — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-design`,
`eden-code-style`, `eden-quality`, `eden-testing`, `eden-security`). Aquí va lo propio de **las apps** de
Shopify: el servidor embebido en el admin, sus extensiones y funciones. **Los temas son otro stack**
(`rules/shopify/`); el Liquid de una theme app extension sigue además esas reglas.

> **Lo que hace distinta a una app:** se instala en **muchas tiendas** de comerciantes. Lo que se libera
> (configuración, scopes, extensiones) llega **a todas a la vez**, y cada scope nuevo lo tiene que aprobar
> cada comerciante. Por eso liberar lo decide siempre el dev (roster § Prohibiciones).
>
> **Si el dev tiene el plugin `smg-shopify-app`**, su skill `shopify-app-rules` (OAuth, HMAC, GDPR,
> versiones de la API, Polaris, App Bridge; React Router, Remix y Express) y su agente `webhook-builder`
> son referencia adicional. Ante una contradicción, mandan la doc vigente de Shopify y el proyecto.

---

## Versiones — se verifican, no se recuerdan

Shopify publica una versión de la Admin API cada trimestre. **Toda consulta, API de extensión o flag del
CLI se comprueba con context7 o el MCP de Shopify Dev (si está conectado) para la versión que usa la
app.**

Referencia **verificada el 2026-10-22** (punto de partida, no verdad):

| Pieza | Estado | Lo que más importa |
|---|---|---|
| Shopify CLI | 4.x (Node ≥ 22.12) | `shopify app init --template reactRouter` |
| Plantilla | **React Router** (`@shopify/shopify-app-react-router` 4) | La de Remix quedó sustituida (hay codemod de migración); las apps son solo **embebidas** |
| Admin API | **2026-10** estable; con soporte 2026-01 → 2026-10 | Cada versión tiene al menos 12 meses de soporte; las de 2025 ya no |
| REST Admin API | Heredada | **Las apps públicas nuevas son solo GraphQL** desde 2025-04-01 |
| Polaris | **Web components 2.x** (`<s-page>`, `<s-button>`…) | El paquete React `@shopify/polaris` está en mantenimiento |
| App Bridge | Script del CDN + `@shopify/app-bridge-react` 4 | Debe cargarse el primero (requisito de la App Store) |
| Tokens offline | **Con expiración** | Obligatorios para apps públicas **antes del 2027-01-01** (token de 1 h, refresh de 90 días que rota) |
| Facturación | **Precios gestionados** (Shopify App Pricing) por defecto | La Billing API manual sigue soportada como heredada |
| Checkout UI extensions | API 2026-10 | Preact + Polaris web components, en un Web Worker, bundle ≤ 64 KB |
| Shopify Scripts | **Retirados** (2026-06-30) | Lo que hacían va a Shopify Functions |

Una app en una versión de la API **sin soporte**, o con tokens offline sin expiración cerca de la fecha
límite, se reporta en el onboarding. Migrar es una tarea propia y la decide el dev.

---

## Configuración (`shopify.app*.toml`)

- Un archivo por entorno: `shopify.app.toml` (desarrollo) y `shopify.app.{entorno}.toml`; se elige con
  `shopify app config use`.
- `[access_scopes] scopes`: **los mínimos**; los que solo hacen falta a veces, en `optional_scopes` y
  pedidos en el momento. Instalación gestionada por Shopify (no `use_legacy_install_flow`).
- `[webhooks] api_version` y las suscripciones en `[[webhooks.subscriptions]]` (`topics`, `uri`, `filter`,
  `include_fields`, `compliance_topics`).
- `[app_proxy]` si la app sirve contenido en la tienda.
- **El TOML lo decide el líder con el sí del dev**: cambiarlo cambia lo que la app pide a cada tienda.

## Autenticación y sesiones

- **Apps embebidas**: el admin entrega un **ID token** (JWT de 1 minuto, firmado con el secreto de la
  app) y se cambia por un token de acceso (*token exchange*). La plantilla lo valida: cada `loader` y
  `action` empieza por `authenticate.admin(request)`.
- **Tokens offline con expiración** en apps públicas (renovar con el refresh token, sin renovar dos veces
  a la vez para la misma tienda). Las apps personalizadas no lo necesitan.
- **Sin cookies de terceros**: la app no puede depender de ellas.
- **Rutas públicas**: los webhooks con `authenticate.webhook`, el app proxy con
  `authenticate.public.appProxy` (verifica la firma); nunca una ruta pública sin su verificación.
- `unauthenticated.admin(shop)` solo para trabajos en segundo plano (colas, webhooks), **nunca** en una
  petición de un usuario.
- Los tokens de acceso y el secreto de la app **nunca** salen del servidor ni van a logs.

## Admin embebido (UI)

- **Polaris para todo lo que tiene componente** (en apps nuevas, los web components; en apps con Polaris
  React, se sigue con lo que tienen — no se mezclan).
- **App Bridge** para navegación, title bar, modales, toasts, selector de recursos y barra de guardado.
  Salir del iframe a una URL externa, con la redirección de la plantilla (`target: '_top'`).
- Estados completos (skeleton, vacío con acción, error con lo que puede hacer el comerciante, éxito).
- Accesibilidad y textos traducibles si la app es multi-idioma.

## Admin GraphQL

- **GraphQL en todo código nuevo**, validado contra el esquema de la versión de la app.
- Solo los campos necesarios; paginación por cursores; `userErrors` de cada mutación tratados.
- **El coste cuenta**: límite por coste calculado (cubo con goteo); reintentos con espera ante throttling;
  para volúmenes grandes, **operaciones masivas** (bulk).
- **Datos protegidos de clientes** (nombre, dirección, teléfono, email…): solo con el nivel y los campos
  aprobados para la app; sin aprobación, Shopify devuelve `null` o errores. Se guarda lo mínimo y se
  borra cuando toca.

## Webhooks

- Suscripciones de la app en el **TOML** (preferido) o por tienda vía API.
- **HMAC** (`X-Shopify-Hmac-SHA256`) sobre el **cuerpo crudo**, antes de parsear, con comparación de
  tiempo constante: lo hace `authenticate.webhook` (devuelve 401). Ningún parser antes de verificar.
- **Responder 200 rápido** (Shopify corta la conexión al segundo y la petición a los 5 s) y dejar el
  trabajo en una cola. Reintenta 8 veces en ~4 horas.
- **Idempotencia**: `X-Shopify-Webhook-Id` identifica la entrega (duplicados); no hay orden garantizado
  (usar `X-Shopify-Triggered-At` o `updated_at`). No se confía solo en webhooks: un trabajo de
  conciliación cubre lo perdido.
- **Cumplimiento obligatorio** en toda app de la App Store: `customers/data_request`, `customers/redact` y
  `shop/redact` (con `compliance_topics`), que **hacen de verdad** lo que dicen, en 30 días como máximo.
- `app/uninstalled` limpia sesiones; `app/scopes_update` mantiene al día los scopes concedidos.

## Extensiones y funciones

- **Se crean con el CLI** (`shopify app generate extension`), cada una con su API y su versión en su TOML.
- **Theme app extensions**: app blocks y app embeds para que el comerciante no edite su tema; assets
  pequeños y solo donde se usan; Liquid según `rules/shopify/eden-shopify-rules.md`. Pesa en la tienda
  del comerciante.
- **Checkout UI y customer account UI**: solo los componentes y APIs de la superficie (sin DOM), dentro
  del límite de tamaño, y si fallan, no bloquean el checkout.
- **Shopify Functions** (Wasm; Rust recomendado, JS posible): descuentos, envíos, pagos, validación del
  carrito, cart transform…; deterministas y dentro de los límites; la consulta de entrada, mínima. En
  apps personalizadas, las funciones exigen Plus.
- **Web pixels**: solo los eventos necesarios, respetando el consentimiento.
- **Una extensión solo llega a las tiendas al liberar una versión de la app.**

## Facturación

Precios gestionados por Shopify (o la Billing API en apps que ya la usan). En la App Store, **todo cobro
pasa por Shopify** y el comerciante cambia de plan sin escribir a soporte.

## Tests

Siguen `eden-testing-rules.md` (el test primero; `eden:shopify-app-tester`):

- `loader`/`action` con la autenticación simulada (sin sesión, `userErrors`, éxito).
- Webhooks: **HMAC inválido → 401 sin efectos**, válido → efecto, **repetido → una vez**; los de
  cumplimiento hacen lo que dicen.
- Functions con entradas de ejemplo y casos límite.
- **Nada contra tiendas reales**: lo de Shopify se simula; lo integrado, en una tienda de desarrollo.

## Entorno y versiones

- `shopify app dev` solo contra **tiendas de desarrollo**; usa un túnel y actualiza la vista previa de
  desarrollo de la app.
- **`shopify app deploy` crea una versión (configuración + todas las extensiones) y la libera a todos los
  usuarios por defecto**; `--no-release` la crea sin liberar y `shopify app release --version` la libera
  después. **No despliega el servidor** (eso es del hosting de la app). Las dos cosas las hace el dev.
- Orden seguro cuando hay scopes o configuración nueva: servidor tolerante primero, después liberar.

## Seguridad

Aplica `eden-security-rules.md`. Lo propio de una app de Shopify:

| Severidad | En una app |
|---|---|
| **Crítica** | Webhook o app proxy sin verificar HMAC/firma; una ruta del servidor sin `authenticate.*`; el secreto de la app o tokens de acceso en el repo, en la UI o en logs; `unauthenticated.admin` en una petición de usuario |
| **Alta** | Scopes de más; datos protegidos de clientes sin aprobación o sin borrado; webhooks de cumplimiento que no hacen nada; mutaciones sin tratar `userErrors` que dejan datos a medias; redirección abierta al salir del iframe |
| **Media** | Webhook lento o no idempotente; versión de la API cerca de quedarse sin soporte; tokens offline sin expiración cerca de 2027-01-01; extensión que pesa en la tienda |
| **Baja** | Polaris o App Bridge desactualizados; logs verbosos |

- `npm audit` (y los avisos de los repositorios `Shopify/shopify-app-js`, `shopify-api-js` y `cli`) en el
  onboarding, en `security-check deps` y en cada `turnoff-task`.
- Rotar el secreto de la app puede tardar hasta una hora en reflejarse en el HMAC: se planifica.

## Blast radius en una app

```bash
grep -rn "{Nombre}\|{tema}\|{handle}" --include="*.ts" --include="*.tsx" --include="*.toml" --include="*.graphql" --include="*.liquid" app extensions
```

Y dos preguntas propias: **¿exige liberar una versión?** (TOML, scopes, extensiones) y **¿qué pasa en las
tiendas que aún no aprobaron un scope nuevo?**

## Documentación vigente

- Apps: https://shopify.dev/docs/apps · CLI: https://shopify.dev/docs/api/shopify-cli
- Admin GraphQL: https://shopify.dev/docs/api/admin-graphql · versiones: https://shopify.dev/docs/api/usage/versioning
- Autenticación: https://shopify.dev/docs/apps/build/authentication-authorization
- Webhooks: https://shopify.dev/docs/apps/build/webhooks · cumplimiento: https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance
- Extensiones: https://shopify.dev/docs/apps/build/app-extensions · Functions: https://shopify.dev/docs/apps/build/functions
- Polaris: https://shopify.dev/docs/api/app-home/polaris-web-components · App Bridge: https://shopify.dev/docs/api/app-bridge
- Requisitos de la App Store: https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements
