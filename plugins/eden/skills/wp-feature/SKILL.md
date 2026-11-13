---
name: wp-feature
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:wp-feature` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable de
  crear un post type, un campo o un formulario: si no lo pidió por su nombre, no se usa. —
  Qué hace cuando SÍ se invoca: construye una funcionalidad de backend de WordPress de punta a punta —
  custom post type, taxonomía, campos (ACF o nativos), endpoint REST, hook o personalización de
  WooCommerce— en el mu-plugin del sitio y no en el tema, con nombres propuestos y consensuados,
  seguridad desde el primer intento (escape, sanitize, nonce, capability), traducciones, y el front
  conectado. Recorre la escalera reuse-first antes de escribir: casi siempre WordPress ya lo trae.
argument-hint: "[url-ticket] [| qué funcionalidad y dónde se usa]"
disable-model-invocation: true
---

## WP Feature — funcionalidad de WordPress, bien puesta

Argumento recibido: `$ARGUMENTS`

Este skill es el hermano de `create-new-section` para lo que **no es una sección**: los datos y la
lógica del sitio. Es autónomo — recolecta su contexto, propone, construye y verifica.

> **Idioma:** al dev, en español. Todo lo que quede escrito —código, slugs, claves, docs— en inglés.

**Lo que NO hace:** commitear, pushear, abrir PRs ni comentar en el tracker. Al terminar, el trabajo queda
en la rama para que `turnoff-task` lo cierre. Tampoco instala plugins sin preguntar.

**Modelos — la sesión principal planifica, los agentes ejecutan.** El inventario se delega a `eden:wp-explorer`, la
implementación a `eden:wp-implementer`, la revisión a `eden:wp-qa-reviewer`. Lo que reporta un agente es
una afirmación: se verifica.

**Reglas:** `rules/wordpress/eden-wordpress-rules.md` (obligatoria) + el sabor del proyecto.

---

### Paso 1 — Contexto, en una sola pregunta

```
Para construir esta funcionalidad necesito lo que tengas a mano:

1. URL del ticket (Asana/SMG Hub/ClickUp) → {si la hay, leo requerimientos y subtareas}
2. ¿Qué tiene que hacer?       → el comportamiento, no la solución técnica
3. ¿Quién lo administra y quién lo ve? → el cliente en el admin, un visitante, ambos
4. Cualquier cosa que aportes: datos de ejemplo, casos borde, integraciones, lo que NO debe hacer.
```

Si el dev describe **la solución** ("hazme un CPT de testimonios") en vez del **problema**, se pregunta
el problema. Muy a menudo la respuesta correcta no es un CPT.

---

### Paso 2 — Escalera reuse-first: WordPress ya trae casi todo

**Antes de registrar nada.** Se recorre en orden y se para en el primero que resuelva:

1. **¿Lo resuelve el contenido nativo?** Páginas, entradas, categorías y etiquetas cubren más de lo que
   parece. Un CPT "Noticias" que es exactamente una entrada con otra etiqueta es deuda gratis.
2. **¿Lo resuelve un campo sobre lo que ya existe?** Un `register_post_meta` o un campo ACF en la
   página, en vez de una entidad nueva.
3. **¿Lo resuelve una taxonomía** en lugar de un tipo de contenido nuevo?
4. **¿Lo resuelve un plugin establecido** que el proyecto ya tiene o que vale la pena tener (formularios,
   SEO, caché)? No se reescribe un motor de formularios.
5. **Funcionalidad propia** en el mu-plugin del sitio — cuando lo anterior no llega.

En qué escalón se paró y **por qué no bastó el anterior** va en la propuesta, como en todo el kit.

---

### Paso 3 — Proponer los nombres (y esperar el OK)

Los nombres no se inventan en silencio: quedan en la base de datos del cliente **para siempre**, y
cambiarlos después significa migrar contenido. En la propuesta, dos opciones y una recomendación:

```
📐 PROPUESTA — {funcionalidad}

Escalón reuse-first: {cuál} — {por qué no bastó el anterior}

Post type / taxonomía / campo
  Opción A  {slug} — {por qué}
  Opción B  {slug} — {por qué}
  Recomiendo A porque {razón}.

Dónde vive
  {mu-plugin del sitio}/inc/{archivo}.php     ← funcionalidad, sobrevive al cambio de tema
  {child theme}/{plantilla}                   ← solo la presentación

