# Roster Motion — el equipo de animación (transversal)

Líder: **`/eden:motion`** (skill, sesión principal). No es un stack: trabaja **dentro** del stack del
proyecto (Shopify, WordPress, React, PHP…) y respeta su roster, su propiedad de archivos y su módulo de
reglas. Reglas del equipo: `rules/eden-motion-rules.md`. Contrato común: `rules/eden-team-rules.md`.

## Roles → agentes

| Rol | Agente | Cuándo entra |
|---|---|---|
| `explorer` | `eden:motion-architect` (modo `inventory`) | Antes de tocar animaciones que existen |
| `architect` | `eden:motion-architect` (modo `audit` / `decide`) | Qué cuesta lo que hay; qué escalón usar para lo nuevo |
| `motion` | `eden:motion-dev` | Implementar o reescribir una animación aprobada |
| `quality-auditor` | `eden:motion-perf-auditor` | Medir en el navegador (fps, cuadros lentos, tareas largas, layout, CLS, input) y el análisis estático; antes y después en cada optimización |
| `design-auditor` | `eden:design-auditor` | Si hay Figma o un prototipo con la animación: medir el resultado |
| `reviewer` | el `reviewer` del roster del stack | Revisión del diff con `eden-motion-rules.md` como checklist |

## Propiedad de archivos

El equipo de motion **no tiene archivos propios**: escribe en los del stack, con la tabla de propiedad de
ese roster. Cuando una unidad de animación cae en un archivo de otro dueño (p. ej. `assets/*.js` de
`eden:shopify-js-dev`), el líder la asigna a `eden:motion-dev` **con ese archivo nombrado en el encargo**
y nunca en paralelo con su dueño. Agregar una librería (`package.json`, un `<script>` en el layout,
`wp_enqueue_script`) es una decisión del dev y del líder del stack.
