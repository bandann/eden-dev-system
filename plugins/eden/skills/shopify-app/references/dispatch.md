# Dispatch — cómo reparte el líder de apps de Shopify

## 1. Partir en unidades

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Un campo más en una pantalla, un ajuste en una consulta | Un especialista (+ su test) |
| **M** | Una pantalla del admin con su loader/action, un webhook, una extensión | tester → backend-dev → admin-dev o extension-dev |
| **L** | Una funcionalidad con admin + webhook + extensión | Varias unidades M con dependencias |
| **XL** | Una app nueva o un módulo entero | Lotes L por funcionalidad |

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa, si exige liberar versión | `eden:shopify-app-architect` |
| UI del admin embebido: Polaris, App Bridge | `eden:shopify-app-admin-dev` |
| Loaders/actions, Admin GraphQL, sesiones, webhooks, facturación, app proxy, base de datos | `eden:shopify-app-backend-dev` |
| Theme app extensions, checkout/customer account UI, admin UI extensions, Functions, web pixels | `eden:shopify-app-extension-dev` |
| Tests (primero) | `eden:shopify-app-tester` |
| CLI, entorno, configuraciones por entorno, CI, preparar versión | `eden:shopify-app-devops` |
| Figma → Design Spec · medir | `eden:figma-extractor` · `eden:design-auditor` |
| Revisar el diff; calidad | `eden:shopify-app-qa-reviewer` |
| Seguridad independiente | `eden:security-auditor` |

`shopify.app*.toml` (scopes, URLs, suscripciones, versión de la API): lo decide el líder con el sí del dev.

## 3. Plantilla del plan (al dev, en español)

```
🧩 PLAN DEL EQUIPO SHOPIFY APP

Trabajo: {new | onboard | task} · {ticket / descripción} · plantilla {x} · Admin API {v}
Rama: {nombre} desde {base — preguntada}
Tienda de desarrollo: {x}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | Tests de {x} | S | eden:shopify-app-tester | … | — | — |
| 2 | Loader + mutación | S | eden:shopify-app-backend-dev | app/routes/app.x.tsx (loader/action) | 3 | 1 |
| 3 | Pantalla | M | eden:shopify-app-admin-dev | app/routes/app.x.tsx (UI) | 2 — Polaris | 1, 2 |

Scopes: {sin cambios | nuevos: read_x — ⚠️ cada tienda tendrá que aprobarlo}
Versión de la app: {liberar — por TOML/extensiones | solo servidor}
🛡️ Superficie: entra {admin, webhooks, app proxy} · verificado {sesión, HMAC, firma} · datos de clientes {…} · secretos {…}
Cumplimiento: {webhooks obligatorios ✅ | n/a — app privada}
Paro a preguntarte en: {scopes, TOML, dependencias, shopify app dev la primera vez}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: template {x} · Admin API {v} (validate queries against this version) · Polaris {web components | React} ·
      dev store {x} · reuse step {n}: {why} · sibling pattern: {file} · tests to make green: {files}
ACCEPT WHEN: {tests + lint + typecheck + build green; GraphQL validated; works on the dev store if authorized}
DO NOT: touch other files; run shopify app deploy/release; deploy the server; touch real stores; add scopes;
        add/upgrade dependencies; log tokens or customer data; {unit-specific}
HANDOFF: teams/shopify-app/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

Solo unidades con **archivos disjuntos**, en un solo turno, como mucho 4 a la vez. Lo que toca
`shopify.app*.toml` o el esquema de la base va en secuencia.
