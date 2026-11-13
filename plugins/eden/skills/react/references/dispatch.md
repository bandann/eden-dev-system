# Dispatch — cómo reparte el líder React

## 1. Partir en unidades

Una unidad = **un encargo para un especialista**: un resultado observable, un dueño, una lista cerrada
de archivos.

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Una prop nueva con default neutro, un ajuste de estilos | Un especialista (+ su test) |
| **M** | Un componente nuevo con estados, o una ruta con su carga de datos | tester → data-dev → ui-dev, con design-auditor en loop si es visual |
| **L** | Una pantalla completa o un componente compartido (header, layout, formulario largo) | Varias unidades M con dependencias declaradas |
| **XL** | Un proyecto o un rediseño | Se parte en lotes L por ruta o por feature |

Una unidad que cruza dueños **se parte**: test (tester) → datos (data-dev: hook, Server Action o route
handler, con el contrato tipado que va a recibir la UI) → UI (ui-dev).

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa | `eden:react-architect` |
| Componentes, estilos, páginas y layouts que renderizan | `eden:react-ui-dev` |
| Tokens del sistema de estilos (con `create-fundaments` o el sí del dev) | `eden:react-ui-dev` |
| Estado, fetching, clientes de API, validación; Server Actions, route handlers | `eden:react-data-dev` |
| Tests (primero), fixtures, e2e | `eden:react-tester` |
| Entorno, scripts, TypeScript, ESLint, config de build, CI | `eden:react-devops` |
| Figma → Design Spec | `eden:figma-extractor` |
| Medir Figma vs render | `eden:design-auditor` |
| Revisar el diff; calidad (Lighthouse, accesibilidad, SEO) | `eden:react-qa-reviewer` |
| Seguridad independiente | `eden:security-auditor` |

Layout raíz, providers globales y `proxy.ts`/`middleware.ts`: el líder decide el dueño y lo escribe en
el plan.

## 3. Plantilla del plan (al dev, en español)

```
⚛️ PLAN DEL EQUIPO REACT

Trabajo: {new | onboard | task} · {ticket / descripción} · sabor {spa | next}
Rama: {nombre} desde {base — preguntada}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | Tests de {x} | S | eden:react-tester | src/x/X.test.tsx | — | — |
| 2 | Datos de {x} | S | eden:react-data-dev | src/x/useX.ts | 3 — {por qué} | 1 |
| 3 | UI de {x} | M | eden:react-ui-dev | src/x/X.tsx, X.module.css | 4 | 1, 2 |

En paralelo: {…} · En secuencia: {1 → 2 → 3}
Server / client (Next): {qué es de servidor, dónde va 'use client'}
🛡️ Superficie: entra {…} · sale {…} · quién {…} · secretos {…} · terceros {…}
Verificación: design-auditor en {unidades visuales} · reviewer + security-auditor al final
Paro a preguntarte en: {dependencias nuevas, cambios globales, variables de entorno}
Blast radius: {consumidores y rutas — de architect}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: flavor {spa | next} (rules/react/flavors/{x}.md) · Design Spec .claude/context/design-spec-{x}.md ·
      tokens {…} · reuse step {n}: {why} · sibling pattern: {file} · consumers: {from architect} ·
      tests to make green: {files from the tester}
ACCEPT WHEN: {lint + typecheck + tests green; renders X at 375/768/1440; new prop default keeps current behaviour}
DO NOT: touch other files; add/remove/upgrade dependencies; deploy; put secrets in NEXT_PUBLIC_/VITE_;
        disable lint rules or tests; {unit-specific temptations}
HANDOFF: teams/react/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

- Solo unidades con **archivos disjuntos**, lanzadas **en un solo turno**, como mucho 4 a la vez.
- `tester` de la unidad siguiente puede ir en paralelo con el implementador de la actual.
- `design-auditor` y `figma-extractor` en primer plano (usan MCP).
