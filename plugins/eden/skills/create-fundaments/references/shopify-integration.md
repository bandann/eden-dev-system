# Referencia — Integrar los fundamentos en un tema Shopify

En Shopify **el tema ya tiene un sistema de tokens**: `config/settings_schema.json` define los ajustes,
y el tema los emite como CSS custom properties. Integrar los fundamentos aquí **no es crear un sistema
nuevo — es llenar el que ya existe** y añadir solo lo que falte.

> Regla que gobierna esta referencia: **primero se lee cómo lo hace este tema.** Lo de abajo es la
> buena práctica por defecto; si el tema hace otra cosa, gana el tema. Y la propuesta final siempre se
> le confirma al dev antes de escribir.

---

## 1. Inventario primero (antes de tocar nada)

```bash
ls config/settings_schema.json config/settings_data.json
grep -rn "color_scheme\|font_picker" config/settings_schema.json | head -40
grep -rln "\-\-color-\|\-\-font-" snippets/ layout/ assets/ | head
sed -n '1,120p' layout/theme.liquid
```

Lo que necesitas saber antes de decidir dónde va cada token:

- **Qué esquemas de color** define el tema (`color_scheme_group`) y cuántos hay.
- **Qué variables emite el tema y con qué nombres** — Horizon las genera en un snippet de variables
  (`snippets/theme-styles-variables.liquid` o equivalente); Dawn las emite en `layout/theme.liquid`.
  **Ese archivo suele ser generado a partir de los settings: no se edita a mano.**
- **Qué font pickers y qué escala tipográfica** existen.
- **Qué variables de espaciado/layout** derivan de settings (`--padding-*`, `--gap-*`, ancho de página).

---

## 2. La decisión de fondo: setting o CSS

Por cada fundamento del Figma, una pregunta:

> ¿Esto debe poder cambiarlo el merchant desde el editor de temas?

| Respuesta | Dónde va |
|---|---|
| **Sí** — paleta de marca, fuentes, escala tipográfica, ancho de página, radios globales | `config/settings_schema.json`, con el **default igual al valor del Figma** |
| **No** — tokens internos del sistema (escala de espaciado, elevaciones, tokens semánticos derivados) | Snippet propio de variables del proyecto |

**Esta es la parte que más se hace mal.** Hardcodear en CSS un color que el merchant debería controlar
rompe el editor de temas; y exponer como setting cada token interno llena el editor de ruido. Cuando
tengas duda de un fundamento concreto, es exactamente el tipo de cosa que se pregunta al dev.

---

## 3. Color — mapear a los esquemas del tema, nunca en paralelo

Los esquemas de color de Shopify (`color_scheme_group`) son el mecanismo nativo, y **cada sección los
consume** por su setting `color_scheme`. El design system de Figma casi siempre tiene el mismo concepto
con otro nombre (Light / Dark / Brand / Inverse).

Buena práctica:

1. **Mapea cada esquema del Figma a un esquema del tema**, uno a uno. Si el Figma tiene 4 y el tema 3,
   se agrega el que falta al `color_scheme_group` — no se inventa un mecanismo alternativo.
2. Rellena los roles del esquema (fondo, texto, botón, borde…) con los colores del Figma.
3. **Los componentes consumen las variables del esquema** (`var(--color-foreground)`,
   `var(--color-background)`, las que este tema emita). Nunca un hex, nunca un token propio paralelo
   que haga lo mismo.
4. Los **primitivos** de la paleta (la escala completa de marca, aunque el tema no la use entera) van
   documentados en `docs/design-system.md`; en código solo entran los que algo consume.

⚠️ **Cambiar el valor de un esquema existente repinta todas las secciones que lo usan.** Si un color de
Figma choca con uno ya configurado en `settings_data.json`, eso es un conflicto del Paso 5 del skill:
lo decide el dev, no se pisa.

---

## 4. Tipografía

- Las familias van por el **`font_picker`** del tema, con default en la fuente del Figma.
- Si la fuente del Figma **no está en la librería de Shopify**, se carga como asset con `@font-face` y
  se documenta en `docs/design-system.md` (incluida la licencia — es una pregunta para el cliente, no
  una decisión técnica).
- La **escala** (h1…h6, body, caption) se mapea a las variables que el tema ya emite
  (`--font-h1--size` y familia, según el tema). No se crea una escala paralela.
