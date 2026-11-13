# Módulo React — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-design`,
`eden-code-style`, `eden-quality`, `eden-testing`, `eden-security`). Aquí solo va lo que es propio de
React. Lo de cada sabor vive en `flavors/`:

| Sabor | Archivo | Qué es |
|---|---|---|
| **SPA** | `flavors/spa.md` | React en el navegador con Vite y un router (React Router u otro). Sin servidor propio |
| **Next.js** | `flavors/next.md` | React con servidor: App Router, Server Components, Server Actions, route handlers |

El sabor se declara en `.claude/project-config.json` → `react.flavor` (lo escribe `/eden:react-setup`) o
lo detecta `scripts/eden_stack.py detect`. **Si no está claro, se pregunta antes de escribir código**:
lo que en Next es un Server Component, en una SPA es un error.

> **La realidad del proyecto manda.** Este módulo dice la buena práctica; si el proyecto hace algo
> distinto y coherente (otra librería de estado, otra estructura), se sigue el proyecto y, si importa,
> se comenta una vez.

---

## Versiones — se verifican, no se recuerdan

React, Next, Vite y React Router cambian de API entre versiones mayores (y a veces menores). **Antes de
usar una API que no sea trivial, se comprueba con context7 contra la versión instalada** en
`package.json`/lockfile, no contra la memoria.

Referencia **verificada el 2026-10-22** (puede haber cambiado; es un punto de partida, no una verdad):

| Herramienta | Versión | Lo que más importa |
|---|---|---|
| React | 19.3 | `ref` como prop (`forwardRef` innecesario), `use`, `useActionState`, `useOptimistic`, `<Activity>`, `useEffectEvent`, `<ViewTransition>` |
| React Compiler | 1.0 (estable) | Memoiza solo; no viene activado por defecto |
| Next.js | 16.4 | App Router, Turbopack por defecto, `proxy.ts`, Cache Components, APIs de petición asíncronas, sin `next lint` |
| Vite | 8 | Rolldown como bundler; Node 20.19+ o 22.12+ |
| React Router | 8 (7 mantenido) | Paquete único `react-router` (`react-router-dom` eliminado); modos declarativo, data y framework |
| Vitest | 5 | Con Testing Library; Browser Mode disponible |
| ESLint | 10 | Flat config (`eslint.config.*`) |
| TypeScript | 7 | Compilador nativo; Next exige ≥ 5.1 |

---

## Componentes

- **Componentes de función**, uno por responsabilidad. Si un componente crece, se compone de otros; no
  se le añaden ramas hasta que haga todo.
- **Props tipadas** (TypeScript si el proyecto lo usa) y **sin `any`**. Valores por defecto con
  parámetros por defecto, no con `defaultProps` (ya no existen en componentes de función).
- **`ref` como prop** en React 19; `forwardRef` solo si el proyecto aún está en React ≤ 18.
- **El estado vive en el nivel más bajo que lo necesita.** Lo que se puede calcular a partir de props o
  estado **se calcula en el render**, no se copia a otro estado ni se sincroniza con `useEffect`.
- **`useEffect` solo para sincronizar con algo externo** (suscripciones, APIs del navegador, librerías
  no React). Pedir datos, transformar datos o reaccionar a un evento del usuario no son efectos.
- **Claves estables en listas** (`key` del dato, nunca el índice si la lista cambia de orden).
- **Composición antes que configuración**: `children` y slots antes que un componente con 20 props
  booleanas.
- **Memoización:** si el proyecto usa React Compiler, no se añaden `useMemo`/`useCallback`/`memo` a
  mano salvo para corregir un caso medido. Sin compilador, solo donde hay un problema de rendimiento
  medido, no "por si acaso".

## Reuse-first en React

La escalera del núcleo, expresada aquí:

1. **Un componente que ya existe, tal cual**, con sus props actuales.
2. **Composición o variante**: componer componentes existentes, o una variante ya soportada (la prop
   `variant`, una clase del sistema de diseño).
3. **Una prop nueva con default neutro**: las instancias actuales se ven y se comportan igual. Antes,
   blast radius (`eden:react-architect`): quién importa el componente.
4. **Código mínimo acotado** al componente de la tarea.
5. **Componente nuevo**: último recurso, con su nombre, su carpeta y sus estilos propios.

Una librería de UI que ya está en el proyecto (shadcn, MUI, Chakra, Radix…) **es el escalón 1**: no se
reescribe un `Dialog` que la librería ya trae.

## Estilos y tokens

- Se usa **el sistema de estilos del proyecto** (CSS Modules, Tailwind, CSS-in-JS, la librería de UI) y
  **solo sus tokens**: variables CSS, el theme de Tailwind o el theme de la librería. Nada de hex, px
  de tipografía ni `font-family` sueltos (`eden-design-rules.md`).
- **Los fundamentos de diseño se integran en ese sistema** (`create-fundaments`): en Tailwind, en su
  theme/`@theme`; con CSS variables, en el archivo de tokens del proyecto; con una librería, en su
  theme. No se crea un sistema paralelo.
- Mobile-first, acotado al componente. Con CSS Modules o Tailwind no hace falta BEM; con CSS global, BEM
  acotado al bloque (`eden-code-style-rules.md`). Sin `!important` ni estilos inline para lo que el
  sistema cubre.

## Datos, estado y formularios

- **Se usa lo que el proyecto ya tiene** (TanStack Query, SWR, RTK Query, Zustand, Redux, Context). Una
  librería nueva es una dependencia nueva: se pregunta.
- **Estado del servidor ≠ estado de la UI.** Lo que viene de una API se cachea con la herramienta de
  datos; el estado local de UI, con `useState`/`useReducer`. No se duplica uno en el otro.
