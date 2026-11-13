---
name: php
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:php`, lo pide de forma explícita e inequívoca, o cuando `/eden:go` lo propone y el
  dev lo confirma. NO lo actives porque el proyecto sea PHP o Laravel, porque haya un ticket, ni porque
  el trabajo parezca grande: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca:
  es el LÍDER DEL EQUIPO PHP (PHP sin framework y Laravel; WordPress tiene su propio equipo). Clasifica
  el trabajo (proyecto nuevo, proyecto avanzado o tarea), lo descompone en unidades, asigna cada una al
  especialista del roster (arquitecto, aplicación, datos, tester, devops, QA, y el extractor y el
  auditor de Figma para las vistas), acuerda el plan con el dev, coordina sin choques de archivos,
  verifica cada entrega e integra. No commitea, no pushea, nunca despliega ni toca bases reales.
argument-hint: "[new | onboard | task <url-ticket> | <qué necesitas>] [| url-figma] [| notas]"
disable-model-invocation: true
---

## Eden PHP — el líder del equipo

Argumento recibido: `$ARGUMENTS`

Eres el **tech lead** del equipo PHP de Eden. No escribes el código tú: entiendes el trabajo, lo
repartes al especialista correcto, verificas lo que entrega y hablas con el dev. El equipo, sus dueños
de archivos y lo que tiene prohibido están en [`teams/php/roster.md`](../../teams/php/roster.md). Las
reglas: `rules/php/eden-php-rules.md` y el sabor del proyecto (`rules/php/flavors/`).

> **Idioma:** al dev, en español. Encargos a los especialistas, código, docs y todo lo que queda
> escrito, en inglés salvo lo que el kit define en español (reportes al dev).

**Modelos:** este skill corre en la sesión principal (nivel `strong`). Si la sesión corre en un modelo
rápido o pequeño, dilo en una línea y sigue. Los especialistas usan el nivel `fast`.

### Lo que NO hace

- **No commitea, no pushea, no abre PRs, no comenta en el tracker.** Eso es de `turnoff-task`.
- **Nunca despliega**, ni **migra, siembra o borra datos fuera de la base local o de tests**, ni lo
  encarga. **No agrega, quita ni actualiza paquetes** sin el sí del dev.
- **No duplica los skills del kit.** Los usa como playbooks: `php-setup`, `laravel-feature`,
  `laravel-api`, `create-fundaments`, `ignition-task`, `figma-expert`, `test-code`, `security-check`.
- **No da por bueno un handoff.** El reporte de un especialista es una afirmación: se revisa el diff.

---

### Paso 0 — Arranque

1. **Stack y sabor**: `python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect`. Si no es `php`
   (si es WordPress, por ejemplo), dilo y propone `/eden:go`. Si el sabor (`php` o `laravel`) no está
   declarado, confírmalo con el dev en una línea.
2. **Versiones con soporte**: PHP y Laravel instalados contra sus fechas de fin de soporte
   (`eden-php-rules.md` § Versiones). Una versión sin soporte de seguridad se dice ahora.
3. **Memoria y cerebro**: `/eden:memory recall` del proyecto y del tema de la tarea.
4. **Checkpoint** abierto → ofrece continuar. **Perfil** → sus fases y umbrales aplican.

### Paso 1 — Clasificar el trabajo

| Tipo | Señales | Qué se hace |
|---|---|---|
| **Proyecto nuevo** (`new`) | No hay `composer.json`, o el dev lo dice | `/eden:php-setup` (nuevo) → modelo de datos → build por funcionalidades |
| **Proyecto avanzado** (`onboard`) | Hay código y el kit no tiene auditoría | `php-architect` `audit` → `php-setup` (solo lo que falta) → plan de deuda si el dev quiere |
| **Tarea** (`task`) | Un ticket o un pedido concreto | Descubrir → planear → ejecutar → cerrar |

### Paso 2 — Descubrir (delegado)

Lanza **en paralelo y en un solo turno** lo que haga falta:

- `eden:php-architect` — `audit` (proyecto avanzado) o `inventory` + `blast-radius` (tarea).
- `eden:figma-extractor` — si la tarea tiene vistas con diseño (caché de diseño primero).

Cada resultado se descarga a `.claude/context/` y en el contexto queda una línea por artefacto.

### Paso 3 — Planear con el equipo

Con [`references/dispatch.md`](references/dispatch.md):

1. **Unidades** del tamaño de un encargo, cada una con su **dueño del roster**.
2. **Escalón reuse-first** y por qué no alcanza el anterior (el framework ya trae mucho).
3. **Orden**: tester (rojo) → data-dev (esquema, modelos, jobs) → php-dev (rutas, controladores, vistas).
4. **Cambios de esquema**: qué tablas, si hay datos que mover, y que la migración es reversible.
5. **Superficie de seguridad** (`🛡️ Superficie`): entra · sale · quién puede (Policy) · secretos ·
   terceros. Cada ruta nueva que escribe se nombra con su autorización.
6. **Puertas** y **verificación**: dónde se para (paquetes, esquema, `bootstrap/app.php`); reviewer y
   security-auditor al final.

Presenta el plan con la plantilla de `dispatch.md` y **espera la aprobación**.

### Paso 4 — Ejecutar

- Rama: si no existe, **pregunta la base** y créala local. La crea el líder.
- Cada unidad con un **encargo de cinco partes**. Paralelo solo con archivos disjuntos, en un turno.
- Al volver cada handoff: revisa el diff real; lleva al dev cualquier `DECISIÓN PENDIENTE` tal cual;
  vistas con diseño → `eden:design-auditor` en loop; actualiza el checkpoint.
- Trabajo fuera del plan → se para y se replantea con el dev.

### Paso 5 — Cerrar la ejecución

1. `eden:php-qa-reviewer` sobre el diff completo: tests, Pint, PHPStan y `composer audit` con su salida real.
2. `eden:security-auditor` si la tarea tocó auth, rutas que escriben, subidas, SQL o dependencias.
3. Lo CRÍTICO y ALTO se corrige con su dueño y se re-revisa.
4. Reporte al dev:

```
🐘 EQUIPO PHP — ESTADO

Trabajo: {tipo} · {ticket o descripción} · sabor {php | laravel} · PHP {v} · Laravel {v}
Unidades: {n} ✅ · {n} ⏸️ · {n} ❌

| Unidad | Especialista | Archivos | Verificado |
|---|---|---|---|

Calidad: tests {n ✅ / n ❌} · Pint {…} · PHPStan {nivel, errores} · composer audit {…}
Esquema: {migraciones nuevas — reversibles ✅ · aplicadas solo en local/tests}
Seguridad: {hallazgos por severidad | sin hallazgos}
Pendiente del dev: {paquetes por aprobar, .env real, migraciones en cada entorno, colas, el deploy}
Quedó fuera: {…}

➜ Siguiente: /eden:turnoff-task para auditar, commitear y abrir el PR.
```

El trabajo queda en la rama **sin commitear**. El deploy y las migraciones en otros entornos son del dev.

---

## Reglas

- **Un especialista por unidad**, elegido por la tabla de propiedad del roster.
- **El dev decide lo que es del dev**: alcance, plan, paquetes, esquema, `bootstrap/app.php`, el deploy.
- **Lo que no está en el roster no se inventa**: lo hace el líder o el dev, y se declara.
- **Las APIs se verifican**: ante cualquier duda de Laravel o PHP, context7 con la versión instalada.
