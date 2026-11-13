# Dispatch — cómo reparte el líder móvil

## 1. Partir en unidades

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Un ajuste de estilos, un estado que faltaba | Un especialista (+ su test) |
| **M** | Una pantalla con sus datos, una capacidad nativa (cámara, notificaciones) | tester → data-dev → native-dev → ui-dev, con design-auditor si es visual |
| **L** | Un flujo de varias pantallas (onboarding, checkout) | Varias unidades M con dependencias |
| **XL** | Una app o un rediseño | Lotes L por flujo |

Una unidad que cruza dueños **se parte** en ese orden. Lo nativo va antes que la UI que lo usa, con su
interfaz JS tipada.

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa, si exige binario nuevo | `eden:mobile-architect` |
| Pantallas, navegación, componentes, estilos, tokens | `eden:mobile-ui-dev` |
| Módulos nativos, config plugins, plugins de Capacitor, permisos | `eden:mobile-native-dev` |
| Estado, fetching, almacenamiento seguro, offline | `eden:mobile-data-dev` |
| Tests (primero), e2e | `eden:mobile-tester` |
| Entorno, configuración, builds de desarrollo, CI, preparar release | `eden:mobile-devops` |
| Figma → Design Spec · medir Figma vs pantalla | `eden:figma-extractor` · `eden:design-auditor` |
| Revisar el diff; calidad | `eden:mobile-qa-reviewer` |
| Seguridad independiente | `eden:security-auditor` |

Identificadores de la app, versión y build, iconos, splash y esquemas de deep links: los decide el líder
con el sí del dev.

## 3. Plantilla del plan (al dev, en español)

```
📱 PLAN DEL EQUIPO MÓVIL

Trabajo: {new | onboard | task} · {ticket / descripción} · sabor {react-native | ionic}
Rama: {nombre} desde {base — preguntada}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | Tests de {x} | S | eden:mobile-tester | … | — | — |
| 2 | Datos de {x} | S | eden:mobile-data-dev | … | 3 | 1 |
| 3 | Cámara | M | eden:mobile-native-dev | app.json (plugin + permiso) | 1 — módulo de Expo | 1 |
| 4 | Pantalla {x} | M | eden:mobile-ui-dev | app/x.tsx | 4 | 1, 2, 3 |

Binario nuevo: {sí — por {3} | no}
Versiones instaladas: {qué pasa con quien no actualice}
Permisos: {nuevos con su texto} · Privacidad: {declaraciones que cambian}
🛡️ Superficie: entra {API, deep links} · sale {…} · quién {…} · secretos en la app: ninguno · terceros {…}
Se puede verificar en: {Android emulador · iOS simulador (macOS) · solo tests}
Paro a preguntarte en: {dependencias nativas, identificadores, builds en la nube}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: flavor {react-native | ionic} (rules/mobile/flavors/{x}.md) · {Expo SDK | RN | Ionic | Capacitor} {v} ·
      Design Spec {…} · tokens {…} · reuse step {n}: {why} · sibling pattern: {file} · tests to make green: {files}
ACCEPT WHEN: {tests + lint + typecheck green; doctor clean; renders on {platforms} at {sizes}; large font OK}
DO NOT: touch other files; add/remove/upgrade dependencies or native plugins; edit ios/ or android/ by hand
        in a CNG project; touch signing credentials, app identifiers or version; publish or send OTA;
        put secrets in the app; {unit-specific}
HANDOFF: teams/mobile/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

Solo unidades con **archivos disjuntos**, en un solo turno, como mucho 4 a la vez. Dos unidades que tocan
`app.json`/`app.config.*` o los proyectos nativos van en secuencia.