- **Mobile vs desktop:** si el Figma define tamaños distintos por breakpoint, se sigue el patrón del
  tema — pares de settings (`heading_size` / `heading_size_mobile`) o `clamp()` fluido. Esto se decide
  una vez, aquí, y todas las tareas posteriores lo heredan. Si el tema no tiene mecanismo responsive,
  **proponlo al dev** en vez de resolverlo con overrides sección por sección.

---

## 5. Lo que no cubre el tema — snippet propio

Todo lo que no tenga hueco en los settings del tema va a **un solo snippet del proyecto**, por ejemplo:

```
snippets/{prefix}-design-tokens.liquid
```

renderizado **una vez** en el `<head>` de `layout/theme.liquid`, **después** del snippet de variables
del tema (para que pueda derivar de él, no competir con él):

```liquid
{% render '{prefix}-design-tokens' %}
```

Contenido: un solo `:root` con los tokens que faltan, agrupados y comentados, derivando de las
variables del tema siempre que se pueda:

```liquid
<style>
  :root {
    /* Spacing scale — Figma 4pt */
    --{prefix}-spacing-xs: 0.25rem;
    --{prefix}-spacing-md: 1rem;

    /* Elevation */
    --{prefix}-shadow-card: 0 1px 3px rgb(from var(--color-foreground) r g b / 12%);

    /* Semantic — derivados del esquema del tema, no colores nuevos */
    --{prefix}-color-border-subtle: rgba(var(--color-foreground-rgb), 0.12);
  }
</style>
```

Convenciones:

- **Prefijo propio** (`--{prefix}-`) solo para lo que el tema no define. Así se distingue de un vistazo qué
  es del tema y qué agregó el proyecto.
- **Nada que el tema ya emita se redefine aquí.** Si existe `--color-foreground`, se usa; no se crea
  `--{prefix}-color-text`.
- Sin `!important`, sin pisar selectores del tema.

---

## 6. Espaciado, radios, sombras, breakpoints

- **Espaciado**: si el tema ya deriva paddings/gaps de settings, se mapea la escala del Figma a esos
  settings. Lo que sobre, al snippet propio.
- **Ancho de página / contenedor**: es un setting del tema. Se ajusta al valor del Figma, no se pisa por
  CSS en cada sección.
- **Radios y sombras**: normalmente no están en el tema → snippet propio.
- **Breakpoints**: Shopify no los define; se toman **los anchos exactos de los frames de Figma** y se
  escriben en `.claude/project-config.json`. Son la regla de medir del `design-auditor` (rol).

---

## 7. Verificación obligatoria antes de dar por hecho

1. **Theme Check** limpio sobre lo que se tocó.
2. **Ninguna página se ve distinta.** Los fundamentos son aditivos: si al integrarlos cambia el aspecto
   de una sección existente, es que se pisó un valor. Se revisa antes de continuar.
3. Los defaults que se agregaron a `settings_schema.json` **reproducen lo que la tienda ya mostraba** —
   salvo el valor que el Figma corrige y que el dev aprobó explícitamente.
4. `config/settings_data.json` es de la tienda: si hay que cambiar valores ahí, se declara y se
   confirma. Un cambio ahí es visible en producción.
5. Contraste WCAG AA en los pares texto/fondo de cada esquema de color; lo que no llegue, se reporta.

---

## 8. Lo que se le propone al dev (Paso 5 del skill)

Nunca una pregunta abierta tipo "¿dónde pongo los tokens?". Se le presenta el mapeo ya resuelto para
que confirme o corrija:

```
🛍️ INTEGRACIÓN SHOPIFY — {tema} ({Horizon/Dawn/custom})

Esquemas de color
  Figma "Light"   → scheme-1 del tema (existente)   ⚠️ cambia --color-foreground: #111 → #0A0A0A
  Figma "Dark"    → scheme-3 del tema (existente)   sin cambios
  Figma "Brand"   → 🆕 scheme-4 (nuevo en color_scheme_group)

Tipografía
  Heading → font_picker `type_header_font` · default {fuente}  ⚠️ no está en la librería de Shopify
                                                                  → se carga por asset (licencia: ?)
  Escala  → variables del tema (--font-h1--size …) · responsive por {pares | clamp}

Settings nuevos en settings_schema.json ({n})
  {lista} — todos con default = comportamiento actual

Snippet propio: snippets/{prefix}-design-tokens.liquid ({n} tokens)
  espaciado, radios, sombras, semánticos derivados

No se toca: {snippet de variables del tema} (autogenerado), settings_data.json

¿Lo integro así?
```

Los ⚠️ son exactamente lo que el dev tiene que mirar: cambios sobre valores que ya están en producción.