- **Formularios:** validación con el esquema del proyecto (Zod u otro) compartido entre cliente y
  servidor; errores accesibles (asociados al campo, anunciados); estados de envío, error y éxito. En
  React 19, `action` en el `<form>` y `useActionState` cuando el sabor lo aprovecha.
- **Estados completos:** carga, vacío, error y éxito existen y están diseñados. Un componente que solo
  pinta el caso feliz está a medias.

## Accesibilidad (WCAG AA)

- HTML semántico primero: `<button>` para acciones, `<a href>` para navegar, `<label>` en cada campo,
  encabezados en orden. Un `div` con `onClick` no es un botón.
- Todo interactivo usable con teclado y con **foco visible**. En modales y menús, el foco entra, queda
  atrapado mientras están abiertos y vuelve al disparador al cerrar (si la librería de UI lo resuelve,
  se usa la suya).
- `aria-*` solo cuando la semántica nativa no alcanza; actualizaciones dinámicas con `aria-live`.
- `prefers-reduced-motion` respetado en toda animación.

## Rendimiento

- **Imágenes** con dimensiones (evitan CLS), tamaños adecuados y carga diferida bajo el fold. En Next,
  `next/image`.
- **El bundle importa:** imports puntuales de librerías grandes, carga diferida (`lazy`, `next/dynamic`)
  de lo que no está en la primera vista, y nada de librerías enteras para una función.
- Listas largas virtualizadas si el proyecto ya tiene con qué. Se mide (Lighthouse, Web Vitals) antes de
  optimizar.

## Tests

Siguen `eden-testing-rules.md`: **el test se escribe antes** y debe fallar primero. Los escribe el rol
`tester` (`eden:react-tester`).

- **Unitarios y de componente:** el runner del proyecto (Vitest o Jest) con **Testing Library**:
  consultas por rol y nombre accesible, interacciones con `user-event`, sin detalles de implementación.
- **e2e:** Playwright (o el que tenga el proyecto) para flujos completos y, en Next, para los Server
  Components asíncronos (que las herramientas unitarias no cubren bien).
- **Visual 1:1 con Figma:** `test-visual` y `attention-detail`, como en cualquier stack.
- La puerta de `turnoff-task`: `lint`, `typecheck`, `test` y `build` en verde.

## Entorno y calidad del código

- **Gestor de paquetes:** el del lockfile que ya existe (`package-lock.json` → npm, `pnpm-lock.yaml` →
  pnpm, `yarn.lock` → yarn, `bun.lock` → bun). No se mezclan.
- **Versión de Node** fijada en el proyecto (`engines`, `.nvmrc` o `.node-version`).
- **TypeScript estricto** (`strict: true`). Un `any`, un `@ts-ignore` o un `eslint-disable` nuevo se
  justifica en el PR o no entra.
- **ESLint con flat config** y las reglas de hooks (`eslint-plugin-react-hooks`); en Next, con
  `eslint-config-next`. Prettier o Biome si el proyecto lo usa.
- **Scripts mínimos** que el kit usa para verificar: `dev`, `build`, `lint`, `typecheck`, `test`
  (`test:e2e` si hay Playwright). Si falta uno, se propone; no se inventa su resultado.

## Seguridad

Aplica `eden-security-rules.md` (principios, checklist y severidad). Lo propio de React:

| Severidad | En React |
|---|---|
| **Crítica** | Un secreto en el bundle del navegador (variable `NEXT_PUBLIC_`/`VITE_`, o importado en un componente cliente); una Server Action o route handler que escribe sin comprobar quién pide; versión de React/Next con una vulnerabilidad crítica conocida y parche disponible |
| **Alta** | `dangerouslySetInnerHTML` con HTML sin sanear (contenido de un CMS, del usuario, de una API); un open redirect con `redirect`/`router.push` hacia una URL de entrada; autorización solo en el middleware/proxy o en la UI |
| **Media** | Dependencia con CVE alta sin parche; tokens de sesión en `localStorage`; script de terceros sin `integrity` |
| **Baja** | Cabeceras de seguridad ausentes (CSP, `frame-ancestors`, `Referrer-Policy`) |

- **Lo que lleva prefijo público llega al navegador.** `NEXT_PUBLIC_*` y `VITE_*` se incrustan en el
  bundle al compilar: ahí van solo valores públicos.
- **HTML de terceros, saneado** (DOMPurify o equivalente) antes de `dangerouslySetInnerHTML`; mejor
  aún, renderizarlo como componentes.
- **Las dependencias se mantienen al día en seguridad.** En diciembre de 2025 se publicó una RCE
  crítica sin autenticación en React Server Components (CVE-2025-55182, y CVE-2025-66478 en Next.js), y
  en 2026 hubo más avisos críticos en Next.js. Un proyecto con una versión afectada **se reporta como
  Crítica** y se propone actualizar al parche (con el sí del dev, que es una dependencia).

## Blast radius en React

```bash
grep -rn "{Componente}\|{hook}\|{ruta}" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" .
```

Más los re-exports (`index.ts`), imports dinámicos, stories y tests. Si el proyecto tiene cerebro,
`graphify affected` sí entiende JS/TS y se suma al grep. Un provider, un layout raíz, un hook compartido
o el middleware/proxy tienen blast radius **de toda la app**: se declaran así en el plan.

## Documentación vigente

- React: https://react.dev · Compiler: https://react.dev/learn/react-compiler
- Next.js: https://nextjs.org/docs (y su guía de actualización y avisos de seguridad en https://nextjs.org/blog)
- Vite: https://vite.dev/guide · React Router: https://reactrouter.com
- Vitest: https://vitest.dev · Testing Library: https://testing-library.com · Playwright: https://playwright.dev
- ESLint: https://eslint.org · reglas de hooks: https://react.dev/reference/eslint-plugin-react-hooks
