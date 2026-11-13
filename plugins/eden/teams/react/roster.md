# Roster React — el equipo

Líder: **`/eden:react`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`) `eden:react-*`.
Reglas del stack: `rules/react/eden-react-rules.md` y el sabor del proyecto (`rules/react/flavors/spa.md`
o `rules/react/flavors/next.md`). Contrato común: `rules/eden-team-rules.md`.

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:react-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe: quién importa el componente, el hook o la ruta |
| `architect` | `eden:react-architect` (modo `audit` / `decide`) | Onboarding de un proyecto avanzado; decidir el escalón reuse-first y dónde vive cada cosa |
| `design-extractor` | `eden:figma-extractor` | Todo trabajo visual con Figma (caché de diseño primero) |
| `design-system` | `eden:react-ui-dev` | Fundamentos: tokens en el sistema de estilos del proyecto (CSS variables, Tailwind theme, CSS-in-JS) |
| `implementer` | `eden:react-ui-dev` / `eden:react-data-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:react-data-dev` | Estado, fetching, clientes de API, formularios con validación; en Next, Server Actions y route handlers |
| `tester` | `eden:react-tester` | Tests primero: unitarios y de componente (Vitest/Jest + Testing Library) y e2e (Playwright) |
| `devops` | `eden:react-devops` | Setup, gestor de paquetes, TypeScript, ESLint, scripts, variables de entorno, CI, configuración de build y deploy |
| `design-auditor` | `eden:design-auditor` | Loop medir → corregir → medir contra Figma |
| `reviewer` | `eden:react-qa-reviewer` | Revisión del diff + lint, type-check, tests y build en verde |
| `quality-auditor` | `eden:react-qa-reviewer` (modo `quality`) | Core Web Vitals, accesibilidad, SEO (en Next: metadata, SSR/SSG) |
| `security-auditor` | `eden:security-auditor` | XSS, secretos en el bundle, Server Actions sin auth, dependencias; lee el módulo React |

`migrator` no aplica: mover datos es del back-end del proyecto. Si una tarea lo necesita, lo hace el
líder o el dev, y se declara.

## Propiedad de archivos (quién escribe qué)

Las rutas son las habituales; **manda la estructura real del proyecto** (`src/`, `app/`, `components/`,
`features/`…). El `react-architect` la confirma en el inventario y el líder asigna por equivalencia.

| Archivos | Dueño |
|---|---|
| Componentes de UI (`*.tsx`/`*.jsx` que renderizan), sus estilos (CSS Modules, Tailwind, `*.css`), iconos y assets de la UI | `eden:react-ui-dev` |
| En Next: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx` (la parte que renderiza) | `eden:react-ui-dev` |
| Tokens del sistema de estilos (`tailwind.config.*` / `@theme`, archivo de CSS variables, theme de la librería de UI) | `eden:react-ui-dev`, solo con el encargo de `create-fundaments` o el sí del dev (es global) |
| Hooks de datos y estado (`use*.ts` que no renderizan), stores (Zustand, Redux, Context de datos), clientes de API, esquemas de validación (Zod…) | `eden:react-data-dev` |
| En Next: Server Actions (`'use server'`), route handlers (`route.ts`), `generateMetadata`/`generateStaticParams` con datos, utilidades `server-only` | `eden:react-data-dev` |
| Tests: `*.test.*`, `*.spec.*`, `__tests__/`, `e2e/`, `tests/`, fixtures y mocks de tests | `eden:react-tester` |
| `package.json` (scripts y dependencias), lockfile, `tsconfig*.json`, `eslint.config.*`, `vite.config.*`, `next.config.*`, `vitest.config.*`, `playwright.config.*`, `.env.example`, `.github/`, `Dockerfile` | `eden:react-devops` |
| Middleware / proxy de Next (`middleware.ts` o `proxy.ts`), `instrumentation.ts` | **Líder decide** — afecta a todas las rutas. Se asigna con encargo explícito |
| `.env*` con valores reales | **Nadie** — los secretos los pone el dev; el kit solo mantiene `.env.example` sin valores |

Si una unidad cruza dueños, el líder la parte en unidades secuenciales (por ejemplo: el `tester`
escribe el test → `data-dev` el hook → `ui-dev` el componente). Nunca dos agentes sobre el mismo
archivo en paralelo.

## Prohibiciones — no negociables

Ningún agente ni el líder las rompe, aunque el encargo lo pida:

| Nunca | Por qué |
|---|---|
| Desplegar (`vercel deploy`, `netlify deploy`, `firebase deploy`, push a la rama que despliega…) | El deploy lo hace el dev |
| Agregar, quitar o actualizar una dependencia sin el sí del dev | Es código de terceros en el proyecto del cliente |
| Escribir secretos en el código, en `.env.example` o en una variable con prefijo público (`NEXT_PUBLIC_`, `VITE_`) | Lo que lleva ese prefijo llega al navegador |
| Desactivar una regla de ESLint, un check de TypeScript (`any`, `@ts-ignore`) o un test para que pase | Se arregla la causa |
| Cambiar la versión mayor de React, Next, Vite o React Router como parte de otra tarea | Una migración es una tarea propia, con su plan |

Sin riesgo y sin autorización: `install` con el lockfile tal cual (`npm ci`, `pnpm install --frozen-lockfile`),
`lint`, `typecheck`, `test`, `build`, `dev` en local.

## Formato de handoff (todos los especialistas)

```
⚛️ {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {lint, typecheck, tests, build, render… con el resultado real}
No verificado: {qué y por qué}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

| Fase | Especialistas |
|---|---|
| 1. Discovery | architect, design-extractor |
| 2. Setup | devops (`/eden:react-setup`) |
| 3. Fundamentos | design-extractor → ui-dev (`create-fundaments`) |
| 4. Mapa | architect (`create-sitemap`: rutas ↔ nodos de Figma) |
| 5. Build | tester (primero) → data-dev → ui-dev, con design-auditor en loop |
| 6. QA | reviewer, quality-auditor, design-auditor, security-auditor |
| 7. Entrega | `turnoff-task`. El deploy lo hace el dev |
