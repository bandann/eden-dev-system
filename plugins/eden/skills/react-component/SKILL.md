---
name: react-component
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:react-component`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:react` o
  `/eden:go` con su confirmación. NO lo actives porque haya que tocar un componente: si no lo pidió por
  su nombre, se trabaja de forma normal. — Qué hace cuando SÍ se invoca: crea o modifica UN componente
  React (SPA o Next) reuse-first: inventaría lo que existe y su blast radius, mide el diseño en Figma
  (caché primero), escribe primero el test, implementa con los tokens del proyecto, accesible y con
  todos sus estados, y lo verifica 1:1. Nueva prop en un componente compartido = default neutro. No
  commitea.
argument-hint: "<componente | ruta> [| url-figma | url-ticket] [| qué debe hacer / qué NO tocar]"
disable-model-invocation: true
---

## React Component — un componente, bien hecho

Argumento recibido: `$ARGUMENTS`

Para cuando el trabajo es **un componente**: crear uno, o cambiar uno que ya existe sin romper a quien
lo usa. Es el equivalente React de `create-new-section` + `section-mod`. Usa el equipo React
(`teams/react/roster.md`) por rol.

> **Idioma:** al dev, en español. Código, tests y docs, en inglés.

### Paso 1 — Entender el pedido

De `$ARGUMENTS` y, si hay, del ticket (`task.read`) y del Figma: qué componente, qué debe hacer, en qué
sabor (`spa` o `next`, de `project-config.json` o `eden_stack.py detect`) y **qué no se toca**. Si falta
algo que cambia el resultado, se pregunta **una vez**, todo junto.

### Paso 2 — Lo que ya existe (delegado)

En paralelo, en un solo turno:

- `eden:react-architect` → `inventory` del componente (o de los candidatos a reutilizar) +
  `blast-radius`: quién lo importa, en qué rutas, qué tests lo cubren.
- `eden:figma-extractor` → Design Spec por breakpoint, **caché de diseño primero**
  (`rules/on-demand/eden-design-cache-rules.md`).

### Paso 3 — El escalón y el plan

Escalera reuse-first de `rules/react/eden-react-rules.md`: tal cual · composición o variante · prop
nueva con default neutro · código acotado · componente nuevo. Se declara el escalón y **por qué no
alcanza el anterior**. En Next, también: **¿de servidor o de cliente?** (cliente solo si necesita
estado, efectos, eventos o APIs del navegador).

```
⚛️ COMPONENTE — {nombre}

Escalón: {n} — {por qué}
Archivos: {lista cerrada}
Servidor / cliente: {…}
Props: {nuevas o cambiadas, con su default}
Estados: carga · vacío · error · deshabilitado · {los del diseño}
Consumidores: {n} — {riesgo}
Tests (primero): {qué criterios}
Queda fuera: {…}

¿Le doy?
```

Espera el sí.

### Paso 4 — Test primero, luego el componente

1. `eden:react-tester`: los tests del componente desde el criterio de aceptación → **rojo**, por la
   razón correcta.
2. `eden:react-data-dev` si el componente necesita un hook de datos nuevo (con su contrato tipado).
3. `eden:react-ui-dev`: el componente, hasta **verde**, con los tokens del proyecto, accesible y con
   todos sus estados.
4. Si hay Figma: `eden:design-auditor` en loop medir → corregir → medir hasta 1:1, o hasta dejar
   escrito qué falta y por qué.

Revisa el diff real de cada handoff; un `DECISIÓN PENDIENTE` se le lleva al dev tal cual.

### Paso 5 — Verificar y reportar

`eden:react-qa-reviewer` sobre el diff (lint, typecheck, tests, build) y, si el componente es
compartido, el grep de consumidores otra vez.

```
⚛️ COMPONENTE — {nombre} — LISTO

Escalón: {n} · Archivos: {…}
Tests: {n} ✅ · lint ✅ · typecheck ✅ · build ✅
Fidelidad: {1:1 en 375/768/1440 | deltas: …}
Consumidores: {siguen igual — verificado cómo}
No verificado: {…}

➜ /eden:turnoff-task para cerrar, o sigue con el siguiente componente.
```

No commitea ni pushea.
