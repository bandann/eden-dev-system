# Integrar los fundamentos de diseño en WordPress

Criterio central, el mismo que en Shopify: **la plataforma ya tiene un sistema de tokens; los
fundamentos LO LLENAN, no crean otro en paralelo.** Un `:root` propio compitiendo con los presets del
tema es la forma más rápida de que el sitio quede con dos verdades.

**Dónde se llena depende del sabor** (`wordpress.flavor` en `project-config.json`):

| Sabor | El sistema de tokens es | Referencia |
|---|---|---|
| block-theme | `theme.json` del child theme | §1 |
| classic-theme | Custom properties propias del tema | §2 |
| page-builder | Los globales del builder | §3 |
| headless | Los tokens del framework del front | §4 |

---

## §1 · Block theme — `theme.json` es el `settings_schema.json` de WordPress

Es el caso ideal: WordPress genera solo las clases, las variables CSS y los controles del editor a
partir de los presets. Se rellena `settings` en el `theme.json` **del child theme**.

### Color

```json
{
  "version": 3,
  "settings": {
    "color": {
      "palette": [
        { "slug": "primary",    "name": "Primary",    "color": "#0F172A" },
        { "slug": "surface",    "name": "Surface",    "color": "#FFFFFF" },
        { "slug": "text",       "name": "Text",       "color": "#111111" }
      ],
      "custom": false,
      "defaultPalette": false
    }
  }
}
```

De cada entrada, WordPress genera solo:
`--wp--preset--color--{slug}`, `.has-{slug}-color`, `.has-{slug}-background-color` y la opción en el
editor. **Eso es lo que se usa en el CSS del tema** — nunca el hex.

Dos decisiones que hay que tomar a propósito:

- **`"defaultPalette": false`** quita la paleta de WordPress. Casi siempre es lo correcto: si se deja,
  el cliente tiene 40 colores que no son de la marca y acabarán en alguna página.
- **`"custom": false`** quita el selector de color libre. Es lo que impide que el sitio se desalinee
  solo, pero es una decisión de producto: **se propone al dev, no se impone**.

### Tipografía

```json
"typography": {
  "fluid": true,
  "fontFamilies": [
    { "slug": "heading", "name": "Heading", "fontFamily": "\"{Fuente}\", serif",
      "fontFace": [ { "src": ["file:./assets/fonts/{archivo}.woff2"], "fontWeight": "400", "fontStyle": "normal", "fontDisplay": "swap" } ] }
  ],
  "fontSizes": [
    { "slug": "body", "name": "Body", "size": "1rem" },
    { "slug": "h2",   "name": "H2",   "size": "2rem",
      "fluid": { "min": "1.75rem", "max": "2.5rem" } }
  ],
  "customFontSize": false
}
```

- **`fluid` resuelve el problema de mobile vs desktop**, que en Shopify obliga a settings pareados. Si
  el Figma especifica tamaños distintos por breakpoint, se expresan como `min`/`max` — es la forma
  nativa y no hace falta CSS extra ni un override.
- Las fuentes **se autoalojan** con `fontFace` (`file:./`). Cargarlas desde Google Fonts es un problema
  de privacidad en la UE y una petición externa que bloquea el render.
- `fontDisplay: swap` siempre.

### Espaciado y layout

```json
"spacing": {
  "spacingSizes": [ { "slug": "40", "name": "Medium", "size": "1.5rem" } ],
  "units": ["px", "rem", "%", "vw"]
},
"layout": { "contentSize": "{ancho de contenido del Figma}", "wideSize": "{ancho amplio}" }
```

**`contentSize` / `wideSize` son el ancho de página del proyecto.** No se pisa con un `max-width` en el
CSS: se configura aquí, y las secciones a sangre completa usan `alignfull`.

### Estilos por bloque

```json
"styles": {
  "blocks": {
    "core/button": { "border": { "radius": "{radio del Figma}" } }
  }
}
```

Esto es mucho mejor que un CSS que pelee con el bloque después: sale en el editor, respeta los presets y
no necesita especificidad.

