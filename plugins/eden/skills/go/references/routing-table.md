# Tabla de enrutamiento — `/eden:go`

Una fila por skill del kit. **Si agregas un skill al kit, agrega su fila en el mismo PR.** Un skill
sin fila no es enrutable.

Leyenda:

- **Modo**: 🟢 delegable · 🟡 delegable hasta la propuesta, luego en línea · 🔴 solo en línea.
- **Router**: el agente `eden-router-*` que lo ejecuta cuando es 🟢/🟡.
- **Plano**: `fg` primer plano (usa MCP, Playwright o lanza `eden-*`) · `bg` segundo plano (lectura
  local pura).
- Un mismo skill puede tener modos distintos según el sub-modo pedido (`run` vs `update`, `recall` vs
  `save`). Se enruta por el sub-modo.

---

## Líderes de stack — primero se enruta por stack

| Skill | Stack | Cuándo | Argumentos que arma | Modo |
|---|---|---|---|---|
| `/eden:shopify` | shopify | Proyecto nuevo, onboarding de un tema avanzado, o un trabajo de **varias unidades** que necesita al equipo (página completa, rediseño, feature con datos + tema + JS) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `shopify-setup` | shopify | "arranca el proyecto Shopify", sin `shopify.theme.toml` o sin bloque `shopify` en `project-config.json` | `[ruta] [\| tienda] [\| base y versión] [\| nuevo \| existente]` | 🔴 |
| `/eden:react` | react | Proyecto React o Next.js nuevo, onboarding de uno avanzado, o un trabajo de **varias unidades** (pantalla completa, feature con datos + UI + tests) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `/eden:php` | php | Proyecto PHP o Laravel nuevo, onboarding de uno avanzado, o un trabajo de **varias unidades** (funcionalidad con esquema + API + vistas) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `php-setup` | php | "arranca el proyecto Laravel/PHP", "levanta el entorno", sin `composer.json` o sin bloque `php` en `project-config.json` | `[ruta] [\| laravel \| php] [\| herd \| sail \| docker] [\| nuevo \| existente]` | 🔴 |
| `/eden:node` | node | Back-end Node (Express, NestJS o sin framework) nuevo, onboarding de uno avanzado, o un trabajo de **varias unidades** (recurso con esquema + endpoints + jobs) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `node-setup` | node | "arranca la API en Node/Nest/Express", "levanta el entorno del back", sin `package.json` o sin bloque `node` en `project-config.json` | `[ruta] [\| nest \| express \| node] [\| gestor] [\| nuevo \| existente]` | 🔴 |
| `/eden:mobile` | mobile | App móvil (React Native/Expo o Ionic) nueva, onboarding de una avanzada, o un trabajo de **varias unidades** (flujo de varias pantallas, pantalla + capacidad nativa) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `mobile-setup` | mobile | "arranca la app", "levanta el entorno móvil", Expo/React Native/Ionic sin proyecto o sin bloque `mobile` en `project-config.json` | `[ruta] [\| expo \| bare \| ionic-angular \| ionic-react \| ionic-vue] [\| nuevo \| existente]` | 🔴 |
| `/eden:shopify-app` | shopify-app | App de Shopify nueva, onboarding de una avanzada, o un trabajo de **varias unidades** (admin + webhook + extensión) | `new \| onboard \| task <url-ticket> \| <pedido>` | 🔴 |
| `shopify-app-setup` | shopify-app | "arranca la app de Shopify", "levanta el entorno de la app", sin `shopify.app.toml` o sin bloque `shopify_app` en `project-config.json` | `[ruta] [\| tienda de desarrollo] [\| nueva \| existente]` | 🔴 |
| `react-setup` | react | "arranca el proyecto React/Next", "levanta el entorno", sin `package.json` o sin bloque `react` en `project-config.json` | `[ruta] [\| spa \| next] [\| gestor] [\| nuevo \| existente]` | 🔴 |

El stack se detecta con `scripts/eden_stack.py detect` (ver `rules/eden-stack-rules.md`). Un stack sin
líder ni skills propios (🔜 en esa tabla) usa los skills del núcleo con el roster genérico, y se dice.

