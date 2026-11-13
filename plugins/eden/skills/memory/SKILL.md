---
name: memory
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:memory` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable de
  recordar algo o de algo que ya pasó: si no lo pidió por su nombre, no se usa. (Los otros comandos del
  kit sí leen y escriben memoria por su cuenta — eso es parte de su flujo.) — Qué hace cuando SÍ se
  invoca: gestiona la memoria de cuatro capas del kit. `recall` recupera lo que sabemos de un tema;
  `save` guarda un hecho, un episodio o un procedimiento; `consolidate` destila la memoria de trabajo al
  cerrar; `promote` propone pasar conocimiento local a global; `status` muestra qué hay y qué está
  dudoso. Global siempre con aprobación del dev.
argument-hint: "recall <tema> | save | consolidate | promote | status"
disable-model-invocation: true
---

## Eden Memory — la memoria del kit

Argumento recibido: `$ARGUMENTS`

Cuatro capas, dos ámbitos. El modelo completo está en `rules/eden-memory-rules.md`; esto es cómo se opera.

```
~/.claude/eden-memory/          GLOBAL — todos los proyectos · se escribe CON APROBACIÓN
└── MEMORY.md · semantic/ · procedural/ · episodic/

{proyecto}/.claude/memory/    LOCAL — este cliente · se escribe automáticamente
└── MEMORY.md · semantic/ · procedural/ · episodic/

{proyecto}/.claude/checkpoint.md    TRABAJO — la tarea en curso
```

> **Idioma:** al dev, en español. **Las entradas de memoria se escriben en inglés** — quedan escritas y
> las lee todo el equipo.

---

### `recall <tema>` — qué sabemos de esto

Antes de construir algo, mirar si ya lo aprendimos. Lo usan los otros comandos al arrancar.

```bash
grep -rin "{tema}" ~/.claude/eden-memory/ .claude/memory/ 2>/dev/null
cat ~/.claude/eden-memory/MEMORY.md .claude/memory/MEMORY.md 2>/dev/null
```

Busca en las tres capas permanentes y **presenta lo relevante, no todo lo que hizo match**:

```
🧠 LO QUE SABEMOS — {tema}

📌 Hechos (semántica)
   · {hecho} — verificado en {dónde}, {cuándo}

🔧 Procedimientos
   · {receta} — usada {n} veces

📅 Ya nos pasó (episódica)
   · {fecha} · {proyecto} — {qué pasó} → {cómo se resolvió}

⚠️ Sin verificar desde hace tiempo
   · {entrada} — última confirmación {fecha}
```

Si no hay nada, **dilo**: "no tengo memoria sobre esto". Un `recall` que inventa contexto es peor que
uno vacío.

---

### `save` — guardar algo

Clasifica primero, **pregunta la capa solo si es ambiguo**:

| Lo que te dan | Capa |
|---|---|
| "Esto pasó y se resolvió así" | Episódica |
| "En este tema/plataforma las cosas son así" | Semántica |
| "Para hacer X, la secuencia es esta" | Procedural |

Y el ámbito:

- **¿Es de este cliente?** → local, se guarda directo.
- **¿Aplica a cualquier proyecto del stack?** → global, **se propone y espera el sí**.

Antes de escribir, comprueba dos cosas:

1. **¿Ya está en el repo, en `docs/` o en git?** Si sí, no se memoriza: se cita. Duplicar conocimiento
   lo desincroniza.
2. **¿Ya existe una entrada parecida?** Si sí, se **actualiza** esa, no se crea otra. Dos entradas sobre
   lo mismo acaban contradiciéndose.

Formato de entrada y frontmatter en `rules/eden-memory-rules.md`. Toda entrada lleva **de dónde salió y
cuándo se verificó**.

---

### `consolidate` — destilar la memoria de trabajo

Se ejecuta al cerrar una tarea (`turnoff-task` lo invoca). Lee `checkpoint.md` y decide, punto por
punto:

```
🧠 CONSOLIDAR — {ticket}

📅 → Episódica (local)     {n}
   · {problema} → {causa} → {solución}

📌 → Semántica             {n}   {local | 🌍 global, requiere tu OK}
   · {hecho} — verificado al {cómo}

🔧 → Procedural            {n}
   · {receta}

🗑️ Se descarta             {n}
   · {lo que solo servía para esta tarea}

{Si hay candidatos globales:}
🌍 Para memoria global — ¿los promuevo?
   · "{hecho}" — visto en {proyectos}
```

**Lo local se escribe solo; lo global espera tu sí.** Después, el checkpoint se marca como finalizado.

**No consolides el checkpoint entero.** La pregunta que filtra: *¿esto le servirá a alguien dentro de
seis meses, en otro proyecto?* Si la respuesta es no, se descarta.

---

### `promote` — de local a global

Revisa la memoria local buscando lo que ya vale para todos:

- Hechos confirmados en **dos o más proyectos**.
- Hechos que son del **stack** (Horizon, Shopify, el tracker), no del cliente.

Presenta cada candidato con su evidencia y **espera aprobación uno por uno**. Con 40+ tiendas, promover
un caso particular como regla general lo propaga a todas — es exactamente el fallo que hace inservible
una memoria automática.

---

### `status` — qué hay y qué está flojo

```
🧠 MEMORIA

Global (~/.claude/eden-memory/)
   Semántica {n} · Procedural {n} · Episódica {n}
Local ({proyecto})
   Semántica {n} · Procedural {n} · Episódica {n}

⚠️ Revisar
   · {n} entradas sin verificar desde hace más de 6 meses
   · {n} contradicciones detectadas
   · {n} recetas procedurales usadas 3+ veces → deberían ser skill o regla
```

Ese último punto es el objetivo del sistema: **la memoria procedural es la antesala del kit**. Lo que se
repite deja de ser memoria y se convierte en skill o regla.

---

### Higiene

- **Un hecho equivocado es peor que ninguno.** Si algo resulta falso: se corrige o se borra.
- Si la memoria contradice al repo, **gana el repo** y se corrige la memoria.
- Nunca se guardan credenciales, tokens ni datos personales de clientes.
- La memoria global es **interna**: se comparte dentro de la organización, no fuera.
