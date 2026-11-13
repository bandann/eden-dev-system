---
name: time-report
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:time-report` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable de
  horas, de cuánto llevas trabajando o de registrar tiempo: si no lo pidió por su nombre, no se usa. —
  Qué hace cuando SÍ se invoca: reporta tiempo trabajado en el tracker del proyecto. Reconstruye cuánto se trabajó y en
  qué —desde el cronómetro activo, el checkpoint, los commits y el tiempo en estado—, detecta lo que
  quedó sin registrar en días anteriores, y **SIEMPRE pregunta antes de cargar nada**: muestra la tarea,
  la duración y la fecha, y espera el sí del dev. Nunca registra tiempo por su cuenta.
argument-hint: "[nada | url-del-ticket | duración | fecha]"
disable-model-invocation: true
---

## Time Report — cargar tiempo en el tracker

Argumento recibido: `$ARGUMENTS`

El tiempo sin registrar es lo que más se olvida y lo que peor se reconstruye después. Este skill lo
reconstruye **con evidencia** y lo carga — pero **nunca sin preguntar**.

> **La regla que no se rompe:** este skill **siempre pregunta antes de cargar**. Muestra qué tarea, qué
> duración y qué fecha, y espera un sí explícito. El tiempo registrado es visible para el PM, entra en
> la facturación del cliente y corrige mal; cargarlo por iniciativa propia no es ayudar.

> **Idioma:** al dev, en español. La descripción de la entrada de tiempo, en inglés.

> **Tracker:** el tiempo se registra donde diga `tracker.time_provider` (vacío = el mismo que
> `tracker.provider`). Las operaciones `time.*` y `task.*` y su adaptador por tracker están en
> `rules/eden-tracker-rules.md`. Cuando la celda del adaptador es "—" (p. ej. Asana no tiene cronómetro
> por MCP), se declara en **una línea**, se usa el fallback (hora de inicio del checkpoint, commits,
> `task.history`) y se **reporta la duración al dev para que la cargue él**. Con `time_provider: smg-hub`
> y un ticket de Asana, `time.add` es `create-time-entry` con `externalLinkUrl` = permalink del ticket,
> contra el Hour Block activo del cliente, con los pasos de `time.add` de `rules/eden-tracker-rules.md`
> (orden activa → tipo de actividad → entrada), sin depender de otros plugins.

---

### Paso 1 — ¿Hay un cronómetro corriendo?

Lo primero, porque cambia todo lo demás:

```
time.current   → ¿hay un timer activo?
```

- **Sí, hay uno corriendo** → di cuál es la tarea y cuánto lleva. Pregunta si lo paras y lo registras
  (`time.stop`), o si lo dejas corriendo.
- **No hay ninguno** → se reconstruye el tiempo (Paso 2).

---

### Paso 2 — Reconstruir cuánto se trabajó y en qué

**No se inventa una duración.** Se arma con lo que hay, y se dice de dónde sale cada cosa:

| Fuente | Qué aporta |
|---|---|
| **`.claude/checkpoint.md`** | La hora de inicio que registró `ignition-task`, y qué unidades se cerraron |
| **Git** | Los commits del rango: primer y último commit acotan la ventana real de trabajo |
| **El tracker** | `task.history` — cuánto estuvo la tarea en In Progress |
| **El dev** | Lo que solo él sabe: pausas, reuniones, trabajo sin commits |

```bash
git log --author="$(git config user.email)" --since="{fecha} 00:00" --until="{fecha} 23:59" \
  --format='%h %cd %s' --date=format:'%H:%M' --all
```

**Los commits acotan, no miden.** Entre el primero y el último hubo comidas, reuniones y bloqueos. Se
propone la ventana y **el dev ajusta** — él es quien sabe cuánto de eso fue trabajo real.

Si no hay ninguna fuente, **se le pregunta directamente** cuánto quiere cargar. Mejor preguntar que
estimar mal un dato que va a facturación.

---

### Paso 3 — Detectar lo que quedó sin registrar

El valor real del skill. Revisa los últimos días laborales:

```
time.list      → qué hay registrado, por día
task.search    → en qué tareas trabajó según su estado y sus comentarios
```

Cruza contra los commits: **un día con commits y sin tiempo registrado es un hueco**. Se reporta:

```
⚠️ Días con actividad y sin tiempo registrado
   · {fecha} — {n} commits en {rama} · tarea probable {ticket}
   · {fecha} — tarea movida a Review, 0h registradas
```

Cada hueco se propone por separado y **se confirma por separado**. Cargar tres días de golpe con una
sola confirmación es exactamente cómo se registra mal.

---

### Paso 4 — Preguntar (el paso obligatorio)

**Nunca se salta.** Se muestra todo lo que se va a escribir, antes de escribirlo:

```
⏱️ TIEMPO A REGISTRAR

Tarea      {ticket} · {título}
Fecha      {fecha}
Duración   {Xh Ym}
Origen     {de dónde salió: cronómetro / commits de 09:14 a 13:40 / lo que dijiste}
Nota       {descripción en inglés que irá en la entrada}

{Si hay más de una:}
   2. {ticket} · {fecha} · {duración} · {origen}

Ya registrado ese día: {Xh}  →  quedaría en {Xh}

¿Lo cargo?  (sí / ajusta la duración / cambia la tarea / no)
```

Tres cosas que se muestran siempre, porque son las que evitan el error:

- **De dónde salió la duración**, para que el dev pueda corregirla con criterio.
- **Cuánto hay ya registrado ese día**, para no duplicar ni pasarse de la jornada.
- **La tarea exacta**, porque cargar horas en el ticket equivocado ensucia dos proyectos a la vez.

Si el dev responde con una duración distinta, **gana la suya, sin discutir**. Él estuvo ahí.

---

### Paso 5 — Cargar

Solo con el sí:

```
time.add    → tiempo de una sesión pasada
time.stop   → cerrar el cronómetro activo
```

Y confirma lo que quedó:

```
✅ REGISTRADO
   {ticket} · {fecha} · {duración}
   Total del día: {Xh}
```

Si la llamada falla, **se dice con el error real** — no se da por registrado algo que no se registró.

---

### Reglas

- **Siempre se pregunta antes de cargar.** Sin excepción, ni siquiera cuando la duración parece obvia.
- **Una confirmación por entrada.** Varias entradas, varias confirmaciones.
- **No se inventa la duración.** Se reconstruye con evidencia, se declara el origen y el dev ajusta.
- **No se registra tiempo de otro dev.** Solo del que está en la sesión.
- **No se borra ni se modifica** una entrada existente sin que el dev lo pida explícitamente.
- Si el perfil o el proyecto declara el tiempo como obligatorio, el skill **avisa** de los huecos
  aunque el dev no pregunte por ellos — pero sigue sin cargar nada solo.

---

### Relación con el resto del kit

- **`ignition-task`** arranca el cronómetro (o guarda la hora de inicio) al poner la tarea en marcha.
- **`turnoff-task`** reporta la duración al cerrar y la registra **tras confirmarla** — es el camino
  normal cuando una tarea se cierra completa.
- **`time-report`** es para todo lo demás: cargar tiempo a mitad de una tarea, recuperar días que se
  quedaron sin registrar, o corregir el registro de una jornada partida entre varios tickets.
- **`mydaily`** avisa de que hay tiempo sin registrar; **este skill es el que lo carga**.