Regla: si el stack tiene líder y el pedido es de **una sola skill** (medir una sección, un `section-mod`
chico), se enruta directo a esa skill: igual usa el equipo del stack, porque las skills resuelven los
agentes por el roster (`rules/eden-team-rules.md`). El líder se propone cuando hay que **coordinar**.

## Ciclo de tarea

| Skill | Cuándo (señales del pedido) | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `ignition-task` | "arranca/empieza la tarea", URL de ticket (Asana, SMG Hub o ClickUp) + trabajo de varias partes, tarea nueva completa | `<url-ticket> [\| url-figma] [\| notas]` | 🔴 | — | — | (ella misma implementa) → `turnoff-task` |
| `turnoff-task` | "ya terminé", "cierra", "sube y abre el PR", checkpoint abierto y trabajo hecho | `[url-ticket] [\| notas]` | 🔴 | — | — | `time-report` si quedó tiempo sin cargar |
| `create-sitemap` | "qué hay que construir", "mapa de páginas/secciones", proyecto sin `docs/sitemap.md` | `[url-figma] [\| --refresh]` | 🟡 | `eden:router-design` | fg | `estimate-time` |
| `create-fundaments` | "design system", "tokens", "fundamentos", proyecto sin `docs/design-system.md` | `[url-figma] [\| --refresh]` | 🟡 | `eden:router-design` | fg | `create-sitemap` |

## Secciones y diseño

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `create-new-section` | "crea una sección nueva", UNA sección que no existe en el tema | `[url-ticket] [\| url-figma] [\| qué sección]` | 🔴 | — | — | `attention-detail` (lo encadena ella) |
| `section-mod` | "cambia/ajusta/arregla la sección X", la sección ya existe | `<sección> [\| url-ticket] [\| url-figma] [\| qué cambiar]` | 🔴 | — | — | `attention-detail` (lo encadena ella) |
| `figma-expert` | "implementa este nodo de Figma 1:1", foco en fidelidad más que en ticket | `<url-figma \| node-id> [\| url render] [\| sección]` | 🔴 (implementa) · 🟡 si solo piden extraer el Design Spec | `eden:router-design` | fg | `test-visual` |
| `download-figma-img` | "baja las imágenes/iconos del Figma", faltan assets | `[url-figma] [\| sección] [\| carpeta]` | 🟡 (hasta el inventario) | `eden:router-design` | fg | — |

## QA y tests

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `attention-detail` | "mide/compara esta sección con Figma", UNA sección | `<sección \| url> [\| url-figma] [\| breakpoints]` | 🟢 (sin exportar imágenes: eso se ofrece aparte) | `eden:router-qa` | fg | `section-mod` si hay deltas |
| `qa-pixel-perfect` | "QA de la página entera", "déjala 1:1", varias secciones | `<url-página> [\| url-figma] [\| sección]` | 🟡 (mide y clasifica; corregir va en línea) | `eden:router-qa` | fg | `turnoff-task` |
| `test-visual` `run` | "corre el test visual", ya hay baseline | `<sección> \| run [\| url]` | 🟢 | `eden:router-qa` | fg | — |
| `test-visual` `baseline` / `update` | "crea/actualiza el baseline" | `<sección> \| baseline \| update` | 🔴 (el baseline es el contrato: lo revisa el dev) | — | — | `test-visual run` |
| `test-code` `run` / `currency` | "corre los tests/linter/Theme Check", "¿esta API está vigente?" | `<qué> \| run \| currency` | 🟢 | `eden:router-qa` | fg | — |
| `test-code` `spec` | "escribe los tests primero" | `<qué> \| spec` | 🔴 | — | — | `test-code run` |
| `launch-check` | "antes/después de lanzar", "deploy a producción", garantía | `[url-prod] [\| pre \| post]` | 🟡 (informe; el sign-off del cliente lo confirma el dev) | `eden:router-qa` | fg | — |
| `security-check` `diff` / `section` / `project` / `secrets` / `deps` | "revisa la seguridad", "audita", "¿es seguro?", "blinda", "secretos", "vulnerabilidades", "dependencias" | `diff` (cambios de la rama) · `section <nombre>` · `project` (todo el repo) · `secrets` (historial) · `deps` (vulnerabilidades) | 🟢 (informe; corregir va en línea con el implementador) | `eden:router-qa` | fg | `section-mod` / `turnoff-task` si hay hallazgos |
| `antislop` `section` / `page` / `copy` / `code` / `contrast` | "slop", "se ve genérico", "parece hecho por IA", "revisa los textos", "revisa el copy", "comentarios de IA", "contraste" | `section <nombre>` · `page <url>` · `copy <archivos>` (textos) · `code <archivos>` (comentarios) · `contrast <hex> <hex>` | 🟢 (informe; corregir, solo con el sí del dev y vía el implementador) | `eden:router-qa` | fg | `section-mod` / `turnoff-task` si hay hallazgos |
| `pastel-sync` | "comentarios de Pastel", "QA del cliente", URL de Pastel | `[url-pastel \| comentarios] [\| url-ticket]` | 🔴 | — | — | `turnoff-task` |

