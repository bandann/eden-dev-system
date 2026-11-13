---
name: react-data
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:react-data`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:react` o
  `/eden:go` con su confirmación. NO lo actives porque haya un fetch, un formulario o un store: si no lo
  pidió por su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: diseña e implementa
  la capa de datos de una funcionalidad React (SPA o Next): de dónde vienen los datos y con qué
  herramienta (la del proyecto), el estado de UI frente al del servidor, los formularios con validación
  compartida cliente/servidor, los estados de carga/vacío/error, la caché y la invalidación, y la
  seguridad de la entrada. Test primero. No commitea.
argument-hint: "<funcionalidad | hook | formulario | store> [| endpoint o fuente] [| url-ticket] [| notas]"
disable-model-invocation: true
---

## React Data — datos, estado y formularios

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **la capa de datos** de algo: consumir una API, un formulario con validación,
un store, una caché que invalidar. Reglas: `rules/react/eden-react-rules.md` § Datos, estado y
formularios, y el sabor (`flavors/spa.md` o `flavors/next.md`). Equipo: `teams/react/roster.md`.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

Qué datos (fuente, forma, quién los puede ver), qué escrituras, qué formularios y qué estados pide el
diseño. Del ticket si lo hay. Si la fuente es una API de otro equipo, su contrato (OpenAPI, tipos) se
pide en vez de adivinarlo.

### Paso 2 — Lo que ya existe (delegado)

`eden:react-architect` → cómo el proyecto ya resuelve datos y estado: librería de fetching (TanStack
Query, SWR, RTK Query, RSC `fetch`, loaders del router), stores, esquemas de validación (Zod u otro),
cliente de API, manejo de errores y de sesión. **Lo que hay se usa**: una librería nueva es una
dependencia nueva y la decide el dev.

### Paso 3 — El plan

```
⚛️ DATOS — {funcionalidad}  ·  sabor {spa | next}

Fuente: {API / DB vía DAL / loader} · contrato: {tipos u OpenAPI}
Herramienta: {la del proyecto} — {por qué encaja}
Estado: servidor {qué, cacheado dónde} · UI {qué, local en qué componente} · global {solo si hace falta, por qué}
Formulario: esquema {x} compartido cliente/servidor · errores por campo · envío / éxito / error
Escrituras: {mutación / Server Action} → invalida {qué}
Estados: carga · vacío · error · éxito
🛡️ Superficie: entra {…} · validado en {servidor} · quién {…} · secretos {solo servidor} · sale {DTO}
Contrato para la UI: {props / valores que devuelve el hook, tipados}
Tests: {qué criterios}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego los datos

1. `eden:react-tester`: tests del hook o de la acción (éxito, error de red, validación que falla,
   acceso denegado, vacío), con la red mockeada en el borde → rojo.
2. `eden:react-data-dev`: la implementación hasta verde, con el contrato tipado para la UI.
3. Si hay UI que conectar: `eden:react-ui-dev` con ese contrato (o `/eden:react-component`).

### Paso 5 — Verificar y reportar

`eden:react-qa-reviewer` y, si hay escrituras, autenticación o datos de usuarios, `eden:security-auditor`.

```
⚛️ DATOS — {funcionalidad} — LISTO

Archivos: {…} · Herramienta: {…}
Estados cubiertos: carga ✅ · vacío ✅ · error ✅ · éxito ✅
Seguridad: {validación en servidor ✅ · auth ✅ | hallazgos}
Tests: {n ✅} · lint ✅ · typecheck ✅ · build ✅
Contrato para la UI: {…}
No verificado: {…}
```

No commitea ni pushea.
