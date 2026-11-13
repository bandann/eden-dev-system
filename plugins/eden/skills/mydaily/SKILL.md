---
name: mydaily
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA O POR SU TAREA PROGRAMADA — NO LO ACTIVES POR TU CUENTA. Este skill se
  usa cuando el dev escribe `/eden:mydaily`, lo pide de forma explícita, o cuando lo dispara su rutina
  programada de lunes a viernes. NO lo actives porque empiece el día o porque se hable de pendientes: si
  no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: arma el reporte diario personal
  del dev cruzando el tracker, git y el checkpoint. Reconstruye qué se hizo el día laboral anterior, qué
  toca hoy, y qué bloqueantes hubo — los resueltos con **cómo** se resolvieron y los que siguen
  abiertos. Entrega cuatro bloques (Accomplished Today, Carried Over to Tomorrow, Tomorrow's Priority,
  Unresolved Blockers) **en español y en inglés**, listos para copiar y pegar — y, si el perfil del proyecto declara un formato de reporte de equipo, también en ese formato.
argument-hint: "[nada | fecha | notas que quieras añadir]"
---

## My Daily — el reporte diario del dev

Argumento recibido: `$ARGUMENTS`

Un reporte que el dev pueda copiar y pegar sin editarlo. Para eso tiene que estar **basado en evidencia**
—lo que el tracker y git dicen que pasó— y no en lo que parecería razonable que hubiera pasado.

> **Idioma:** la conversación contigo, en español. **El reporte se entrega en las dos versiones**,
> español e inglés, cada una completa y lista para pegar donde toque.

---

### Paso 1 — Fijar el rango

**"Ayer" es el último día laboral, no el día calendario anterior.**

| Hoy es | "Ayer" es |
|---|---|
| Martes a viernes | El día anterior |
| **Lunes** | **El viernes** |
| Después de un festivo o de días libres | El último día con actividad real |

Si el dev pasó varios días sin actividad, **cubre todo el hueco** — y dilo, en vez de reportar un día
vacío como si no hubiera pasado nada.

---

### Paso 2 — Recolectar la evidencia

Tres fuentes, en este orden:

**El tracker** (operaciones de `rules/eden-tracker-rules.md`; el provider se resuelve ahí)

```
task.search     → tareas del dev: qué cambió de estado en el rango
task.comments   → comentarios suyos y hacia él
time.list       → tiempo registrado ayer (en tracker.time_provider)
```

Si `time.list` no está disponible en el tracker de tiempo (celda "—" del adaptador), se declara en una
línea y el aviso de tiempo sin registrar se basa en commits y checkpoint.

Qué buscar: tareas movidas a Review o cerradas, tareas que **volvieron** de Review a In Progress (eso es
trabajo que reaparece), comentarios nuevos del PM o de QA sin responder, y tiempo sin registrar.

**Git** — lo que efectivamente se escribió:

```bash
git log --author="$(git config user.email)" --since="{fecha} 00:00" --until="{fecha} 23:59" \
  --oneline --all
git branch --show-current
git status --short
```

**El checkpoint** (`.claude/checkpoint.md`) — el estado real de la tarea en curso: qué unidades se
cerraron, cuáles quedaron a medias y qué estaba bloqueado.

---

### Paso 3 — Los bloqueantes (la parte que casi nadie escribe bien)

Un bloqueante mal reportado no sirve a nadie. Por cada uno:

| | Qué se registra |
|---|---|
| **Qué bloqueó** | En concreto, no "problemas con el header" |
| **Cuánto costó** | Si se puede estimar |
| **¿Se resolvió?** | Sí / No |
| **Si sí: CÓMO** | La solución concreta — esto es lo que evita que el equipo lo repita |
| **Si no: quién lo desbloquea** | Con nombre. "Esperando" no es un bloqueante útil; "esperando que el diseñador confirme el espaciado del hero" sí |

Los resueltos **no desaparecen del reporte**: van con su solución. Es la parte que convierte el reporte
diario en conocimiento del equipo en vez de en un trámite.

Y si un bloqueante resuelto dejó un aprendizaje que servirá dentro de seis meses, **propón guardarlo**
con `/eden:memory save` — así el reporte alimenta la memoria en vez de perderse en Slack.

---

### Paso 4 — Verificar antes de escribir