## WordPress

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `wp-setup` | proyecto WP sin `wordpress.flavor`, "arranca el proyecto WP" | `[ruta] [\| sabor, entorno]` | 🔴 | — | — | `wp-local up` |
| `wp-local` `doctor` / WP-CLI de lectura | "pantalla blanca", "no se ve el cambio", "¿qué plugins hay?" | `doctor [\| síntoma]` · `wp {comando de lectura}` | 🟢 | `eden:router-wp` | fg | `wp-local` en línea para arreglar |
| `wp-local` `up` / `reset` / WP-CLI que escribe | "levanta el sitio", "resetea" | `up \| reset \| wp {…}` | 🔴 | — | — | — |
| `wp-import` | "baja producción", "importa contenido", "migra desde Shopify/Wix", "sube a staging" | `<from-prod \| content \| migrate \| to-staging> [\| origen y destino]` | 🔴 | — | — | `wp-local doctor` |
| `wp-feature` | "CPT", "taxonomía", "campo ACF", "endpoint", "WooCommerce" | `[url-ticket] [\| qué y dónde]` | 🔴 | — | — | `test-code` |

En WordPress, **sin sabor declarado la única ruta válida es `wp-setup`**, salvo `wp-local doctor`.

## React · Next.js

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `react-component` | "crea/modifica el componente X", un botón, una card, un modal; un componente con Figma | `<componente \| ruta> [\| url-figma \| url-ticket] [\| notas]` | 🔴 | — | — | `test-visual` / `turnoff-task` |
| `next-route` | "una página nueva", "la ruta /x", "un endpoint / route handler", "una Server Action" — proyecto Next | `<ruta> [\| page \| layout \| route \| action] [\| url-ticket \| url-figma]` | 🔴 | — | — | `security-check diff` |
| `react-data` | "conecta con la API", "el formulario de X", "el store", "carga los datos de", "caché/invalidación" | `<funcionalidad> [\| fuente] [\| url-ticket]` | 🔴 | — | — | `react-component` si falta la UI |

En React, **sin sabor claro (`spa` o `next`) la ruta es `react-setup`** (o confirmarlo con el dev):
`next-route` solo aplica a Next.

| Duda | Regla |
|---|---|
| `react-component` vs `create-new-section` | Proyecto React → `react-component`. `create-new-section` es para temas (Shopify, WordPress) |
| `next-route` vs `react-component` | Si el trabajo es la ruta (datos, metadata, caché, auth) → `next-route`. Si es una pieza de UI dentro de una ruta → `react-component` |
| `react-data` vs `next-route` | En Next, una Server Action o route handler **de una ruta concreta** → `next-route`. La capa de datos de una funcionalidad que cruza rutas → `react-data` |

## PHP · Laravel

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `laravel-feature` | "un CRUD de X", "la funcionalidad de pedidos", modelo + migración + vistas, un formulario con su lógica — proyecto Laravel | `<funcionalidad> [\| url-ticket \| url-figma] [\| qué NO tocar]` | 🔴 | — | — | `security-check diff` |
| `laravel-api` | "un endpoint", "la API de X", "lo que consume el front/la app", Sanctum, Resources | `<recurso o endpoint> [\| url-ticket] [\| consumidores]` | 🔴 | — | — | `react-data` si la consume el front |

En PHP, **WordPress no entra aquí** (es su propio stack), y sin sabor claro (`php` o `laravel`) la ruta
es `php-setup`. Los skills `laravel-*` solo aplican al sabor `laravel`; en PHP sin framework, el trabajo
lo coordina `/eden:php`.