Configuración
  {qué podrá cambiar el cliente sin tocar código, y qué queda fijo}

Comportamiento cuando está vacío
  {qué se ve si no hay contenido / el campo está vacío}

Lo que el cliente tiene que hacer en el admin
  {pasos concretos}

⚠️ Blast radius
  {si toca algo existente: qué más lo usa, en código y en contenido}
```

Reglas de nombres que no se negocian:

- **Slug con prefijo del proyecto** (`{prefix}_testimonial`, `{cliente}_case_study`). Un `testimonial` pelado
  choca el día que se instale un plugin que registre lo mismo.
- **Máximo 20 caracteres** en el nombre de un post type — es un límite de WordPress, no una preferencia.
- Slugs en **inglés, singular, snake_case**; las etiquetas visibles van por traducción.
- Las claves de meta empiezan por `_` si **no** deben aparecer en la UI de campos personalizados.
- Un slug **no se cambia después**: cambiarlo deja huérfano todo el contenido publicado.

---

### Paso 4 — Construir

Delega a **`eden:wp-implementer`** con alcance cerrado. Lo que la implementación tiene que cumplir sí o
sí (`references/patterns.md` tiene los moldes):

- **En el mu-plugin del sitio**, no en el tema. La funcionalidad sobrevive al cambio de diseño.
- Registro en `init`, con `show_in_rest => true` si el editor, un bloque o el front lo necesitan.
- **Seguridad desde el primer intento**: escapar en la salida, sanitizar en la entrada, nonce +
  capability en toda acción, `permission_callback` real en cada ruta REST. No es una pasada posterior.
- **Todo texto visible traducido** con el text domain del proyecto.
- Campos ACF **versionados** (`acf-json/` o registro en PHP). Un campo creado solo en el admin no
  existe para el resto del equipo.
- **Fallback pensado** para cada campo vacío: nada de contenedores vacíos ni "Array" impreso en la
  página.
- Consultas con lo mínimo (`no_found_rows`, `fields => ids` cuando aplique). Sin `posts_per_page => -1`.
- `wp rewrite flush` tras registrar un CPT o taxonomía — **y anotado como paso de deploy**, porque en
  producción hay que ejecutarlo a propósito.

Si la funcionalidad tiene front, la parte visual se construye con el sabor del proyecto
(`rules/wordpress/flavors/`) o con `/eden:create-new-section` si es una sección de verdad.

---

### Paso 5 — Verificar

No se da por bueno lo que no se probó:

```bash
{wp} post-type list --fields=name,label,public,rest_base
{wp} taxonomy list
{wp} rewrite flush
{wp} post create --post_type={slug} --post_title="Test" --porcelain
composer exec phpcs -- --standard=WordPress {rutas}
```

Y en el navegador:

- **El admin**: el tipo aparece, los campos se ven y se guardan, los textos están traducidos.
- **El front**: se renderiza, y **con el contenido vacío también** — sin imagen, sin campo, sin
  entradas.
- **La REST**, si se expuso: `/wp-json/wp/v2/{rest_base}` devuelve lo esperado, y lo que escribe exige
  permisos de verdad.
- Sin PHP notices nuevos en `debug.log`.
- Los permisos: **un usuario con rol bajo no debería poder hacer lo que no le toca.** Se prueba, no se
  supone.

**Tests** (`rules/eden-testing-rules.md`): el criterio se escribe antes y debe fallar primero
(`/eden:test-code spec`). Y las APIs que se usen se verifican **vigentes** con context7 — WordPress deprecia
funciones y una deprecada pasa el linter y falla meses después.

---

### Paso 6 — Documentar

Toda funcionalidad con configuración o lógica no obvia deja su doc en `docs/`, en inglés
(`feature-doc`): qué es, qué slug y qué claves usa, qué tiene que hacer el cliente en el admin, qué pasa
cuando está vacío, y **qué pasos de deploy hacen falta** (el `rewrite flush`, la activación de un
plugin, la creación de una página).

---

### Reporte

```
🧩 WP FEATURE — {qué}

Escalón reuse-first  {cuál} — {por qué no bastó el anterior}
Nombres              {slugs y claves finales}
Dónde                {archivos}

Verificado
  ✅ {admin | front | REST | vacío | permisos | phpcs}

Para el cliente en el admin
  {pasos}

Pasos de deploy
  {rewrite flush, activaciones, lo que haya}

⚠️ Fuera de alcance / pendiente
  {qué y por qué}
```
