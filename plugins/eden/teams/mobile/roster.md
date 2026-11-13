# Roster móvil — el equipo

Líder: **`/eden:mobile`** (skill, sesión principal). Especialistas: subagentes (nivel `fast`) `eden:mobile-*`.
Reglas del stack: `rules/mobile/eden-mobile-rules.md` y el sabor del proyecto
(`rules/mobile/flavors/react-native.md` o `rules/mobile/flavors/ionic.md`). Contrato común:
`rules/eden-team-rules.md`.

> **Una app móvil vive en dos mundos**: el código JS/TS que el equipo escribe y los proyectos nativos
> (iOS y Android) que firman, compilan y publican las tiendas. Este roster separa los dos, y **lo que
> llega a una tienda lo decide siempre el dev**.

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:mobile-architect` (modo `inventory` / `blast-radius`) | Antes de tocar algo que existe: quién usa la pantalla, el componente, el hook o el módulo nativo |
| `architect` | `eden:mobile-architect` (modo `audit` / `decide`) | Onboarding de una app avanzada; decidir el escalón reuse-first y dónde vive cada cosa |
| `design-extractor` | `eden:figma-extractor` | Todo trabajo visual con Figma (caché de diseño primero) |
| `design-system` | `eden:mobile-ui-dev` | Tokens en el theme del proyecto (StyleSheet/theme, Tamagui, NativeWind, variables CSS de Ionic) con `create-fundaments` |
| `implementer` | `eden:mobile-ui-dev` / `eden:mobile-native-dev` / `eden:mobile-data-dev` | Según la tabla de propiedad de abajo |
| `data` | `eden:mobile-data-dev` | Estado, fetching, clientes de API, almacenamiento local y seguro, sincronización offline |
| `tester` | `eden:mobile-tester` | Tests primero: unitarios y de componente (Jest/Vitest + Testing Library), e2e (Maestro, Detox, Playwright/Cypress en Ionic) |
| `devops` | `eden:mobile-devops` | Setup, versiones, configuración de la app, builds de desarrollo, firma, perfiles de build, CI. **Nunca publica** |
| `design-auditor` | `eden:design-auditor` | Loop medir → corregir → medir contra Figma (en Ionic, en el navegador; en React Native, con capturas del simulador y medidas del layout) |
| `reviewer` | `eden:mobile-qa-reviewer` | Revisión del diff + lint, typecheck, tests y doctor del framework |
| `quality-auditor` | `eden:mobile-qa-reviewer` (modo `quality`) | Rendimiento (listas, renders, arranque), accesibilidad, tamaño del bundle |
| `security-auditor` | `eden:security-auditor` | Secretos en el bundle, almacenamiento inseguro, deep links, WebView, permisos; lee el módulo móvil |

`migrator` no aplica: mover datos de usuarios es del back-end. Si una tarea lo necesita (migrar el
almacenamiento local entre versiones de la app), lo hace `mobile-data-dev` con encargo explícito.

## Propiedad de archivos (quién escribe qué)

**Manda la estructura real del proyecto** (`app/` de Expo Router, `src/screens`, `src/app` de Ionic…);
el `mobile-architect` la confirma y el líder asigna por equivalencia.

| Archivos | Dueño |
|---|---|
| Pantallas y rutas (`app/**` de Expo Router, `src/screens`, páginas de Ionic), componentes de UI, estilos, theme y tokens, assets de UI | `eden:mobile-ui-dev` |
| Navegación (layouts de Expo Router, stacks y tabs, rutas de Ionic) | `eden:mobile-ui-dev` |
| Hooks de datos, stores, clientes de API, esquemas de validación, almacenamiento local y seguro, caché offline | `eden:mobile-data-dev` |
| Módulos nativos y config plugins de Expo, plugins de Capacitor, código Swift/Kotlin/Java propio, permisos y su texto (`Info.plist`, `AndroidManifest.xml`, entradas de permisos en `app.json`) | `eden:mobile-native-dev` |
| Tests: `*.test.*`, `__tests__/`, `e2e/`, flujos de Maestro (`.maestro/`), fixtures | `eden:mobile-tester` |
| `package.json`, lockfile, `tsconfig*`, `eslint.config.*`, `babel.config.*`/`metro.config.*`, `app.json`/`app.config.*` (salvo permisos), `eas.json`, `capacitor.config.*`, `ionic.config.json`, `.env.example`, `.github/` | `eden:mobile-devops` |
| Identificadores de la app (bundle id, package name), versión y número de build, iconos y splash, esquemas de deep links | **Líder decide** — afectan a la tienda y a los usuarios existentes. Con el sí del dev |
| Credenciales de firma (keystores, certificados, perfiles, contraseñas), `google-services.json` / `GoogleService-Info.plist` reales, `.env` con valores | **Nadie** — los gestiona el dev (o EAS credentials con su sesión); nunca en el repo |

Si una unidad cruza dueños, el líder la parte en unidades secuenciales (tester → data-dev → native-dev
→ ui-dev). Nunca dos agentes sobre el mismo archivo en paralelo.

## Prohibiciones — no negociables

| Nunca | Por qué |
|---|---|
| Publicar en una tienda (`eas submit`, `fastlane deliver/supply`, subir a TestFlight o a Play Console) | Lo publica el dev |
| Enviar una actualización OTA a usuarios reales (`eas update` a un canal de producción, Capgo/Appflow live updates) | Cambia la app de usuarios reales sin revisión de tienda |
| Lanzar builds en la nube que gastan cuota o firman con credenciales de producción sin el sí del dev | Cuesta dinero y usa la identidad del cliente |
| Cambiar el bundle id, el package name o el esquema de deep links de una app publicada | Rompe la app instalada y las actualizaciones |
| Tocar credenciales de firma, o commitear keystores, certificados o archivos de servicios con claves | Es la identidad del cliente en la tienda |
| Agregar, quitar o actualizar dependencias o plugins nativos sin el sí del dev | Cambia el binario y puede romper la compilación nativa |
| Poner secretos en el código o en variables públicas (`EXPO_PUBLIC_*`, el bundle de Ionic) | Todo lo que va en la app se puede extraer |
| Cambiar la versión de React Native, del SDK de Expo, de Ionic o de Capacitor como parte de otra tarea | Una actualización es una tarea propia |

Sin riesgo y sin autorización: `install` con el lockfile, `lint`, `typecheck`, `test`, `expo-doctor`,
`npx cap doctor`, el servidor de desarrollo y builds **locales** de desarrollo en simulador o emulador.

## Formato de handoff (todos los especialistas)

```
📱 {agente} · {unidad}
Estado: ✅ hecho | ⏸️ detenido en {punto} | ⛔ fuera de alcance | ❌ falló
Escalón reuse-first: {1–5} — {por qué no bastó el anterior}
Archivos: {ruta — creado|modificado — qué}
Verificado: {tests, lint, typecheck, doctor, build de desarrollo, simulador/emulador… con el resultado real}
No verificado: {qué y por qué — p.ej. "sin dispositivo iOS"}
DECISIÓN PENDIENTE: {pregunta exacta — o "ninguna"}
Para el siguiente: {rol → qué necesita saber}
```

## Fases del ciclo y quién trabaja en cada una

| Fase | Especialistas |
|---|---|
| 1. Discovery | architect, design-extractor |
| 2. Setup | devops (`/eden:mobile-setup`) |
| 3. Fundamentos | design-extractor → ui-dev (`create-fundaments`) |
| 4. Build | tester (primero) → data-dev → native-dev → ui-dev, con design-auditor en loop |
| 5. QA | reviewer, quality-auditor, design-auditor, security-auditor |
| 6. Release | devops prepara (`/eden:mobile-release`); **el dev publica** |