| Duda | Regla |
|---|---|
| `laravel-feature` vs `laravel-api` | Con vistas (Blade, Livewire, Inertia) → `laravel-feature`. Solo endpoints para otro consumidor → `laravel-api` |
| `laravel-api` vs `react-data` | El endpoint en el back → `laravel-api`. Consumirlo desde el front React → `react-data` |

## Node · Express · NestJS

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `node-api` | "un endpoint", "la API de X", "una ruta de Express", "un módulo/controlador de Nest", lo que consume el front o la app | `<recurso o endpoint> [\| url-ticket] [\| consumidores]` | 🔴 | — | — | `security-check diff` · `react-data` si la consume el front |
| `node-data` | "el esquema", "una tabla/colección", "la migración", Prisma/Drizzle/TypeORM/Mongoose, "un job", "una cola", "un worker" | `<entidad, cambio o job> [\| url-ticket] [\| datos existentes]` | 🔴 | — | — | `node-api` si hay endpoints que lo usan |

En Node, **Next.js no entra aquí** (es del stack `react`), y sin sabor claro (`node`, `express` o
`nest`) la ruta es `node-setup`.

| Duda | Regla |
|---|---|
| `node-api` vs `node-data` | El endpoint (validación, auth, contrato) → `node-api`. El esquema, la migración, el repositorio o la cola → `node-data` |
| `node-api` vs `next-route` | Back-end Node aparte → `node-api`. Un route handler o Server Action dentro de Next → `next-route` |

## Móvil · React Native · Ionic

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `mobile-screen` | "una pantalla", "la vista de X en la app", una pantalla con Figma | `<pantalla o ruta> [\| url-figma \| url-ticket] [\| plataformas]` | 🔴 | — | — | `test-visual` / `turnoff-task` |
| `mobile-native` | "la cámara", "notificaciones push", "ubicación", "biometría", "un plugin de Capacitor", "un módulo nativo" | `<capacidad> [\| url-ticket] [\| plataformas]` | 🔴 | — | — | `mobile-release` cuando toque (exige binario nuevo) |
| `mobile-release` | "prepara la versión", "sube a la tienda", "TestFlight", "Play Console", "una OTA" | `[versión] [\| binario \| ota] [\| plataformas]` | 🔴 (prepara; **publica el dev**) | — | — | — |

En móvil, **publicar o enviar una OTA a producción nunca lo hace el kit**: `mobile-release` lo deja listo
y el dev ejecuta los comandos.

| Duda | Regla |
|---|---|
| `mobile-screen` vs `react-component` | App de React Native o Ionic → `mobile-screen` (y sus componentes). Web React → `react-component` |
| `mobile-screen` vs `mobile-native` | La pantalla y su UI → `mobile-screen`. La capacidad del dispositivo (permisos, módulo o plugin) → `mobile-native` |

## Apps de Shopify

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `shopify-app-admin` | "una pantalla de la app", "la configuración en el admin", Polaris, App Bridge, una lista o un formulario de la app | `<pantalla o funcionalidad> [\| url-figma \| url-ticket]` | 🔴 | — | — | `security-check diff` |
| `shopify-app-extension` | "un app block", "un app embed", "una extensión de checkout", "una Shopify Function", "un descuento", "un web pixel" | `<qué extensión> [\| superficie] [\| url-ticket]` | 🔴 | — | — | `shopify-app-deploy` (exige liberar versión) |
| `shopify-app-webhook` | "un webhook", "cuando se cree un pedido…", "app/uninstalled", "los webhooks de GDPR/cumplimiento" | `<tema> [\| qué debe hacer] [\| url-ticket]` | 🔴 | — | — | `security-check diff` |
| `shopify-app-deploy` | "libera la app", "deploy de la app", "nueva versión", "a la App Store" | `[entorno] [\| notas]` | 🔴 (prepara; **libera el dev**) | — | — | — |

En apps, **`shopify app deploy`/`release` nunca lo ejecuta el kit**: libera para todas las tiendas.

