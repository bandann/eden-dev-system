---
name: estimate-time
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:estimate-time` o lo pide de forma explícita e inequívoca. NO lo actives porque se
  hable de plazos, tiempos o de cuánto va a tardar algo: si no lo pidió por su nombre, no se usa. — Qué
  hace cuando SÍ se invoca: estima el tiempo de una tarea del tracker y carga el estimado en ella.
  Descompone por subtarea, y si es una página, sección por sección. Cada estimación incluye desarrollo
  **y pruebas** —las automatizadas del kit y el QA manual del dev— más el cierre y un margen declarado.
  Se apoya en el tiempo real de tareas parecidas ya cerradas, no en intuición. Propone la tabla y espera
  aprobación antes de escribir nada en el tracker.
argument-hint: "<url-del-ticket> [| contexto que ayude a estimar]"
disable-model-invocation: true
---

## Estimation Time — estimar con base, no a ojo

Argumento recibido: `$ARGUMENTS`

Una estimación inventada es peor que ninguna: compromete al equipo con un número que nadie puede
defender. Este skill estima **a partir de lo que ya pasó** —cuánto tardaron de verdad tareas parecidas—
y declara en qué se apoya cada número.

> **Idioma:** al dev, en español. Lo que se escriba en el tracker, en inglés.

**Lo que NO hace sin permiso:** escribir en el tracker. Propone la tabla completa y **espera tu
aprobación**; cargar estimados es visible para todo el equipo y condiciona la planificación.

**Modelos:** la recolección de histórico y el análisis del Figma se delegan a agentes (nivel `fast`) con los
roles `explorer` y `design-extractor`; la sesión principal decide los números y habla contigo.
Los agentes se resuelven por rol con el roster del stack del proyecto (`teams/{stack}/roster.md`, ver
`rules/eden-team-rules.md`); si el stack no tiene roster, se usa `teams/_generic/roster.md`.

---

### Paso 1 — Entender qué se estima

Con las operaciones del tracker (`rules/eden-tracker-rules.md`):

```
task.read       → la tarea y sus campos
task.subtasks   → sus subtareas
task.comments   → contexto que cambia el alcance
```

Y clasifica **qué tipo de estimación es**, porque cambia todo lo demás:

| Si la tarea es… | Se estima |
|---|---|
| **Una página completa** | **Sección por sección**, por separado, y se suma |
| **Con subtareas** | **Cada subtarea** por separado — el padre es la suma, no una estimación propia |
| **Una sección o cambio puntual** | Una sola unidad |
| **Un bug** | Aparte: la investigación es la parte impredecible (ver `references/how-to-estimate.md`) |

**Si el alcance no está claro, no estimes.** Un número sobre un alcance difuso es una promesa que se
rompe sola. Pregunta primero.

---

### Paso 2 — Buscar la base: qué tardó lo parecido

Esto es lo que separa una estimación de una adivinanza. **Antes de proponer ningún número:**

```
time.list       → tiempo REAL registrado en tareas cerradas parecidas
task.history    → cuánto estuvo en In Progress y en Review (el rework se ve aquí)
task.search     → tareas cerradas del mismo tipo en este proyecto o en otros
/eden:memory recall {tipo de sección}  → qué nos pasó antes con algo así
```

Y del proyecto:

- **`docs/sitemap.md`** — si la sección está marcada ♻️ *reusable*, el tiempo es una fracción del de una
  🆕 *to-build*. Es el dato que más mueve la estimación.
- **El Figma** — número de elementos, breakpoints, estados y animaciones. Un hero con dos textos y un
  botón no es un carrusel filtrable.
- **El blast radius** — tocar algo usado en 20 páginas multiplica el QA, no el desarrollo.

Método completo en `references/how-to-estimate.md`.

---

### Paso 3 — Descomponer cada unidad

**Nunca un número único.** Cada sección o subtarea se descompone, porque es lo que hace la estimación
revisable — y lo que explica por qué "dos horas de desarrollo" nunca son dos horas:

| Fase | Qué incluye |
|---|---|
| 🔍 **Análisis** | Leer el ticket, extraer el Figma, decidir el escalón reuse-first, escribir el baseline |
| 🛠️ **Desarrollo** | Escribir el código hasta que el test pasa |
| 🧪 **Pruebas del kit** | `test-visual` + `test-code` y **el loop de corrección** hasta verde |
| 👤 **QA del dev** | Tu revisión manual en los breakpoints, en los navegadores, y los estados |
| 📦 **Cierre** | Auditoría, PR, comentario del ticket |
| ⚠️ **Margen** | La incertidumbre, **declarada y visible** — nunca escondida dentro de las otras fases |

El loop de corrección es la fase que más se subestima: no se acaba al escribir el código, se acaba
cuando el test está en verde. Y el **QA del dev es tiempo del proyecto**, aunque no lo hagas tú: si no
está en la estimación, el plazo miente.

---

### Paso 4 — Proponer, con la confianza declarada

```
⏱️ ESTIMACIÓN — {ticket} · {título}

