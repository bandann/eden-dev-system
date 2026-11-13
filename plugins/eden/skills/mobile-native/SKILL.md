---
name: mobile-native
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:mobile-native`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:mobile` o
  `/eden:go` con su confirmación. NO lo actives porque se mencione la cámara o las notificaciones: si no
  lo pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: integra UNA
  capacidad nativa del dispositivo (cámara, ubicación, notificaciones push, biometría, archivos, contactos,
  Bluetooth, pagos in-app…) en una app React Native o Ionic, eligiendo primero el módulo de Expo o el
  plugin oficial de Capacitor, con los permisos mínimos y sus textos, las declaraciones de privacidad, el
  manejo del "no" y la compilación comprobada en las dos plataformas. Avisa de que exige un binario nuevo.
  No commitea.
argument-hint: "<capacidad, p.ej. 'notificaciones push'> [| url-ticket] [| plataformas] [| notas]"
disable-model-invocation: true
---

## Mobile Native — una capacidad del dispositivo

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una capacidad nativa**. Es el cambio móvil más caro: **exige un binario nuevo**
(pasa por la tienda, no por OTA), puede romper la compilación de una plataforma y añade permisos que el
usuario y la tienda revisan. Reglas: `rules/mobile/eden-mobile-rules.md` § Nativo y permisos, y el sabor.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué capacidad, para qué la usa el usuario (eso es el texto del permiso), en qué plataformas, qué pasa si
la niega, y si hay un servicio externo (push, pagos) con sus cuentas y claves, **que gestiona el dev**.

### Paso 2 — Lo que ya existe (delegado)

`eden:mobile-architect` → qué módulos y plugins nativos ya hay, cómo se maneja lo nativo (CNG con config
plugins, o carpetas versionadas), permisos ya declarados, y la versión del SDK o de Capacitor.

### Paso 3 — Elegir cómo, de lo más barato a lo más caro

1. **Ya está** en un módulo o plugin instalado.
2. **Módulo oficial**: de Expo (`npx expo install` resuelve la versión compatible) o `@capacitor/*`.
3. **Librería de la comunidad** mantenida, compatible con la Arquitectura Nueva (React Native) o con la
   mayor de Capacitor — con el sí del dev.
4. **Código nativo propio** (Expo Modules API o plugin de Capacitor en Swift/Kotlin) — último recurso.

```
📱 NATIVO — {capacidad}  ·  {react-native | ionic}

Cómo: {escalón} — {módulo o plugin y versión} — por qué no alcanza el anterior
Permisos: iOS {clave: "texto"} · Android {permiso} — se piden {cuándo}
Si lo niega: {qué ve el usuario}
Privacidad: {manifiesto de privacidad / declaraciones de la tienda que cambian}
Cuentas y claves: {servicio — las configura el dev; en la app solo lo público}
Exige binario nuevo: sí · OTA: no
Se compila en: Android {✅} · iOS {macOS ✅ | ❌ — en la nube con tu sí}
Tests (primero): {interfaz JS con lo nativo simulado · permiso negado}

¿Le doy?
```

Espera el sí (y el de la dependencia, si es nueva).

### Paso 4 — Test primero, luego lo nativo

1. `eden:mobile-tester`: tests de la interfaz JS con el módulo simulado (éxito, permiso negado, no
   disponible en el dispositivo, error) → rojo.
2. `eden:mobile-native-dev`: módulo o plugin, config plugin o proyecto nativo, permisos con su texto y
   declaraciones de privacidad; compila en las dos plataformas en local.
3. `eden:mobile-ui-dev`: el punto de la UI que lo usa y el estado de "permiso negado".

### Paso 5 — Verificar y reportar

`eden:mobile-qa-reviewer` y `eden:security-auditor` (permisos, datos que salen del dispositivo).

```
📱 NATIVO — {capacidad} — LISTO

Cómo: {módulo/plugin v} · Permisos: {…} · Privacidad: {…}
Compila: Android {✅} · iOS {✅ | no compilado — motivo}
Probado en dispositivo/emulador: {…} · Permiso negado: {✅}
Tests: {n ✅} · doctor ✅
Exige binario nuevo: sí → /eden:mobile-release cuando toque
Pendiente del dev: {cuentas, claves del servicio, credenciales de push}
```

No commitea ni pushea.
