# Sabor: SPA — React con Vite

React que corre **solo en el navegador**: Vite como herramienta de build y un router en el cliente
(React Router casi siempre). No hay servidor propio: los datos vienen de una API externa, y **todo lo
que está en el código llega al navegador**.

## Estructura habitual

```
src/
├── main.tsx            punto de entrada: createRoot, providers, router
├── App.tsx             (o routes.tsx / el archivo de rutas del router)
├── components/         UI reutilizable
├── features/ · pages/ · routes/   pantallas y su lógica, según el proyecto
├── hooks/  · lib/      hooks de datos, clientes de API, utilidades
├── styles/             tokens y estilos globales
└── test/               setup de tests (o junto a cada componente)
vite.config.ts · tsconfig*.json · eslint.config.js · vitest.config.ts (o dentro de vite.config)
```

**Manda la estructura real del proyecto.** Si organiza por features, se crea por feature.

## Vite

- **Proyecto nuevo:** `npm create vite@latest {nombre} -- --template react-ts` (o la plantilla con
  React Compiler, `react-compiler-ts`, si el dev la elige). Comprobar antes la versión mínima de Node en
  la doc vigente.
- `vite.config.*` es del rol `devops`. Alias de imports en Vite **y** en `tsconfig` a la vez, o el
  editor y el build no coinciden.
- **Variables de entorno:** solo las que empiezan por `VITE_` llegan al código, **y llegan al
  navegador**. En una SPA no existe un lugar "seguro" para un secreto: si hace falta uno, hace falta un
  back-end (o un proxy del back-end), y eso se dice al dev.
- `vite build` + `vite preview` para comprobar el build de producción en local.

## Router

React Router es el más común. **Verifica la versión instalada**: en la versión mayor actual se importa
todo desde `react-router` (el paquete `react-router-dom` dejó de existir), y hay tres modos:

| Modo | Cómo se reconoce | Dónde van los datos |
|---|---|---|
| **Declarativo** | `<BrowserRouter>` + `<Routes>` | En los componentes, con la librería de datos del proyecto |
| **Data** | `createBrowserRouter` + `<RouterProvider>` | `loader` / `action` por ruta |
| **Framework** | plugin de Vite, `routes.ts`, tipos `Route.*` | `loader` / `action` del módulo de ruta (puede tener SSR: entonces es casi otro sabor, y se declara) |

Se sigue el modo que use el proyecto; **no se migra de modo como parte de otra tarea**.

- Rutas con **carga diferida** (`lazy`) para lo que no es la pantalla inicial.
- Cada ruta tiene su **estado de error** (`errorElement` / `ErrorBoundary`) y su **404**.
- Las rutas protegidas lo son en la UI **y en la API**: ocultar una ruta en el cliente no protege
  nada.

## Datos

- **Sin servidor propio, todo pedido sale del navegador:** la autorización real vive en la API.
- Fetch con la librería del proyecto (TanStack Query, SWR, RTK Query) o con los `loader` del router en
  modo data/framework. No `useEffect` + `fetch` a mano en código nuevo.
- Tokens de sesión: lo que proponga la API (cookies `HttpOnly` si es posible); `localStorage` para un
  token es Media en seguridad y se reporta.

## SEO y metadata

Una SPA pura renderiza en el cliente: los buscadores la ven peor. Si el proyecto depende del tráfico
orgánico, **se le dice al dev** (las opciones son prerender, el modo framework con SSR, o Next.js) en
vez de prometer un SEO que la plataforma no da. Dentro de la SPA: `<title>` y `<meta>` por ruta (React
19 los eleva solos al `<head>`).

## Tests

Vitest + Testing Library con `jsdom` (o `happy-dom`) y `@testing-library/jest-dom`; Playwright para
e2e contra `vite preview`.

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} run test && {pm} run build
```

Y en el navegador: sin errores de consola, sin peticiones fallidas y la navegación entre rutas sin
recargar la página.
