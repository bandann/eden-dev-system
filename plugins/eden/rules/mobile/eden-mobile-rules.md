# Módulo móvil — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow`, `eden-component-strategy`, `eden-design`,
`eden-code-style`, `eden-quality`, `eden-testing`, `eden-security`). Aquí solo va lo que es propio de una
app móvil. Lo de cada sabor vive en `flavors/`:

| Sabor | Archivo | Qué es |
|---|---|---|
| **React Native** | `flavors/react-native.md` | React Native con Expo (lo recomendado) o sin framework (bare): UI nativa escrita en React |
| **Ionic** | `flavors/ionic.md` | Ionic con Capacitor: una app web (Angular, React o Vue) dentro de un WebView, con acceso nativo por plugins |

El sabor se declara en `.claude/project-config.json` → `mobile.flavor` (lo escribe `/eden:mobile-setup`)
o lo detecta `scripts/eden_stack.py detect`. Si no está claro, se pregunta antes de escribir código.

> **Dos verdades que cambian todo en móvil:**
> 1. **La app publicada convive con versiones viejas instaladas.** Un usuario puede no actualizar en
>    meses: el back-end, el almacenamiento local y los deep links tienen que seguir sirviéndole.
> 2. **Lo que llega a una tienda lo decide el dev.** El kit prepara; publicar, enviar una actualización OTA
>    a producción o firmar con las credenciales del cliente, nunca (roster § Prohibiciones).

---

## Versiones y requisitos de tienda — se verifican, no se recuerdan

Referencia **verificada el 2026-10-22** (punto de partida, no verdad):

| Herramienta / requisito | Estado | Lo que más importa |
|---|---|---|
| React Native | 0.88 (React 19.3) | Solo la **Arquitectura Nueva**; Hermes V1 por defecto; Node ≥ 22.13; borde a borde en Android 15+ |
| Expo | SDK 58 (RN 0.88) | Expo Router versionado con el SDK; Continuous Native Generation; Expo Go exige iniciar sesión |
| Ionic | 9 | Angular 18–22, React 18+, Vue 3.5+; `ion-img` deprecado |
| Capacitor | 8 | Node ≥ 22, Xcode 26+, Android Studio 2025.2.1+; iOS 15.0, minSdk 24, target/compileSdk 36; iOS con Swift Package Manager |
| **Google Play** | desde 2026-08-31 | Apps nuevas y actualizaciones deben apuntar a **Android 16 (API 36)** |
| **Google Play** | desde 2027-02-01 | Actualizaciones con objetivo Android 15+ deben soportar **páginas de 16 KB** (las apps con librerías nativas —React Native, Hermes— se recompilan con AGP 8.5.1+ y NDK r28+) |
| **App Store** | desde 2026-04-28 | Subidas compiladas con **Xcode 26 y el SDK de iOS 26**; desde 2026-09-09, objetivo iOS 13+; **manifiesto de privacidad** (`PrivacyInfo.xcprivacy`) con las APIs de "razón requerida", también las de SDKs de terceros |
| Tests | Testing Library RN 14 · `jest-expo` del SDK · Detox 20 · Maestro | |
| Listas y animación | FlashList 2 (requiere la Arquitectura Nueva) · Reanimated 4 | |

En el onboarding y en cada release se comprueban **los requisitos vigentes de las dos tiendas**: una app
que no cumple el target de Play o el SDK de Xcode no se puede actualizar. Es una tarea propia y la decide
el dev.

---

## Cómo se escribe

- **TypeScript estricto**, componentes de función, una responsabilidad por componente; las reglas de
  React (`rules/react/eden-react-rules.md` § Componentes) valen igual en React Native y en Ionic React.
- **Tokens del proyecto** en el theme (StyleSheet con constantes del theme, NativeWind, Tamagui, o las
  variables CSS de Ionic): nada de colores, tamaños ni fuentes sueltos. Modo claro y oscuro si el diseño
  lo define.
- **Áreas seguras** y borde a borde: el contenido respeta notch, barra de estado y barra de gestos.
- **Estados completos**: carga, vacío, error, **sin conexión** y **permiso negado**.
- **Nada bloquea el hilo de UI** (o el de JS en React Native): trabajo pesado, fuera.

## Reuse-first en móvil

1. **Lo que ya trae el framework o una librería instalada** (componentes de Expo, de Ionic, de la librería
   de UI del proyecto; módulos de Expo; plugins oficiales de Capacitor).
2. **Configuración** (config de la app, opciones del componente).
3. **Extender** con una prop o parámetro con el comportamiento actual por defecto. Antes, blast radius.
4. **Código acotado** en JS/TS.
5. **Código nativo nuevo** (módulo o plugin propio): último recurso, porque **exige un binario nuevo** y
   pasar por la tienda. Se declara así en el plan.

Una librería nueva, y más si es nativa, la decide el dev: cambia el binario, puede romper la compilación
de una plataforma y debe ser compatible con la versión del SDK.

## Nativo y permisos

- **Permisos mínimos**, pedidos **en el momento de usarlos** con su texto explicativo real (iOS:
  `NS*UsageDescription`; Android: manifiesto + petición en tiempo de ejecución), y se maneja el "no".