Antes de armar el reporte, comprueba y dilo si algo falla:

- [ ] ¿Hay tiempo sin registrar de ayer? — es lo que más se olvida
- [ ] ¿Alguna tarea terminada sigue sin moverse a Review?
- [ ] ¿Hay comentarios del PM o de QA sin responder?
- [ ] ¿El checkpoint refleja el estado real, o quedó desactualizado?

El reporte debe **reflejar** el tracker, no adelantarlo. Si hay desajuste, se arregla primero o se dice.

---

### Paso 5 — El reporte, en los dos idiomas

Se entregan **las dos versiones completas**, cada una en su bloque, listas para copiar:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DAILY — {Día, fecha}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇪🇸 ESPAÑOL

Logrado
    • {qué se completó — con el ticket entre paréntesis}
    • {…}

Se traslada a mañana
    • {qué quedó a medias, y en qué punto quedó}

Prioridad de mañana
    {una frase}

Bloqueantes
    ✅ Resuelto — {qué bloqueaba}
       Cómo: {la solución concreta}
    ⛔ Sin resolver — {qué bloquea}
       Espera: {qué se necesita} · Depende de: {quién}
    {o "Ninguno"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇬🇧 ENGLISH

Accomplished Today
    • {…}

Carried Over to Tomorrow
    • {…}

Tomorrow's Priority
    {one sentence}

Unresolved Blockers
    ✅ Resolved — {what was blocking}
       How: {the concrete fix}
    ⛔ Unresolved — {what is blocking}
       Waiting on: {what} · Owner: {who}
    {or "None"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**La versión en inglés no es una traducción literal** de la española: es el mismo contenido escrito con
naturalidad en cada idioma. Los nombres de tickets, ramas y archivos se conservan igual en ambas.

Después del reporte, y **fuera** de los bloques copiables, añade en español lo que el dev debería saber
antes de arrancar:

```
⚠️ Antes de empezar
   · {tiempo sin registrar de ayer}
   · {tarea devuelta por QA}
   · {comentario del PM sin responder}
   · {tarea vencida o para hoy}
```

---

### Paso 5b — El formato del equipo, si el perfil lo declara

Si el proyecto tiene un perfil activo con `daily_reports` (el formato que declare
`daily_reports`), añade **un tercer bloque copiable** con ese formato exacto — campos y orden tal
cual, porque alimenta el sistema que rastrea el progreso del equipo y la consistencia importa más que la
prosa:

```
AM UPDATE — [Day, Date]
Today's Focus: [una frase]
Key Tasks:
    • […]
Meetings: [lista o 'None scheduled']
Blockers: [lo que haya, o 'None']
```

Es el mismo contenido que ya reuniste, reordenado a la plantilla del equipo. Si el perfil no declara
formato, este bloque no se emite.

---

### Reglas

- **No se inventan logros.** Si algo quedó a medias, va en *Se traslada*, no en *Logrado*. Un reporte
  optimista que no coincide con el tracker cuesta más que uno honesto.
- **Cada punto con su ticket.** Un logro sin referencia no se puede verificar.
- **Los bloqueantes resueltos llevan el cómo.** Sin eso, el equipo repite el mismo tropiezo.
- **Los bloqueantes abiertos llevan dueño.** Si no sabes quién desbloquea, pregúntaselo al dev en vez
  de escribir "pendiente".
- **Lo que no puedas determinar, pregúntalo.** Las reuniones del día y la prioridad real las sabe el
  dev; propón lo que se deduce del tracker y deja que corrija.
- **El kit no publica el reporte.** Lo entrega para que el dev lo revise y lo pegue donde corresponda.

---

### Ejecución programada (lunes a viernes)

Este skill está pensado para correr **a primera hora, de lunes a viernes**. Eso lo hace una tarea
programada del sistema, no el skill por sí mismo: un skill se ejecuta cuando algo lo invoca.

Para dejarlo programado, el dev lo pide una vez y se crea la rutina (lunes a viernes, a la hora y zona
horaria que él indique). Al dispararse, el skill corre igual que si lo hubiera escrito, y **le deja el
reporte listo para revisar** — nunca lo publica solo.

Si la rutina se dispara un día sin actividad previa (vuelta de vacaciones, festivo), el reporte lo dice
en vez de entregar cuatro bloques vacíos.
