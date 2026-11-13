# Referencia — Orquestación del trabajo

El orquestador es quien decide **quién hace qué**. No escribe código: descompone, reparte, integra y
verifica. Su trabajo bien hecho se nota en que cada ejecutor recibe una tarea que puede completar sin
volver a preguntar.

## 1. Clasificar la complejidad

Se mide por **alcance** (cuántas unidades independientes) y **riesgo** (a quién más afecta), no por
cuánto código se escribe.

| | Alcance | Riesgo | Ejecución |
|---|---|---|---|
| **S** | 1 archivo, cambio local | Nulo — nada más lo consume | Directo, sin subagentes |
| **M** | 1 sección/componente | Contenido; schema aditivo con default neutro | `implementer` → `design-auditor` en loop → `reviewer` |
| **L** | Varias secciones/páginas o varias subtareas independientes | Medio | Un `implementer` por unidad **en paralelo** + integración + `reviewer` |
| **XL** | Alcance difuso, código compartido, migración, refactor transversal | Alto — rompe cosas en producción | **No se ejecuta directo.** Se parte en subtareas, se re-valida el alcance con el dev, y cada parte vuelve a entrar por esta tabla |

Señales de que subiste un nivel: hay que tocar un snippet/componente usado en otras páginas; hay que
cambiar el comportamiento por defecto de algo existente; el diseño no cubre todos los breakpoints; el
ticket usa palabras como "y de paso".

## 2. Descomponer en unidades de trabajo

Una unidad de trabajo es válida solo si tiene las cinco cosas:

1. **Qué** — el resultado observable, en una frase.
2. **Dónde** — la lista cerrada de archivos que puede tocar. Fuera de esa lista, no toca nada.
3. **Con qué** — el Design Spec del elemento, los tokens, lo reutilizable que ya se identificó.
4. **Acepta cuando** — criterio verificable (no "que quede bien").
5. **Qué NO hacer** — lo que está fuera de alcance y podría tentar.

Las subtareas del ticket se mapean 1:1 a unidades de trabajo. Si una subtarea es demasiado grande para
las cinco cosas, se parte otra vez.

Cada unidad lleva su **especialista asignado**, resuelto por rol con el roster del stack del proyecto
(`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`; sin roster, `teams/_generic/roster.md`). Las
unidades del `implementer` se parten según la tabla **"Propiedad de archivos"** del roster: cada unidad
tiene un solo dueño. Si una unidad cruza dos dueños, se parte en unidades secuenciales o se asigna al
dueño del archivo principal con un encargo explícito sobre el otro.

## 3. Paralelizar

Se paralelizan unidades cuyos **conjuntos de archivos no se cruzan** — el reparto por la tabla de
propiedad del roster lo garantiza. Si dos unidades tocan el mismo archivo, van en serie — dos agentes
escribiendo el mismo archivo se pisan.

Cuando lances varios ejecutores a la vez, lánzalos en un solo turno para que corran de verdad en
paralelo, y **verifica cada resultado** antes de integrarlo. El reporte de un agente es una afirmación,
no una verificación: se comprueba.

## 4. Los roles disponibles

El agente concreto de cada rol lo dice el roster del stack; aquí solo cuenta qué hace el rol.

| Rol | Hace | No hace |
|---|---|---|
| `implementer` | Escribe el código de UNA unidad de trabajo con alcance cerrado | Decidir alcance, tocar archivos fuera de su lista, abrir PRs |
| `design-auditor` | Mide Figma vs implementación real y reporta diferencias en píxeles por breakpoint | Arreglar el código |
| `reviewer` | Revisa el diff completo: bugs, regresiones, bleed, reglas, consola | Editar código |
| `quality-auditor` | Performance, accesibilidad y SEO de lo tocado | Editar código |

El loop de diseño es: implementar → auditar → corregir → auditar, hasta que el auditor no reporta
diferencias. El dev no debería ver un resultado que todavía no pasó ese loop.

## 5. Integración y responsabilidad

Después de repartir, el orquestador:

- Revisa que cada unidad hizo lo suyo **y solo lo suyo** (`git diff --stat`).
- Verifica que no hay bleed: estilos que se escapan, cambios de comportamiento en componentes
  compartidos, defaults de schema que alteran instancias existentes.
- Corre la validación del stack (Theme Check en Shopify, linters/tests donde aplique).
- Reporta al dev en español lo que se hizo, lo que falló, y lo que quedó fuera — **completo y honesto**.
  Si una unidad no se pudo completar, se dice; no se maquilla.

## 6. Cuándo se detiene todo y se pregunta

- El alcance real resultó mayor que el planeado.
- Hay que modificar algo compartido y el blast radius no es aceptable.
- El diseño y el ticket se contradicen.
- Una unidad requiere una decisión de producto.

Detenerse y preguntar cuesta minutos; adivinar cuesta un rollback.
