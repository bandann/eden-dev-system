---
name: react-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:react-setup`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:react` (que ya
  fue invocado por él y le pide confirmación antes). NO lo actives porque el proyecto sea React o porque
  falte un script: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: levanta el
  entorno de desarrollo de un proyecto React. En un proyecto nuevo pregunta el sabor (SPA con Vite o
  Next.js), el gestor de paquetes, la versión de Node y las herramientas (tests, e2e, estilos), y lo
  monta con el scaffold oficial vigente. En un proyecto existente completa solo lo que falta (scripts,
  TypeScript estricto, ESLint, tests, `.env.example`) sin tocar lo que funciona, y declara el bloque
  `react` en `project-config.json`. Nunca despliega ni instala dependencias sin el sí del dev.
argument-hint: "[ruta del proyecto] [| spa | next] [| npm | pnpm | yarn | bun] [| nuevo | existente]"
disable-model-invocation: true
---

## React Setup — el entorno del proyecto

Argumento recibido: `$ARGUMENTS`

Deja el proyecto en el estado en el que cualquier skill del kit puede trabajar y verificar: el
framework instalado con su versión vigente, los scripts que el kit usa (`dev`, `build`, `lint`,
`typecheck`, `test`), la validación montada y la configuración declarada.

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace el `devops` del roster React
(`eden:react-devops`), con `eden:react-architect` para el inventario si el proyecto ya existe.

### Lo que NO hace — nunca

- **Desplegar**, ni crear cuentas en un proveedor (Vercel, Netlify…), ni dejar un workflow que
  despliegue solo.
- **Instalar herramientas globales** o dependencias sin el sí del dev, con la lista exacta delante.
- **Escribir secretos**: `.env.example` solo lleva nombres y comentarios.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.
- Reescribir la configuración de un proyecto que ya funciona "por limpiar".

---

### Paso 1 — Qué hay

`python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect {ruta}` y, si hay código, un `inventory`
de `eden:react-architect`:

- ¿Hay `package.json`? ¿Qué lockfile (y por tanto qué gestor)? ¿Qué versiones de React, Next, Vite,
  React Router, TypeScript?
- ¿Node fijado (`engines`, `.nvmrc`, `.node-version`)? `node --version` instalado.
- ¿Existen los scripts `dev`, `build`, `lint`, `typecheck`, `test`? ¿`tsconfig` estricto? ¿ESLint flat
  config? ¿Runner de tests y Testing Library? ¿Playwright?
- ¿`.env.example`, `.gitignore` correcto, `.claude/project-config.json` con su bloque `react`?
- ¿Git? ¿Qué ramas?

Clasifica: **nuevo** (sin `package.json`) o **existente** (solo se completa lo que falta).

### Paso 2 — Preguntar lo que falta, en una sola intervención

Antes, comprueba en la doc vigente (context7) los comandos de scaffold y la versión mínima de Node del
framework: no se usan de memoria.

```
⚛️ SETUP REACT — necesito:

Sabor:            [spa — React + Vite] · [next — Next.js]   (recomiendo {x} porque {razón del proyecto})
Gestor:           npm · pnpm · yarn · bun                   (recomiendo {x})
Node:             {versión instalada} — mínimo del framework {y} {✅ | ❌ hay que actualizar Node}
Lenguaje:         TypeScript (recomendado) · JavaScript
Estilos:          {Tailwind · CSS Modules · librería de UI} — o lo que diga el diseño
Tests:            Vitest + Testing Library (recomendado) · Jest
e2e:              Playwright (recomendado) · ninguno por ahora
React Compiler:   sí · no
Next (si next):   App Router (recomendado) · Cache Components {sí por defecto en proyectos nuevos}
Carpeta:          {ruta} {vacía ✅ | con archivos ⚠️}
Rama base:        {la que digas}
```

Para un proyecto **existente** se pregunta solo lo que falta, con lo que se va a añadir y por qué.

### Paso 3 — Montarlo (delegado a `eden:react-devops`)

Con el encargo de cinco partes y el sí del dev explícito en él (incluida la lista de dependencias):

- **Nuevo:** scaffold oficial del sabor con las opciones elegidas; scripts del kit; `tsconfig`
  estricto; ESLint (en Next, CLI de ESLint con `eslint-config-next`: `next lint` ya no existe); runner
  de tests con un test de ejemplo que pasa; Playwright si se eligió; `.env.example`; `.gitignore`;
  `engines`/`.nvmrc`.
- **Existente:** solo los huecos aprobados.

### Paso 4 — Verificar y declarar

1. `install` con el lockfile, `lint`, `typecheck`, `test`, `build`: la salida real de cada uno.
2. `dev` arranca y la página inicial responde (si hay Playwright MCP o navegador, se mira; si no, se
   declara).
3. Escribe en `.claude/project-config.json`: `project.stack: "react"` y el bloque `react`
   (`flavor`, `package_manager`, `node_version`). Si no existe el archivo, desde
   `team/project-config.example.json`.
4. En el `CLAUDE.md` del proyecto, el marcador `<!-- eden-stack: react -->` y una línea con el sabor.

### Paso 5 — Reporte

```
⚛️ SETUP REACT — LISTO

Sabor: {spa | next} {versión} · React {v} · TypeScript {v} · Node {v} · gestor {x}
Scripts: dev ✅ · build ✅ · lint ✅ · typecheck ✅ · test ✅ · test:e2e {✅ | —}
Verificación: {salida resumida de cada comando}
Declarado: project-config.json (react.flavor = {x}) · CLAUDE.md
Pendiente del dev: {variables de entorno reales, cuentas, el deploy}

➜ Siguiente: /eden:create-fundaments (tokens desde Figma) o /eden:react para la primera tarea.
```