- **Declaraciones de privacidad** de las tiendas al día con lo que la app usa y recoge.
- **Lo nativo no viaja por OTA**: un cambio nativo exige un build nuevo y pasar por la tienda. Una
  actualización OTA (solo JS y assets) va atada a una versión de runtime compatible.
- Deep links y universal/app links declarados en la config y en los archivos del dominio
  (`apple-app-site-association`, `assetlinks.json`), y **sus parámetros tratados como entrada hostil**.

## Datos y almacenamiento

- **Ningún secreto en la app**: todo lo que va en el bundle o el paquete se puede extraer. Las claves que
  deben ser secretas viven en el back-end; las variables públicas (`EXPO_PUBLIC_*`, `environment.ts`)
  solo llevan valores públicos.
- **Tokens y datos sensibles en Keychain/Keystore** (`expo-secure-store`, o un plugin seguro en
  Capacitor). AsyncStorage, `@capacitor/preferences` y `localStorage` son texto plano.
- **La red falla**: timeouts, reintentos en lo idempotente, cola de escrituras sin conexión.
- **El almacenamiento local tiene versión** y se migra al arrancar una versión nueva.

## Accesibilidad

- React Native: `accessibilityRole`, `accessibilityLabel`, `accessibilityState`, `accessibilityHint`; en
  Ionic, la semántica HTML y los atributos ARIA de sus componentes.
- **El texto escala con la fuente del sistema** y el layout aguanta el tamaño grande (no se desactiva el
  escalado para "que quepa").
- Objetivos táctiles de al menos **44×44 pt (iOS) / 48×48 dp (Android)**, contraste AA, orden de foco
  lógico, y `prefers-reduced-motion`/"reducir movimiento" respetado.
- Se prueba con VoiceOver y TalkBack cuando el entorno lo permite; si no, se declara.

## Tests

Siguen `eden-testing-rules.md`: **el test se escribe antes** y debe fallar primero (`eden:mobile-tester`).

- Unitarios y de componente con el runner del proyecto + Testing Library; lo nativo, simulado en el borde.
- **e2e** de los flujos críticos: Maestro o Detox en React Native; Playwright o Cypress contra el
  servidor web en Ionic (y en dispositivo cuando el flujo depende de un plugin).
- La puerta de `turnoff-task`: lint, typecheck, tests y el doctor del framework (`expo-doctor`,
  `cap doctor`). **Lo que no se pudo ver en una plataforma se declara** ("sin simulador iOS").

## Entorno, builds y tiendas

- **Xcode solo existe en macOS.** En Windows o Linux, iOS se compila en la nube (EAS Build u otro) o en
  otra máquina; el kit lo dice en vez de asumirlo.
- **Perfiles de build separados** (desarrollo, preview, producción) y **canales de OTA separados**; el de
  producción no se usa sin el sí del dev.
- **Versión y número de build** suben en cada release; el identificador de la app (bundle id, package
  name) no cambia en una app publicada.
- Las **credenciales de firma** las gestiona el dev; nunca entran en el repo.

## Seguridad

Aplica `eden-security-rules.md` y **OWASP MASVS** (v2.1, con su apartado de privacidad). Lo propio:

| Severidad | En móvil |
|---|---|
| **Crítica** | Un secreto en el bundle o en una variable pública; un deep link que ejecuta una acción sensible sin validar; un WebView que carga contenido remoto con acceso a los plugins; credenciales de firma en el repo; una versión con RCE o bypass conocido y parche disponible |
| **Alta** | Tokens en almacenamiento plano; navegación del WebView abierta (`allowNavigation` amplio, `server.url` de desarrollo en una build de producción); comunicación sin TLS; datos personales en logs |
| **Media** | Permisos de más o sin texto; dependencia con aviso alto; falta de declaración de privacidad; sin bloqueo de capturas en pantallas sensibles cuando el negocio lo pide |
| **Baja** | Sin ofuscación ni comprobación de integridad en apps que no la necesitan; logs verbosos en release |

- **Dependencias auditadas** (`npm audit`): en 2026 apareció en npm un paquete malicioso que se hacía pasar
  por una librería de React Native. Una dependencia nueva se revisa (autor, descargas, repositorio) antes
  de proponerla.

## Blast radius en móvil

```bash
grep -rn "{Nombre}" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" app src
```

Más: rutas y deep links que llevan a la pantalla, plugins o módulos nativos que dependen del cambio, y
dos preguntas que solo existen aquí: **¿exige un binario nuevo?** y **¿rompe a quien tenga la versión
anterior instalada?** (almacenamiento local, contrato con el back-end, deep links).

## Documentación vigente

- React Native: https://reactnative.dev · Expo: https://docs.expo.dev
- Ionic: https://ionicframework.com/docs · Capacitor: https://capacitorjs.com/docs
- Google Play — target SDK: https://developer.android.com/google/play/requirements/target-sdk · 16 KB: https://developer.android.com/guide/practices/page-sizes
- Apple — requisitos de subida: https://developer.apple.com/news/upcoming-requirements/ · privacidad: https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- OWASP MASVS: https://mas.owasp.org/MASVS/