### ⚠️ El aviso que hay que dar antes de escribir

**Cambiar un preset que ya está en uso repinta todas las páginas publicadas que lo aplican.** Un
`primary` que pasa de azul a negro cambia todos los botones del sitio al instante. Eso es un conflicto:
lo decide el dev, no se pisa en silencio. En la propuesta va con ⚠️ y con el número:

```bash
{wp} db search "has-primary-background-color" --stats
```

---

## §2 · Tema clásico — custom properties propias, en un solo sitio

No hay sistema nativo, así que se crea **uno y solo uno**:

- Un archivo del child theme (`assets/css/_tokens.css` o el que el proyecto ya use), encolado **antes**
  que todo lo demás.
- Prefijo propio (`--{prefix}-`) para no chocar con nada del tema padre ni de un plugin.
- Si algún fundamento debe poder cambiarlo el cliente, va al **Customizer** con `default` igual al valor
  del Figma, y se emite como custom property desde ahí — misma lógica de default neutro que en el resto
  del kit.

```css
:root {
  --{prefix}-color-primary: #0F172A;
  --{prefix}-font-heading: "{Fuente}", serif;
  --{prefix}-space-40: 1.5rem;
}
```

Y una decisión que hay que tomar y declarar: **si el proyecto es fluido o de escala fija**. Si es
fluido, los tamaños van con `clamp()` aquí; si es fijo, con media queries. Se sigue cómo está construido
el proyecto — no se le impone otro modelo.

---

## §3 · Page builder — los globales del builder son los tokens

Elementor tiene Global Colors y Global Fonts; Divi tiene sus presets. **Ahí se integran los
fundamentos**, no en un CSS paralelo: es lo que hace que el cliente, al elegir "Primary" en un widget,
use el color correcto sin saber nada.

Consecuencias que hay que decir en voz alta:

- **Los tokens de este sabor viven en la base de datos, no en el repo.** No se pueden revisar en un PR.
  Por eso `docs/design-system.md` es aquí *más* importante que en los otros sabores: es el único sitio
  donde queda escrito qué valor tiene cada token.
- Cambiar un global **repinta el sitio entero al instante**. Se mide antes y lo autoriza el dev.
- Lo que el builder no pueda expresar se cubre con custom properties propias en el child theme (§2), y
  se documenta cuál va por dónde.

---

## §4 · Headless — los tokens son del front

WordPress no participa: el diseño lo renderiza el framework. Los fundamentos se integran **en el front**
según sus convenciones (config de Tailwind, `tokens.css`, el objeto de tema del design system) — ver
`output-targets.md`.

Del lado de WP solo se documenta lo que el front necesite conocer (p. ej. qué tamaños de imagen se
registran con `add_image_size` para que el front pida el correcto).

---

## Verificación — qué se comprueba antes de dar los fundamentos por integrados

```bash
{wp} theme list --status=active --fields=name,parent
php -l {archivos-tocados}
```

Y en el navegador:

- Los presets **aparecen en el editor** con sus nombres correctos (block theme).
- Una página existente **se ve igual que antes**, salvo lo que el dev aprobó cambiar.
- Los tokens se resuelven de verdad: inspeccionar un elemento y ver `var(--wp--preset--color--primary)`
  con valor, no una variable vacía.
- **Ningún hex nuevo suelto** en el CSS que se escribió:
  ```bash
  grep -rnE "#[0-9a-fA-F]{3,8}\b" {css-tocado}
  ```

## Los cuatro artefactos

Igual que en cualquier stack (`output-targets.md`): tokens en código · `docs/design-system.md` ·
`.claude/project-config.json` · el bloque del `CLAUDE.md`, los cuatro con el marcador
`<!-- eden-fundaments: updated=… figma=… version=… -->`. En WordPress, `docs/design-system.md` declara
además **en qué sabor están los tokens y por tanto dónde vive cada valor** — sin eso, el siguiente dev
los busca en el sitio equivocado.
