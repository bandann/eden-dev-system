# Sabor: React Native

React Native escribe UI **nativa** con React. La recomendación oficial para apps nuevas es usar un
framework, y ese framework es **Expo**; React Native sin framework (bare) queda para restricciones
especiales. Verificado para **React Native 0.88 y Expo SDK 58** (2026-10-22).

## Expo o bare

| | Expo (recomendado) | Bare |
|---|---|---|
| Crear | `npx create-expo-app@latest` | Solo si el dev tiene una restricción concreta; con el CLI de la comunidad |
| Carpetas nativas | **Generadas** (Continuous Native Generation): `npx expo prebuild` crea `ios/` y `android/` desde `app.json`/`app.config.*` y los config plugins; por defecto **no se versionan** | Código fuente versionado |
| Cambiar lo nativo | Config plugins y la config de la app — **nunca a mano** en `ios/`/`android/` (`prebuild --clean` lo borra) | Directamente en Xcode/Android Studio, con revisión |
| Builds | EAS Build (nube) o local con `npx expo run:ios|android` | Xcode y Gradle |
| Actualizaciones OTA | EAS Update (solo JS y assets, atadas a `runtimeVersion`) | Lo que tenga el proyecto |

Si un proyecto Expo **versiona** `ios/` y `android/`, EAS no los regenera: se trabaja como bare para lo
nativo, y se dice.

## Estructura (Expo Router)

```
app/                    rutas por archivos: _layout.tsx (stacks, tabs), index.tsx, [id].tsx, (grupos)
components/ · hooks/ · lib/ · constants/ (theme y tokens)
assets/                 imágenes y fuentes
app.json | app.config.ts   identificadores, permisos, plugins, esquema de deep links
eas.json                perfiles de build y canales
```

Si el proyecto usa React Navigation en vez de Expo Router, se sigue.

## Lo que cambió y hay que saber

- **Solo la Arquitectura Nueva** (Fabric, TurboModules) desde 0.82: una librería que dependa del bridge
  antiguo **no funciona**. Antes de proponer una, se comprueba que la soporte.
- **Hermes V1** es el motor por defecto.
- **Borde a borde en Android 15+**: se usan las safe areas (`react-native-safe-area-context` o lo que use
  el proyecto) en vez de suponer barras opacas.
- **Expo Go** solo sirve si todo el código nativo está en Expo Go (y ahora exige iniciar sesión). Con
  módulos nativos propios o de terceros, se usa un **development build** (`expo-dev-client`).
- **`npx expo install {paquete}`** instala la versión compatible con el SDK; `npx expo-doctor` revisa
  dependencias y configuración.

## Componentes y estilo

- Primitivas de React Native (`View`, `Text`, `Pressable`, `Image`/`expo-image`) o las de la librería de UI
  del proyecto. **Todo texto va dentro de `<Text>`**.
- `StyleSheet.create` con valores del theme, o el sistema del proyecto (NativeWind, Tamagui, Unistyles).
- `Pressable` con `accessibilityRole="button"` y su etiqueta; `hitSlop` para llegar al objetivo táctil
  mínimo sin agrandar el diseño.
- Listas: `FlatList`/`SectionList` o **FlashList 2** si el proyecto la tiene; nunca `ScrollView` con
  `map()` para listas largas.
- Animaciones con Reanimated (4) si el proyecto la usa, respetando "reducir movimiento".

## Datos y almacenamiento

- Tokens en **`expo-secure-store`** (Keychain/Keystore; para valores pequeños). AsyncStorage para
  preferencias no sensibles.
- `EXPO_PUBLIC_*` se incrusta en el bundle: **solo valores públicos**.

## Tests

- **Jest** con el preset del SDK (`jest-expo`) y **Testing Library React Native (14)**.
- **e2e:** Maestro (flujos en YAML, funciona con development builds) o Detox, lo que tenga el proyecto.

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} test && npx expo-doctor
npx expo run:android            # build de desarrollo local (y run:ios en macOS)
```

Y en el simulador o emulador: la pantalla en un teléfono pequeño y uno grande, con fuente grande y con el
lector de pantalla. Lo que no se pudo ver, se declara.
