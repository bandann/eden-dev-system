# Sabor: Block theme (FSE) — WordPress

Tema de bloques con `theme.json`, plantillas HTML, template parts y patterns. Es el sabor que más se
parece a Shopify Horizon: **hay un sistema de tokens y un sistema de bloques anidables, y el trabajo
consiste en llenarlos, no en crear otro paralelo**.

## Estructura

```
{child-theme}/
├── style.css              cabecera del tema (Template: {padre} si es child)
├── theme.json             EL sistema de diseño — tokens, layout, estilos por bloque
├── functions.php          solo enqueues, supports y registros de presentación
├── templates/             plantillas de página (index.html, single.html, page-x.html)
├── parts/                 template parts (header.html, footer.html)
├── patterns/              block patterns en PHP con cabecera
├── styles/                variaciones de estilo del tema (style variations)
├── blocks/                bloques propios (uno por carpeta, con su block.json)
└── assets/
```

## theme.json es el settings_schema del tema — se llena, no se duplica

Los fundamentos de diseño del proyecto se integran **aquí**. Es el equivalente exacto de lo que en
Shopify hace `config/settings_schema.json` + las custom properties del tema:

- `settings.color.palette` → cada color del Figma, con `slug`, `name` y `color`. WordPress genera
  solas las clases `.has-{slug}-color` / `.has-{slug}-background-color` y la variable
  `--wp--preset--color--{slug}`.
- `settings.typography.fontSizes` → la escala. Con `fluid` (min/max) si el proyecto es fluido; con
  `size` fijo si es fijo. **Se sigue cómo está construido el proyecto.**
- `settings.typography.fontFamilies` → las familias, con `fontFace` para autoalojarlas.
- `settings.spacing.spacingSizes` → la escala de espaciado.
- `settings.layout.contentSize` / `wideSize` → el ancho de página. **No se pisa con CSS**: se
  configura aquí y las secciones a sangre completa usan `alignfull`.
- `styles.blocks.{core/x}` → los estilos por defecto de cada bloque del core, en vez de un CSS que los
  pelee después.

**Nunca se hardcodea un hex ni un px en el CSS del tema** si hay preset para él: se usa
`var(--wp--preset--color--{slug})` o `var(--wp--preset--spacing--{n})`.

**Default neutro en `theme.json`:** cambiar un preset que ya está en uso **repinta todas las páginas
publicadas que lo aplican**. Eso es un conflicto: lo decide el dev, no se pisa en silencio.

## Escalera reuse-first en un block theme

1. **Un pattern con bloques del core, configurado desde el editor.** Sin código. Es el mejor
   resultado y en FSE alcanza mucho más lejos de lo que parece: Group + Columns + Cover + Query Loop
   con sus supports resuelven la mayoría de las secciones de una landing.
2. **Un pattern propio** en `patterns/` — sigue siendo markup de bloques del core, versionado, y el
   merchant puede insertarlo y editarlo. **Este es el escalón donde debería quedarse la mayoría del
   trabajo de secciones.**
3. **Block variation / block style** de un bloque existente (`registerBlockStyle`,
   `registerBlockVariation`) cuando solo cambia el aspecto o los defaults.
4. **Block Bindings** para conectar un bloque del core a un metadato, sin crear un bloque nuevo.
5. **Bloque propio** (`block.json` + `render_callback` dinámico, o `save` estático) — último recurso,
   cuando hay lógica o datos que ningún bloque del core puede expresar.

Cuál se eligió y **por qué no bastó el anterior** va escrito en el plan, igual que en el núcleo.

## Bloques propios

- Una carpeta por bloque, con `block.json` (`apiVersion: 3`) como fuente de verdad: nombre, atributos,
  supports, y las rutas de `editorScript`, `script`, `style` y `viewScript`.
- Registro con `register_block_type( __DIR__ . '/blocks/{x}' )` — nunca declarando los assets a mano.
- **Prefijo propio en el nombre**: `{prefix}/{bloque}` o `{cliente}/{bloque}`. Un `core/`-lookalike es un
  problema el día que el core cree ese bloque.
- **Bloque dinámico (`render_callback`) por defecto.** El estático guarda el HTML dentro del contenido:
  cuando cambie el markup, todas las entradas publicadas quedan en "block validation error". Si aun así
  se elige estático, se escribe una `deprecated` en cuanto cambie el `save`.
- `supports` antes que atributos propios: color, spacing, typography y align los da WordPress gratis y
  ya salen conectados a los presets del `theme.json`.
- Los estilos del bloque van en su `style.css` (front + editor) y `editor.css` (solo editor), no en el
  CSS global del tema.

## Interactividad

- Interactividad ligera del front: **Interactivity API** (`@wordpress/interactivity`, directivas
  `data-wp-*`) o un Web Component en Light DOM. Sin jQuery.
- El editor es React (`@wordpress/element`); el front **no tiene por qué serlo**. No se mete React en
  el front por costumbre.

## Fidelidad al Figma en FSE

El punto que más cuesta: **el editor debe verse igual que el front**. Un pattern que se ve bien en la
página pero descuadrado en el editor está a medio entregar, porque el cliente edita ahí.

- El ancho: `contentSize`/`wideSize` del `theme.json`, no un `max-width` propio.
- Los huecos entre bloques: `blockGap` y los presets de spacing, no `margin` suelto.
- Los tamaños distintos entre mobile y desktop: **`fluid` en `fontSizes` o `clamp()`**, siguiendo lo que
  el proyecto ya use. Si el Figma difiere entre breakpoints y el preset no lo puede expresar, es un
  hueco de configuración — se propone al dev, no se resuelve con un override CSS.

## Validación propia de este sabor

```bash
npx wp-scripts lint-js blocks/
npx wp-scripts build
wp theme list --status=active          # que el child esté activo y su padre exista
```

Y una comprobación que ahorra horas: **abrir una entrada ya publicada** que use lo que se tocó y
confirmar que no aparece "This block contains unexpected or invalid content".
