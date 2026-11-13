---
name: mobile-screen
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:mobile-screen`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:mobile` o
  `/eden:go` con su confirmación. NO lo actives porque haya que tocar una pantalla: si no lo pidió por su
  nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: crea o modifica UNA pantalla de una
  app móvil (React Native o Ionic) reuse-first: blast radius, Figma medido (caché primero), navegación y
  deep link si aplica, datos con todos sus estados (carga, vacío, error, sin conexión), test primero,
  tokens del proyecto, áreas seguras y accesibilidad (lector de pantalla, fuente grande, objetivos
  táctiles), verificada en las plataformas disponibles. No commitea.
argument-hint: "<pantalla o ruta> [| url-figma | url-ticket] [| plataformas] [| qué NO tocar]"
disable-model-invocation: true
---

## Mobile Screen — una pantalla, bien hecha

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **una pantalla**: crearla, o cambiar una que existe sin romper la navegación ni
a quien tenga la app instalada. Reglas: `rules/mobile/eden-mobile-rules.md` y el sabor. Equipo:
`teams/mobile/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué pantalla, qué muestra, de dónde vienen los datos, cómo se llega (navegación, deep link), qué hace
cada acción, en qué plataformas, y **qué no se toca**. Del ticket y del Figma si los hay.

### Paso 2 — Lo que ya existe (delegado)

En paralelo: `eden:mobile-architect` (`inventory` de la pantalla o sus vecinas, componentes reutilizables,
`blast-radius`, y **si algo exige binario nuevo**) y `eden:figma-extractor` (Design Spec por tamaño de
dispositivo, caché de diseño primero).

### Paso 3 — El plan

```
📱 PANTALLA — {nombre}  ·  {react-native | ionic}

Escalón: {n} — {por qué}
Ruta: {archivo de la ruta} · se llega desde {…} · deep link {sí: {esquema} — parámetros validados | no}
Componentes: {reutilizados} · nuevos {…}
Datos: {hook o servicio} · estados: carga · vacío · error · sin conexión
Nativo: {ninguno | permiso o API → mobile-native (exige binario nuevo)}
Accesibilidad: roles y etiquetas · fuente grande · objetivos táctiles · orden de foco
Se verifica en: {Android emulador · iOS simulador · tamaños}
Tests (primero): {criterios}
Queda fuera: {…}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego la pantalla

1. `eden:mobile-tester`: tests de la pantalla (lo que se ve, cada acción, los cuatro estados, etiquetas
   accesibles) → rojo.
2. `eden:mobile-data-dev` si hace falta un hook o servicio nuevo, con sus estados tipados.
3. `eden:mobile-native-dev` si hace falta una capacidad nativa (o `/eden:mobile-native` si es grande).
4. `eden:mobile-ui-dev`: la pantalla hasta verde, con los tokens, las áreas seguras y la accesibilidad.
5. Si hay Figma: `eden:design-auditor` en loop hasta 1:1 en los tamaños acordados.

### Paso 5 — Verificar y reportar

`eden:mobile-qa-reviewer` (lint, typecheck, tests, doctor) y, si hay deep link o datos sensibles,
`eden:security-auditor`.

```
📱 PANTALLA — {nombre} — LISTA

Archivos: {…} · Escalón: {n}
Tests: {n ✅} · lint ✅ · typecheck ✅ · doctor ✅
Fidelidad: {1:1 en {tamaños} | deltas: …}
Plataformas: Android {✅ | no probado} · iOS {✅ | sin macOS}
Accesibilidad: lector {✅ | no probado} · fuente grande {✅} · objetivos táctiles {✅}
Binario nuevo: {sí | no}
No verificado: {…}
```

No commitea ni pushea.
