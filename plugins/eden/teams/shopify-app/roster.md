# Roster Shopify App — el equipo

Líder: **`/eden:shopify-app`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`)
`eden:shopify-app-*`. Reglas del stack: `rules/shopify-app/eden-shopify-app-rules.md`. Contrato común:
`rules/eden-team-rules.md`.

> **Una app de Shopify no es un tema.** El tema de una tienda es del stack `shopify` y de su equipo
> (`teams/shopify/roster.md`); una app se instala en **muchas tiendas** de comerciantes, tiene su propio
> servidor, su base de datos y sus extensiones, y lo que se libera llega a todas a la vez.
>
> **Si el dev tiene instalado el plugin `smg-shopify-app`**, su skill `shopify-app-rules` y su agente
> `webhook-builder` son material de referencia válido: se consultan, y ante una contradicción mandan la
> documentación vigente de Shopify y las convenciones del proyecto.

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:shopify-app-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe: quién usa la ruta, el webhook, la consulta o la extensión |
| `architect` | `eden:shopify-app-architect` (modo `audit` / `decide`) | Onboarding de una app avanzada; decidir el escalón reuse-first (¿lo resuelve una extensión, una función, la API?) |
| `design-extractor` | `eden:figma-extractor` | Pantallas del admin o extensiones con diseño (caché de diseño primero) |
| `design-system` | `eden:shopify-app-admin-dev` | En apps embebidas el sistema es **Polaris**: los fundamentos se mapean a sus componentes, no se crea un sistema paralelo |
| `implementer` | `eden:shopify-app-admin-dev` / `eden:shopify-app-backend-dev` / `eden:shopify-app-extension-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:shopify-app-backend-dev` | Admin GraphQL, sesiones y autenticación, webhooks, facturación, base de datos de la app, app proxy |
| `tester` | `eden:shopify-app-tester` | Tests primero: rutas y loaders/actions, verificación de webhooks (HMAC), funciones, extensiones |
| `devops` | `eden:shopify-app-devops` | Shopify CLI, `shopify.app*.toml`, entornos, tienda de desarrollo, base de datos local, CI. **Nunca libera una versión** |
| `design-auditor` | `eden:design-auditor` | Loop medir → corregir → medir contra Figma |
| `reviewer` | `eden:shopify-app-qa-reviewer` | Revisión del diff + lint, typecheck, tests, build y validación de GraphQL |
| `quality-auditor` | `eden:shopify-app-qa-reviewer` (modo `quality`) | Rendimiento (impacto en la tienda, tiempos del admin), accesibilidad, requisitos de la App Store |
| `security-auditor` | `eden:security-auditor` | HMAC, sesiones, scopes mínimos, datos protegidos de clientes, secretos; lee el módulo de apps |

## Propiedad de archivos (quién escribe qué)

Rutas habituales de la plantilla de React Router; **manda la estructura real del proyecto**.

| Archivos | Dueño |
|---|---|
| Rutas del admin embebido (`app/routes/app.*.tsx`): la UI, los componentes, el uso de Polaris y App Bridge | `eden:shopify-app-admin-dev` |
| `loader`/`action` de esas rutas, servicios del servidor, consultas y mutaciones de Admin GraphQL, `app/shopify.server.*`, sesiones | `eden:shopify-app-backend-dev` |
| Rutas de webhooks (`app/routes/webhooks.*`), facturación, app proxy, esquema de la base de datos de la app (`prisma/schema.prisma`) y sus migraciones | `eden:shopify-app-backend-dev` |
| Extensiones (`extensions/**`): theme app extensions, checkout UI, customer account UI, admin UI, Shopify Functions, web pixels | `eden:shopify-app-extension-dev` |
| Tests y fixtures (incluidos los payloads de webhooks de ejemplo) | `eden:shopify-app-tester` |
| `package.json`, lockfile, `tsconfig*`, `eslint.config.*`, `vite.config.*`, `.env.example`, `Dockerfile`, `.github/` | `eden:shopify-app-devops` |
| `shopify.app*.toml` (scopes, URLs, suscripciones de webhooks, app proxy, versión de la API) | **Líder decide** — cambia lo que la app pide a cada tienda. Los scopes nuevos, siempre con el sí del dev |
| Credenciales (`SHOPIFY_API_SECRET`, tokens, `.env` con valores) | **Nadie** — los gestiona el dev; el kit solo mantiene `.env.example` sin valores |

Si una unidad cruza dueños, el líder la parte (tester → backend-dev → admin-dev o extension-dev). Nunca
dos agentes sobre el mismo archivo en paralelo.

## Prohibiciones — no negociables

| Nunca | Por qué |
|---|---|
| `shopify app deploy` / `shopify app release` sin el sí explícito del dev en el momento | **Crea y libera una versión de la app para todas las tiendas que la tienen instalada** |
| Desplegar el servidor de la app (cualquier proveedor) | El deploy lo hace el dev |
| Instalar la app, crear datos o cambiar configuración en una **tienda real** de un comerciante | Es la tienda de otro; solo tiendas de desarrollo |
| Añadir scopes sin el sí del dev | Cada tienda tendrá que aprobarlos; pedir de más es motivo de rechazo en la App Store |
| Ejecutar mutaciones de Admin GraphQL contra una tienda que no sea de desarrollo | Cambia la tienda de un comerciante |
| Commitear secretos de la app o tokens de acceso, o registrarlos en logs | Dan acceso a todas las tiendas |
| Agregar, quitar o actualizar dependencias sin el sí del dev | Código de terceros que corre con acceso a tiendas |
| Cambiar la versión de la Admin API, del CLI o de la plantilla como parte de otra tarea | Una migración de versión es una tarea propia |

Sin riesgo y sin autorización: `install` con el lockfile, `lint`, `typecheck`, `test`, `build`,
`shopify app info`, `shopify app versions list`, y `shopify app dev` **contra una tienda de desarrollo**
declarada en el encargo (el dev confirma la primera vez, porque actualiza la configuración de la app en
desarrollo).

## Formato de handoff (todos los especialistas)

```
🧩 {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {tests, lint, typecheck, build, GraphQL validado, en la tienda de desarrollo… con el resultado real}
No verificado: {qué y por qué}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

| Fase | Especialistas |
|---|---|
| 1. Discovery | architect, design-extractor |
| 2. Setup | devops (`/eden:shopify-app-setup`) |
| 3. Build | tester (primero) → backend-dev → admin-dev / extension-dev, con design-auditor en loop |
| 4. QA | reviewer, quality-auditor, security-auditor |
| 5. Versión | devops prepara (`/eden:shopify-app-deploy`); **el dev libera** |
