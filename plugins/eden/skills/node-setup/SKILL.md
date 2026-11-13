---
name: node-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:node-setup`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:node` (que ya
  fue invocado por él y le pide confirmación antes). NO lo actives porque el proyecto sea Node o falte un
  script: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: levanta el entorno de
  desarrollo de un back-end en Node. En un proyecto nuevo pregunta el sabor (NestJS, Express o Node sin
  framework), la versión LTS de Node, el gestor de paquetes, ESM o CommonJS, el ORM y la base de datos,
  la validación y el runner de tests, y lo monta con el scaffold vigente y una base local en Docker. En
  uno existente completa solo lo que falta, sin tocar lo que funciona, y declara el bloque `node` en
  `project-config.json`. Nunca despliega, ni toca bases reales, ni instala dependencias sin el sí del dev.
argument-hint: "[ruta del proyecto] [| nest | express | node] [| npm | pnpm | yarn | bun] [| nuevo | existente]"
disable-model-invocation: true
---

## Node Setup — el entorno del back-end

Argumento recibido: `$ARGUMENTS`

Deja el proyecto en el estado en el que cualquier skill del kit puede trabajar y verificar: Node LTS,
el framework con su versión vigente, una base local y otra de tests desechable, y los scripts que el kit
usa (`dev`, `build`, `lint`, `typecheck`, `test`).

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace `eden:node-devops`, con
`eden:node-architect` para el inventario si el proyecto ya existe.

### Lo que NO hace — nunca

- **Desplegar** ni conectarse a un servidor o a una base que no sea local.
- **Instalar herramientas globales** (Node, Docker) ni dependencias sin el sí del dev, con la lista
  exacta delante.
- **Escribir secretos**: `.env.example` solo lleva nombres y comentarios.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.

---

### Paso 1 — Qué hay

`python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect {ruta}` y, si hay código, un `inventory`
de `eden:node-architect`:

- ¿`package.json`? ¿Qué lockfile (gestor)? ¿`"type": "module"`? ¿Qué framework, ORM y versiones?
- ¿Node fijado (`engines`, `.nvmrc`)? `node --version` instalado; `docker --version` si hará falta.
- ¿Scripts `dev`, `build`, `lint`, `typecheck`, `test`? ¿`tsconfig` estricto? ¿ESLint flat config?
  ¿Tests de integración HTTP y contra qué base?
- ¿`.env.example`, `.gitignore` correcto, `.claude/project-config.json` con su bloque `node`?

Si resulta ser **Next.js**, se para: su setup es `/eden:react-setup`. Si es una app de Shopify, el stack
`shopify-app`.

### Paso 2 — Preguntar lo que falta, en una sola intervención

Antes, comprueba en la doc vigente (context7 o nodejs.org y la doc del framework) la LTS actual, el
comando de scaffold y los mínimos de versión: no se usan de memoria.

```
🟩 SETUP NODE — necesito:

Sabor:          [nest — NestJS] · [express — Express] · [node — sin framework]   (recomiendo {x} porque {razón})
Node:           {instalado} — LTS vigente {v} {✅ | ❌ hay que actualizar}
Gestor:         npm · pnpm · yarn · bun                     (recomiendo {x})
Módulos:        ESM (recomendado en proyectos nuevos) · CommonJS
Lenguaje:       TypeScript (recomendado) · JavaScript
Datos:          Prisma · Drizzle · TypeORM · Mongoose · ninguno   + base: PostgreSQL · MySQL · SQLite · MongoDB
Validación:     Zod · class-validator (Nest)
Tests:          Vitest (por defecto en Nest 12 con ESM) · Jest 30 · node:test   + supertest
Base local:     Docker Compose (recomendado) · instalada en el sistema
Carpeta:        {ruta} {vacía ✅ | con archivos ⚠️}
Rama base:      {la que digas}
```

Para un proyecto **existente** se pregunta solo lo que falta, con lo que se va a añadir y por qué.

### Paso 3 — Montarlo (delegado a `eden:node-devops`)

Con el encargo de cinco partes y el sí del dev explícito en él (incluida la lista de dependencias):

- **NestJS nuevo:** `nest new` vigente con el gestor elegido; `ValidationPipe` global con `whitelist` y
  `forbidNonWhitelisted`; `@nestjs/config`; el ORM elegido; tests unitarios y e2e.
- **Express o Node nuevo:** `package.json` con la estructura acordada (`src/app.ts` separado de
  `src/server.ts` para poder testear la app sin levantar el puerto), middleware de errores, validación,
  cabeceras de seguridad, el ORM y los tests con supertest.
- **Todos:** TypeScript estricto, ESLint flat config, scripts del kit, `.env.example`, `.gitignore`,
  `engines`/`.nvmrc`, `docker-compose.yml` con la base local y la de tests.
- **Existente:** solo los huecos aprobados.

### Paso 4 — Verificar y declarar

1. `install` con el lockfile, `lint`, `typecheck`, `test`, `build`; la base local arriba y la migración
   inicial aplicada **en local**: la salida real de cada uno.
2. `dev` arranca y un endpoint de salud responde.
3. Escribe en `.claude/project-config.json`: `project.stack: "node"` y el bloque `node` (`flavor`,
   `package_manager`, `node_version`).
4. En el `CLAUDE.md` del proyecto, el marcador `<!-- eden-stack: node -->` y una línea con el sabor.

### Paso 5 — Reporte

```
🟩 SETUP NODE — LISTO

Sabor: {nest | express | node} {v} · Node {v} (LTS hasta {fecha}) · {ESM | CJS} · gestor {x} · ORM {x} · base {x}
Scripts: dev ✅ · build ✅ · lint ✅ · typecheck ✅ · test ✅ · test:e2e {✅ | —}
Verificación: {salida resumida de cada comando}
Declarado: project-config.json (node.flavor = {x}) · CLAUDE.md
Pendiente del dev: {.env real, servicios externos, el deploy}

➜ Siguiente: /eden:node para la primera tarea, o /eden:node-api para un endpoint.
```
