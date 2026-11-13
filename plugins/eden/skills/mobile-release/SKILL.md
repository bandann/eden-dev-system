---
name: mobile-release
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:mobile-release`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:mobile` con
  su confirmación. NO lo actives porque se hable de la tienda o de una versión: si no lo pidió por su
  nombre, no se usa. — Qué hace cuando SÍ se invoca: PREPARA una versión de una app móvil para las
  tiendas: decide con el dev si es binario nuevo o actualización OTA, sube versión y número de build,
  comprueba los requisitos vigentes de Google Play y App Store (target SDK, Xcode/SDK, páginas de 16 KB,
  manifiesto de privacidad, permisos y textos, borrado de cuenta), escribe las notas y deja los comandos
  exactos. NUNCA publica, ni envía OTA a producción, ni firma: eso lo hace el dev.
argument-hint: "[versión, p.ej. 1.4.0] [| binario | ota] [| plataformas] [| notas]"
disable-model-invocation: true
---

## Mobile Release — preparar la versión (publica el dev)

Argumento recibido: `$ARGUMENTS`

Deja una versión **lista para que el dev la publique**: el número correcto, los requisitos de las tiendas
comprobados, las notas escritas y los comandos exactos. **Este skill no publica nada**: ni `eas submit`,
ni TestFlight, ni Play Console, ni `eas update` a producción, ni builds firmados en la nube sin el sí del
dev. Reglas: `rules/mobile/eden-mobile-rules.md` § Versiones y requisitos de tienda, y § Entorno, builds y
tiendas.

> **Idioma:** al dev, en español. Notas de la versión y textos de tienda, en el idioma que pida el dev
> (por defecto, inglés).

### Paso 1 — ¿Binario o OTA?

`eden:mobile-architect` compara con la última versión publicada (etiqueta o rama que diga el dev):

- **Hay cambios nativos** (módulos, plugins, permisos, config nativa, SDK) → **binario nuevo**: pasa por
  la revisión de la tienda.
- **Solo JS y assets**, con la misma versión de runtime → **cabe en OTA** (si el proyecto la usa), a un
  canal que **el dev** elige.

Si el dev pidió OTA y hay cambios nativos, **se para y se dice**: una OTA así rompe la app instalada.

### Paso 2 — Requisitos vigentes (se comprueban, no se recuerdan)

Con la doc vigente de las dos tiendas (`eden-mobile-rules.md` § Versiones tiene la referencia del
2026-10-22):

```
📱 RELEASE {versión} — CHECKLIST

Tipo: {binario | OTA → canal {x}}
Versión: {semver} · build: {n+1} (Android versionCode / iOS buildNumber)
Google Play:  target SDK {36 ✅ | ❌} · páginas de 16 KB {✅ | ❌ (desde 2027-02-01)} · declaraciones de datos {✅ | revisar}
App Store:    Xcode / SDK de iOS {26 ✅ | ❌} · objetivo iOS mínimo {✅} · PrivacyInfo.xcprivacy {✅ | falta: …}
Permisos:     {lista con su texto — ✅ | ⚠️ texto genérico}
Cuenta:       {la app crea cuentas → borrado en la app ✅ | ❌}
Tracking:     {ATT necesario: sí/no}
Calidad:      tests ✅ · lint ✅ · typecheck ✅ · doctor ✅ · security-check deps {…}
Assets:       iconos · splash · capturas {✅ | faltan}
Notas:        {borrador}
```

Lo que no se puede comprobar en local (por ejemplo, alineación de 16 KB sin compilar, o iOS sin macOS) se
marca como **no verificado**, con cómo verificarlo.

### Paso 3 — Preparar (delegado a `eden:mobile-devops`, con el sí del dev)

- Subir versión y número de build en la config del proyecto.
- Notas de la versión (y textos de tienda si el dev los pide).
- Lo que la checklist marcó como arreglable en el repo (un texto de permiso, una entrada del manifiesto de
  privacidad) — como unidades normales, con test si aplica.

### Paso 4 — Entregar al dev

```
📱 RELEASE {versión} — LISTA PARA PUBLICAR

Checklist: {✅ todo | ⚠️ pendientes: …}
Cambios: {resumen desde la versión anterior}
Comandos (los ejecutas tú):
  {eas build --profile production --platform all}     ← build firmado (cuota y credenciales)
  {eas submit --platform ios|android}                 ← publicar
  {o: eas update --channel production --message "…"}  ← solo si es OTA
No verificado: {…}
```

El trabajo queda en la rama **sin commitear**: el commit de la versión lo hace `turnoff-task`. Publicar es
del dev.
