# Sabor: Ionic con Capacitor

Una **app web** (Angular, React o Vue con los componentes de Ionic) que corre dentro de un **WebView**
nativo, con acceso al dispositivo por **plugins de Capacitor**. Todo lo de la web aplica (accesibilidad,
rendimiento, seguridad de la salida), más lo que añade vivir dentro de un WebView. Verificado para
**Ionic 9 y Capacitor 8** (2026-10-22).

## Estructura

```
src/                    la app web (estructura de Angular, React o Vue)
├── app/ · pages/ · components/
└── theme/variables.css tokens de Ionic (colores, tipografía) — aquí van los fundamentos
capacitor.config.ts     appId, appName, webDir, servidor y plugins
ios/  android/          proyectos nativos: SON CÓDIGO FUENTE y se versionan
ionic.config.json
```

- **Las reglas del framework web aplican**: en Ionic React, `rules/react/` (§ Componentes, datos y
  accesibilidad); en Angular y Vue, sus convenciones y las del proyecto.
- Tokens en `theme/variables.css` y las variables de Ionic (`--ion-color-*`, `--ion-font-family`…): nada
  de colores sueltos.

## Ionic 9 — lo que hay que saber

- Angular 18–22 (21+ sin zone.js por defecto; `IonicModule` deprecado a favor de `provideIonicAngular()`),
  React 18+ con React Router 6, Vue 3.5+ con Vue Router 5.
- `ion-img` está deprecado: `<img loading="lazy">` nativo. `ion-picker-legacy` ya no existe.
- La migración entre mayores (`npx @ionic/migrate`) es una tarea propia.

## Capacitor 8

- Requisitos: Node ≥ 22, Xcode 26+, Android Studio 2025.2.1+. Por defecto: iOS 15.0, minSdk 24,
  targetSdk y compileSdk 36; iOS con Swift Package Manager.
- Flujo: `{pm} run build` → **`npx cap sync`** (copia la web y actualiza plugins nativos) →
  `npx cap open ios|android` o `npx cap run`. Tras añadir un plugin nativo, siempre `cap sync`.
- Los proyectos `ios/` y `android/` **se versionan y se revisan**: los cambios nativos (permisos,
  configuración) se hacen ahí y entran en el PR.
- Borde a borde: el ajuste de márgenes automático se eliminó; las áreas se manejan con las variables CSS
  `env(safe-area-inset-*)` y el plugin de barras del sistema.
- Plugins: los oficiales (`@capacitor/*`) primero; uno de la comunidad, con el sí del dev y comprobando
  que su mayor coincide con la de Capacitor.

## El WebView es la superficie de ataque

- **`server.allowNavigation` mínimo** (solo los dominios necesarios) y **CSP estricta** en el
  `index.html`. En octubre de 2026 se publicó un aviso **crítico** de Capacitor
  (GHSA-rvm3-566m-v7fv): la guarda de navegación del WebView comprobaba solo esquema y host, no la ruta,
  y permitía cargar contenido remoto en el origen de la app con acceso a `localStorage`, cookies y
  plugins. Corregido en 6.2.2, 7.6.9, 8.4.3 y 8.5.1: **una versión afectada es Crítica**.
- **Nunca `server.url` apuntando a un servidor de desarrollo en una build de producción** (el live reload
  es solo para desarrollo).
- Contenido de terceros o HTML del usuario, saneado; nada de `eval` ni de inyectar scripts.
- `@capacitor/preferences` **no es seguro** (texto plano): tokens y secretos, con un plugin de
  Keychain/Keystore.

## Tests

- Unitarios con el runner del framework y Testing Library; **e2e** con Playwright o Cypress contra el
  servidor web (rápido), y en dispositivo o emulador para los flujos que dependen de un plugin.
- Lighthouse y la auditoría de accesibilidad sobre la versión web, como en cualquier front.

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} test && {pm} run build
npx cap sync && npx cap doctor
npx cap run android              # en emulador (y ios en macOS)
```