| Duda | Regla |
|---|---|
| `shopify-app-extension` vs `create-new-section` | Un app block o app embed de **una app** → `shopify-app-extension`. Una sección del **tema** de una tienda → `create-new-section` (equipo Shopify) |
| `shopify-app-*` vs `/eden:shopify` | Hay `shopify.app.toml` → apps. Hay `sections/` + `config/settings_schema.json` → tema |

## Tiempo y reportes

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `mydaily` | "mi daily", "reporte del día", "qué hice ayer" | `[fecha] [\| notas]` | 🟢 (los huecos quedan como `{?}` en vez de preguntar) | `eden:router-knowledge` | fg | `time-report` si detecta tiempo sin cargar |
| `estimate-time` | "cuánto tarda", "estima la tarea" | `<url-ticket> [\| contexto]` | 🟡 (hasta la tabla; cargar el tiempo en el tracker va en línea) | `eden:router-knowledge` | fg | — |
| `time-report` | "carga/registra las horas" | `[url-ticket] [\| duración] [\| fecha]` | 🔴 | — | — | — |

## Memoria, cerebro y contexto

| Skill | Cuándo | Argumentos que arma | Modo | Router | Plano | Después conviene |
|---|---|---|---|---|---|---|
| `/eden:memory` `recall` / `status` | "¿esto ya nos pasó?", "qué sabemos de X" | `recall <tema> \| status` | 🟢 | `eden:router-knowledge` | bg | — |
| `/eden:memory` `save` / `consolidate` / `promote` | "guarda esto", "consolida", "súbelo a global" | `save \| consolidate \| promote` | 🔴 | — | — | — |
| `/eden:brain` `query` / `affected` / `status` / `doctor` | "¿quién usa X?", "blast radius", "¿el grafo está al día?" | `query <pregunta> \| affected <qué> \| status \| doctor` | 🟢 (`doctor` reporta, no reaplica) | `eden:router-knowledge` | bg | `/eden:brain build` en línea si está viejo |
| `/eden:brain` `init` / `build` / `note` / `sync` / `promote` / `open` | "crea el cerebro", "reconstruye el grafo" | `init \| build \| …` | 🔴 | — | — | — |
| `/eden:context` `index` / `status` / `load` | "qué hay descargado", "recupera el spec del hero" | `index \| status \| load <archivo>` | 🟢 | `eden:router-knowledge` | bg | — |
| `/eden:context` `offload` / `close` | "descarga el contexto", "limpia al cerrar" | `offload \| close` | 🔴 (tocan el contexto de la sesión principal) | — | — | — |

## Enrutador

| Skill | Cuándo | Modo |
|---|---|---|
| `eden` | El dev lo invoca por su nombre | 🔴 — es la sesión principal decidiendo |

---

## Desempates frecuentes

| Duda | Regla |
|---|---|
| `section-mod` vs `create-new-section` | ¿Existe ya un archivo de sección que se parezca? → `section-mod`. Aunque se "sienta nueva", la escalera reuse-first empieza por modificar |
| `section-mod` vs `ignition-task` | Una sección y sin subtareas → `section-mod`. Varias secciones, subtareas o un ticket con fases → `ignition-task` |
| `figma-expert` vs `create-new-section` | Hay ticket y es una sección del tema → `create-new-section`. Solo hay un nodo de Figma y el foco es la fidelidad → `figma-expert` |
| `attention-detail` vs `qa-pixel-perfect` | Una sección → `attention-detail` (mide). Página entera o "déjala 1:1" → `qa-pixel-perfect` (mide y corrige) |
| `test-visual` vs `attention-detail` | Hay baseline versionado y se quiere rojo/verde → `test-visual run`. Se quiere el diagnóstico en profundidad → `attention-detail` |
| `security-check` modo | Lo que cambió en la rama → `diff`. Una sección concreta → `section`. "Todo el sitio" o antes de lanzar → `project` (lo hace `launch-check`). "¿Se filtró una clave?" → `secrets`. "¿Hay librerías vulnerables?" → `deps` |
| `antislop` modo | Una sección o componente → `section`. Una página en el render real → `page`. "Revisa los textos/copy" → `copy`. "Comentarios de IA" → `code`. "¿Pasa contraste?" con dos colores → `contrast` |
| `turnoff-task` vs `pastel-sync` | Hay comentarios de Pastel abiertos → `pastel-sync` primero; `turnoff-task` cuando no queda ninguno |
