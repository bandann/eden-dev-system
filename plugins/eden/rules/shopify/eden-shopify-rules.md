# Módulo Shopify — Eden

Se monta **encima** de las reglas núcleo (`eden-workflow-rules`, `eden-component-strategy-rules`,
`eden-code-style-rules`, `eden-design-rules`, `eden-quality-rules`). Aquí solo va lo que es propio de Shopify.

## Liquid

- **Siempre `{% render 'snippet' %}`, nunca `{% include %}`.** `include` está deprecado y filtra el
  scope global.
- Nunca lógica pesada en plantillas: se mueve a snippets.
- Nunca texto visible hardcodeado: `{{ 'general.title' | t }}`, con la clave en `locales/`.
- Contenido de usuario siempre escapado: `{{ variable | escape }}`.
- Minimiza los loops; pagina cuando se pueda.
- Evita `{{ 'file' | asset_url }}` dentro de loops — cachea en una variable.

## Sigue los patrones del tema

- Si el tema usa **theme blocks** (Horizon y similares), prefiere bloques para lo nuevo.
- Si el tema **no** usa bloques, no los introduzcas: sigue su patrón.
- Los estilos van donde el tema los pone: `{% stylesheet %}` dentro de la sección/bloque, o
  `assets/section-*.css`. **La convención del tema, no la preferencia de quien escribe.**
- Las variables globales del tema (esquemas de color, tipografía, espaciado) son las que se usan; las
  variables propias del proyecto van en el snippet que el proyecto destine a eso.

## Fundamentos de diseño en un tema Shopify

El tema **ya tiene** un sistema de tokens: `config/settings_schema.json` define los ajustes y el tema los
emite como custom properties. Los fundamentos del proyecto **llenan ese sistema**, no crean otro.

- Por cada fundamento: **¿lo cambia el merchant?** Sí → setting del tema, con **default igual al valor
  actual**. No → snippet propio del proyecto (`snippets/{prefix}-design-tokens.liquid`, prefijo `--{prefix}-`,
  renderizado una vez en `theme.liquid` **después** del snippet de variables del tema).
- Los esquemas de color del Figma se mapean **uno a uno** a los `color_scheme` del tema. Las secciones
  consumen las variables del esquema — **nunca un hex ni un token paralelo que haga lo mismo**.
- El snippet de variables del tema suele ser **autogenerado desde los settings**: no se edita a mano.
- Cambiar el valor de un esquema existente **repinta todas las secciones que lo usan**. Es un conflicto:
  lo decide el dev, no se pisa.
- `config/settings_data.json` es de la tienda: tocarlo es visible en producción. Se declara y se
  confirma.

Los levanta `create-fundaments` (ver su referencia `shopify-integration.md`).

## Schema

- Toda sección expone un setting de **esquema de color** y aplica su clase, para que el merchant controle
  el color y nosotros no incrustemos ninguno.
- Todo setting nuevo lleva **default que reproduce el comportamiento actual** — las instancias que ya
  existen se renderizan idénticas. Después se cambia el valor solo en la instancia que la tarea pide,
  desde el JSON de la plantilla o el editor.
- Antes de tocar una sección/snippet/bloque compartido, mide el blast radius:
  ```bash
  grep -rn "{nombre}" --include="*.liquid" --include="*.js" --include="*.json" .
  ```
  Revisa también los JSON de plantillas y los presets. Lo que encuentres va en el plan.
- Duplicar una sección implica: nombre propio, `type` de schema propio, namespace de clases propio y
  assets propios. El original y sus consumidores quedan intactos.

## Tipografía responsive en bloques de texto

Los bloques de texto se reutilizan en todo el tema y Figma suele especificar tamaños distintos por
breakpoint. Si el bloque solo expone un control de tamaño, mobile no puede quedar 1:1. Eso es un hueco
de settings: evalúa agregar la variante móvil (`heading_size_mobile` junto a `heading_size`, o el patrón
responsive que el tema ya use), con default neutro, y **propónselo al dev antes de hacerlo**. No lo
resuelvas con un override CSS sobre un bloque compartido.

## JavaScript

- Web Components en **Light DOM**. Shadow DOM rompe el render de Liquid y los estilos BEM globales.
- Datos de Liquid al componente por `<script type="application/json">` dentro del elemento.
- Un archivo por componente en `assets/`, con el nombre del componente.
- Section Rendering API para contenido dinámico, en vez de recargar la página.

## Metafields y metaobjects

Cuando una tarea los necesite, en el plan:

- 2 opciones de nombre con una recomendación y su motivo.
- `namespace`, `key` y tipo de cada uno.
- Qué debe crear el merchant en el Admin y qué pasa cuando el campo está vacío.
- Convenciones vigentes de Shopify — verificadas en la documentación actual, no de memoria (los
  namespaces reservados y las reglas de nombres cambian).

## Seguridad

Aplica `rules/eden-security-rules.md` (principios, checklist y severidad). Aquí solo lo propio de
Shopify. **El código del tema es público**: cualquiera puede leer `assets/`, `sections/` y el HTML
renderizado.

### Escapar según el contexto de salida

| Contexto | Filtro | Ejemplo |
|---|---|---|
| Texto HTML y atributos | `escape` | `<a title="{{ block.settings.title \| escape }}">` |
| Parámetro de URL | `url_param_escape` / `url_encode` | `?q={{ term \| url_encode }}` |
| Valor dentro de `<script>` | `json` | `const label = {{ block.settings.label \| json }};` |
| Texto del merchant que no debe llevar HTML | `strip_html` + `escape` | `{{ text \| strip_html \| escape }}` |

