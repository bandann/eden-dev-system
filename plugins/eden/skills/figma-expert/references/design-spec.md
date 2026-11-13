# Design Spec — el contrato de implementación

El Design Spec es lo que convierte "pixel-perfect" en algo **verificable**. Se escribe **antes** de
implementar, y a partir de ahí:

- es la fuente de cada valor que se escribe en el código;
- es el baseline del test visual (`rules/eden-testing-rules.md` — el baseline se congela antes del
  código, o el test solo describe lo que se hizo en vez de verificar lo que se debía hacer);
- es lo que se recarga cuando la sesión larga descargó el detalle (`rules/eden-context-rules.md`).

**Se escribe en inglés** (`rules/eden-workflow-rules.md`). Vive en
`.claude/context/design-spec-{sección}.md` y se declara en `.claude/context/INDEX.md`.

**Y sobrevive a la tarea en la caché de diseño** (`rules/on-demand/eden-design-cache-rules.md`): el
mismo spec en JSON —misma estructura que el YAML de abajo, más `source.file_key` y `source.node_id`—
se guarda con `eden_design.py save` en la memoria del proyecto. Así la próxima tarea sobre esa sección
no vuelve a leer Figma si nadie lo tocó, y si lo tocaron, sabe exactamente qué cambió.

---

## Formato

Un bloque por componente, y dentro, un bloque por breakpoint. Solo valores **medidos** — un campo que no
se pudo medir se escribe como `unmeasured` con su motivo, nunca con un número plausible.

```yaml
# design-spec-hero.md
source:
  figma_file: "{nombre del archivo}"
  node_id: "{id}"
  extracted: 2026-09-17
  breakpoints: [390, 768, 1440]

hero:
  container:
    390:  { width: 390,  height: 520, padding: [40, 20, 40, 20], gap: 24 }
    1440: { width: 1440, height: 720, padding: [96, 120, 96, 120], gap: 32 }
    content_max_width: { 390: 350, 1440: 1200 }
    background: token(--color-background-accent)

  title:
    element: h1
    font_family: token(--font-heading--family)
    390:  { font_size: 36, line_height: 40, letter_spacing: -0.5, font_weight: 700 }
    1440: { font_size: 64, line_height: 68, letter_spacing: -1,   font_weight: 700 }
    color: token(--color-foreground)
    max_width: { 1440: 720 }

  button:
    390:  { width: fill, height: 48, radius: 24, padding_x: 24 }
    1440: { width: 180,  height: 52, radius: 26, padding_x: 32 }
    background: token(--color-primary)
    label: token(--font-body--family) / 16 / 600

  image:
    390:  { asset: hero-mobile.jpg,  ratio: "4/5",  object_position: "50% 30%" }
    1440: { asset: hero-desktop.jpg, ratio: "16/9", object_position: "50% 50%" }

breakpoint_deltas:
  - "La imagen es OTRA en mobile (4/5 vs 16/9), no la misma recortada."
  - "El botón pasa de ancho fijo (1440) a llenar el contenedor (390)."
  - "El título baja de 64/68 a 36/40 — requiere control de tamaño por breakpoint."

states:
  button:
    hover:   { background: token(--color-primary-dark) }
    focus:   "no definido en Figma — se implementa el foco accesible del proyecto"
    disabled: unmeasured  # el diseño no lo dibuja; preguntar al diseñador
```

---

## Reglas del spec

- **Los colores se escriben como token**, no como hex. Si el hex del Figma no corresponde a ningún token
  del proyecto, se anota como hueco y se sigue el proceso del proyecto para añadirlo — no se cuela un
  valor crudo (`rules/eden-design-rules.md`).
- **Los cuatro lados del padding, por separado.** Un `padding: 24` que en realidad era `24 20 32 20` es
  una diferencia que aparecerá en la validación y costará el doble encontrar.
- **`breakpoint_deltas` no es opcional.** Es la sección que evita el fallo más común: implementar
  desktop y dejar que mobile herede.
- **Lo no definido se marca**, no se rellena. `unmeasured` con el motivo, y se pregunta.
- Una vez escrito, **el spec manda sobre la memoria**: ante una duda de medida a mitad de la
  implementación, se lee el archivo; no se recuerda.

---

## Cuando el diseño cambia

Si el Figma se actualiza a mitad del trabajo, **el spec se vuelve a derivar desde Figma** — no se edita
a mano para que cuadre con lo implementado. Al guardarlo, `eden_design.py save` devuelve la lista de
cambios contra el anterior: es lo que se le enseña al dev. Ajustar el baseline para que el test pase es exactamente lo
que `rules/eden-testing-rules.md` prohíbe.
