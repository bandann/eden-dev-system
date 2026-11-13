---
name: mobile-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:mobile-setup`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:mobile` (que
  ya fue invocado por él y le pide confirmación antes). NO lo actives porque el proyecto sea móvil o falte
  una herramienta: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: levanta el
  entorno de desarrollo de una app móvil. En una app nueva pregunta el sabor (React Native con Expo, React
  Native bare o Ionic con Capacitor y su framework), las plataformas, el entorno disponible (macOS/Xcode,
  Android SDK), la navegación, el theme y las herramientas de tests, y lo monta con el scaffold vigente y
  perfiles de build separados. En una existente completa solo lo que falta y declara el bloque `mobile`
  en `project-config.json`. Nunca publica, ni lanza builds en la nube, ni toca credenciales sin el sí del
  dev.
argument-hint: "[ruta del proyecto] [| expo | bare | ionic-angular | ionic-react | ionic-vue] [| nuevo | existente]"
disable-model-invocation: true
---

## Mobile Setup — el entorno de la app

Argumento recibido: `$ARGUMENTS`

Deja la app en el estado en el que cualquier skill del kit puede trabajar y verificar: el framework con
su versión vigente, la app arrancando en un emulador o simulador, perfiles de build separados, y lo que
el kit usa para verificar (lint, typecheck, tests, doctor).

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace `eden:mobile-devops`, con
`eden:mobile-architect` para el inventario si la app ya existe.

### Lo que NO hace — nunca

- **Publicar** ni crear apps en las consolas de las tiendas.
- **Builds en la nube** (EAS Build, Appflow) ni **credenciales de firma**, sin el sí del dev.
- **Instalar herramientas globales** (Xcode, Android Studio, CLIs globales) ni dependencias sin el sí del
  dev, con la lista exacta.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.

---

### Paso 1 — Qué hay

`python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect {ruta}` y, si hay código, un `inventory`
de `eden:mobile-architect`:

- ¿Proyecto existente? ¿Expo (y su SDK), React Native bare, o Ionic (y su framework) con Capacitor?
- ¿`ios/` y `android/` versionados o generados (CNG)?
- Entorno: `node --version`; **¿es macOS con Xcode?** (sin eso no hay build local de iOS); Android SDK y
  un emulador; Java/Gradle si es Android nativo.
- ¿`app.json`/`app.config.*`, `eas.json`, `capacitor.config.*`? ¿Tests y e2e? ¿Scripts del kit?
- ¿`.env.example`, `.gitignore` sin credenciales, `.claude/project-config.json` con su bloque `mobile`?

### Paso 2 — Preguntar lo que falta, en una sola intervención

Antes, comprueba en la doc vigente (context7 o docs.expo.dev / reactnative.dev / ionicframework.com /
capacitorjs.com) los comandos de creación, las versiones y los mínimos de Node, Xcode y Android, y los
requisitos de las tiendas: no se usan de memoria.

```
📱 SETUP MÓVIL — necesito:

Sabor:          [expo — React Native con Expo] · [bare — React Native sin framework] · [ionic — Ionic + Capacitor]
                (recomiendo {x} porque {razón del proyecto})
Framework web:  {solo Ionic} Angular · React · Vue
Plataformas:    iOS · Android · web
Entorno:        macOS con Xcode {✅ | ❌ → iOS solo en la nube, con tu sí} · Android SDK {✅ | ❌}
Navegación:     Expo Router (recomendado en Expo) · React Navigation · router de Ionic
Estilos:        StyleSheet + theme · NativeWind · Tamagui · variables de Ionic
Tests:          Jest + Testing Library (recomendado) · e2e: Maestro · Detox · Playwright (Ionic) · ninguno
Identificador:  {bundle id / package name} — {lo eliges tú; no se cambia después de publicar}
Carpeta:        {ruta} {vacía ✅ | con archivos ⚠️}
Rama base:      {la que digas}
```

Para una app **existente** se pregunta solo lo que falta, con lo que se va a añadir y por qué.

### Paso 3 — Montarlo (delegado a `eden:mobile-devops`)

Con el encargo de cinco partes y el sí del dev explícito en él (incluida la lista de dependencias):

- **Expo:** `create-expo-app` vigente con la plantilla elegida; `app.config.ts` con el identificador;
  `eas.json` con perfiles `development`, `preview` y `production` y canales de OTA separados;
  development build si habrá código nativo.
- **Bare:** el CLI de la comunidad con la versión vigente; proyectos nativos versionados.
- **Ionic:** el creador de Ionic con el framework elegido; `npx cap add ios|android`; `capacitor.config.ts`
  con `allowNavigation` mínimo y sin `server.url`.
- **Todos:** TypeScript estricto, ESLint, tests con Testing Library (y e2e si se eligió), scripts del kit,
  `.env.example`, `.gitignore` (credenciales, `.env*`, y en Expo con CNG, `ios/` y `android/`).
- **Existente:** solo los huecos aprobados.

### Paso 4 — Verificar y declarar

1. `install`, `lint`, `typecheck`, `test` y `expo-doctor` / `cap doctor`: la salida real.
2. La app arranca en el **emulador de Android** (y en el **simulador de iOS** si hay macOS): se mira; si
   no se pudo, se declara.
3. Escribe en `.claude/project-config.json`: `project.stack: "mobile"` y el bloque `mobile` (`flavor`).
4. En el `CLAUDE.md` del proyecto, el marcador `<!-- eden-stack: mobile -->` y una línea con el sabor.

### Paso 5 — Reporte

```
📱 SETUP MÓVIL — LISTO

Sabor: {expo SDK v · RN v | bare RN v | ionic v + {framework} · Capacitor v} · plataformas {…}
Herramientas: lint ✅ · typecheck ✅ · tests ✅ · e2e {✅ | —} · doctor ✅
Arranca en: Android {✅ | no probado} · iOS {✅ | sin macOS}
Builds: perfiles development · preview · production · canales OTA separados
Declarado: project-config.json (mobile.flavor = {x}) · CLAUDE.md
Pendiente del dev: credenciales de firma, cuentas de tienda, builds en la nube, publicar

➜ Siguiente: /eden:create-fundaments (tokens desde Figma) o /eden:mobile para la primera tarea.
```