- **`{{ x }}` dentro de `<script>` o de un atributo `on*` sin `| json` es severidad Alta.** Nunca se
  interpola un setting o metafield dentro de una cadena JS entre comillas.
- Ajustes `richtext`/`inline_richtext` y metafields `rich_text`: se imprimen con el helper del tema
  (`metafield_tag` o la salida que el tema ya usa), nunca se copian a una cadena JS ni a un atributo.
- **Línea de propiedades, atributos del carrito y nota del cliente son datos del visitante**: se
  escapan al pintarlos (cart drawer, mini-cart, plantillas de confirmación). Sin `escape`, es XSS
  almacenado: Alta.

### Secretos y tokens

- En el tema **nunca** va un token de Admin API, contraseña de app privada, secreto de app ni clave de
  un servicio de terceros: **Crítica**, y se rota.
- El token público de Storefront API está pensado para ser público, pero con los **scopes mínimos**
  (solo lectura de lo que se consulta). Un scope de más es Media; cualquier otro token, Crítica.
- Un secreto en `settings_data.json` o en un setting del tema también es público.

### JavaScript

- Sin `innerHTML` / `insertAdjacentHTML` con datos de respuestas de la Section Rendering API, parámetros
  de URL, atributos del carrito o propiedades de línea, salvo saneados. Se prefiere `textContent` y las
  APIs del DOM.
- `DOMParser` sobre una respuesta de la Section Rendering API es válido **cuando el HTML viene de
  nuestra propia sección** y se inserta con los nodos ya parseados.
  ```js
  // Mal: dato del visitante interpretado como HTML
  el.innerHTML = item.properties['Engraving'];
  // Bien
  el.textContent = item.properties['Engraving'];
  ```
- **Open redirects:** `return_to`, `checkout_url` y cualquier parámetro de redirección propio solo
  aceptan **rutas relativas** (empiezan por un único `/`, no por `//` ni por un esquema). Alta.
- Sin PII (email, dirección, teléfono) en atributos `data-*`, globales JS ni eventos de analytics más
  allá de lo que la función necesita.

### Formularios

- Los formularios de cliente y contacto usan las etiquetas nativas (`{% form 'contact' %}`,
  `{% form 'customer_login' %}`…): incluyen CSRF y el `authenticity_token`. **Nunca** un `<form>` o
  `fetch` POST artesanal a `/contact` o `/account`.
- El anti-spam nativo (hCaptcha/reCAPTCHA de Shopify) **no se desactiva ni se oculta**. Un formulario
  que envía correo sin él es Media.

### Terceros

- Scripts de terceros por **app embed** o `{{ 'x.js' | asset_url | script_tag }}` con `defer`; un CDN
  externo solo con versión exacta, `integrity` y `crossorigin` (sin SRI: Media).
- **Nunca** se carga un script desde una URL que el merchant puede cambiar en un setting sin
  validación (allowlist de dominios): equivale a darle ejecución de código a quien edite el tema.
- `content_for_header` no se quita ni se altera. En checkout no se intenta inyectar scripts: se usa
  Checkout Extensibility.

### Apps, app proxy y webhooks

- App proxy: la firma (`signature`) se **verifica en el servidor** con HMAC. El parámetro `shop` no se
  confía sin esa verificación.
- Webhooks: se verifica `X-Shopify-Hmac-Sha256` sobre el **cuerpo crudo** con comparación de tiempo
  constante (`crypto.timingSafeEqual` o equivalente). Sin verificación: Crítica.

### Herramientas y severidad

- **Theme Check es el piso**, no la garantía. Además: `gitleaks` sobre el tema y `semgrep` sobre
  `assets/*.js` (comandos en el núcleo).
- Mapa a la tabla del núcleo:

| Severidad | Ejemplos en Shopify |
|---|---|
| **Crítica** | Token de Admin API en el tema; webhook sin HMAC; propiedad de línea pintada sin escapar en el cart drawer (XSS almacenado) |
| **Alta** | `{{ x }}` en `<script>` sin `\| json`; `return_to` abierto; `innerHTML` con datos de URL |
| **Media** | CDN sin `integrity`; `innerHTML` con setting del merchant; formulario sin anti-spam; scope de Storefront de más |
| **Baja** | `target="_blank"` sin `rel` en enlace propio; `console.log` sin datos sensibles |

## Validación

Antes de cerrar cualquier tarea, Theme Check sobre lo que se tocó. Errores en cero; los warnings se le
explican al dev en español.

## Preview y cierre

El link de preview del comentario de cierre apunta a **la página exacta del cambio**:
`/pages/about?preview_theme_id={id}`, nunca la home. Si se tocaron varias páginas, un link por página.

## Documentación de Shopify — verificar por año

Shopify cambia etiquetas de Liquid, opciones de schema y APIs con frecuencia. Ante duda o error,
consulta la documentación **vigente** y contrástala con cómo lo hace este tema:

- Tema Horizon: https://github.com/Shopify/horizon
- Arquitectura de secciones: https://shopify.dev/docs/storefronts/themes/architecture/sections
- Schema de secciones: https://shopify.dev/docs/storefronts/themes/architecture/sections/section-schema
- Theme blocks: https://shopify.dev/docs/storefronts/themes/architecture/blocks
- Referencia de Liquid: https://shopify.dev/docs/api/liquid
- Theme Check: https://shopify.dev/docs/storefronts/themes/tools/theme-check
- Admin GraphQL (metafields/metaobjects): https://shopify.dev/docs/api/admin-graphql
- Changelog: https://shopify.dev/changelog