{Sección / subtarea}          Análisis  Desarrollo  Tests kit  QA dev  Cierre  Margen  TOTAL
─────────────────────────────────────────────────────────────────────────────────────────────
1. hero-banner                  0:30      2:00        1:00      0:30    0:20    0:30    4:50
   ♻️ reusable desde `hero` · 2 breakpoints · sin animación
   📊 Base: CU-86ab tardó 4:15 en algo equivalente · confianza ALTA

2. product-carousel             1:00      5:00        1:30      1:00    0:20    2:00   10:50
   🆕 to-build · 3 breakpoints · filtros + animación
   📊 Base: nada parecido cerrado · confianza BAJA → rango 8:00–14:00

─────────────────────────────────────────────────────────────────────────────────────────────
TOTAL                           1:30      7:00        2:30      1:30    0:40    2:30   15:40
                                                                        Rango: 13:00–20:00

📊 Confianza global: MEDIA — {n} de {n} unidades tienen histórico comparable

⚠️ Lo que puede mover esto
   · {riesgo concreto y cuánto costaría}
   · {hueco del diseño sin resolver}

❓ Supuestos
   · {lo que asumí y que si es falso cambia el número}

¿Cargo estos estimados en el tracker?
```

Reglas del formato:

- **Cada unidad con su base.** "4:50 porque CU-86ab tardó 4:15 en algo equivalente" es defendible;
  "4:50" solo, no.
- **Confianza explícita por unidad**: ALTA (hay histórico directo), MEDIA (hay parecido), BAJA (nunca
  hicimos algo así).
- **Confianza BAJA se entrega como rango**, no como número. Fingir precisión donde no la hay es la
  forma más rápida de perder la confianza del PM.
- **El margen va en su columna.** Inflar las otras fases para cubrirse hace la estimación imposible de
  revisar y de aprender de ella.

---

### Paso 5 — Cargar en el tracker (solo con tu sí)

Con la aprobación:

```
task.estimate    → estimado en CADA subtarea (adaptador en rules/eden-tracker-rules.md)
```

Si el tracker no tiene un campo de estimación escribible (o el proyecto no lo definió), se declara en
una línea y el desglose completo va solo como comentario (`task.comment`), para que el dev lo cargue.

- **Cada subtarea lleva su propio estimado.** El padre queda como la suma — si el tracker no la calcula
  solo, se carga la suma en el padre y se dice.
- Si una tarea **ya tenía estimado**, no se pisa en silencio: se muestra el anterior y el nuevo, y lo
  decides tú.
- El desglose por fases va como **comentario en inglés** en la tarea, para que el PM vea de dónde sale
  el número — no solo el total.

Y se guarda el desglose en `.claude/context/estimate-{ticket}.md` para poder compararlo con el tiempo
real al cerrar.

---

### Paso 6 — Cerrar el ciclo (lo que hace que mejore)

Una estimación sin comparación posterior nunca aprende. Al terminar la tarea, `turnoff-task` tiene el
tiempo real; entonces:

- Se compara estimado vs real, unidad por unidad.
- Si la desviación es significativa, **se guarda en memoria** (`/eden:memory save`): *"un carrusel con
  filtros tomó 14h, no 10 — la parte cara fue el loop de responsive"*.
- Eso alimenta la base del Paso 2 en la siguiente estimación.

Sin este paso, el kit estima igual de mal dentro de un año.

---

### Lo que nunca se hace

- **No se estima un alcance que no está claro.** Se pregunta.
- **No se inventa un histórico.** Si no hay tarea comparable, la confianza es BAJA y se dice.
- **No se esconde el margen** dentro de las otras fases.
- **No se omite el QA del dev.** Es tiempo del proyecto aunque no lo ejecute el kit.
- **No se cargan estimados sin aprobación** — condicionan la planificación de todo el equipo.
- **No se ajusta la estimación para que quepa en un plazo.** Si el número no cabe, eso es información
  para el PM, no un error a corregir.
