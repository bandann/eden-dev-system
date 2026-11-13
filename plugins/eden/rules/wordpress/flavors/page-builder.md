# Sabor: Page builder (Elementor / Divi / WPBakery / Beaver) — WordPress

El diseño lo arma el cliente o el diseñador dentro del builder. Nuestro trabajo custom es otro: widgets
propios, CSS acotado, plantillas y hooks del builder.

**La advertencia que hay que decir una vez y no repetir:** en un page builder, **el diseño vive en la
base de datos, no en el repo**. Eso cambia tres cosas de raíz — el blast radius, qué significa
"versionado", y qué se puede prometer como pixel-perfect. Todo lo demás del kit sigue igual.

## Qué es una "sección" aquí

Según lo que pida la tarea:

- Una **plantilla guardada** del builder (Elementor Template, Divi Library, Saved Template) — vive en la
  DB.
- Un **widget/módulo propio**, registrado en código, que el cliente arrastra como cualquier otro.
- Un **bloque de CSS/JS acotado** que ajusta cómo se ve algo ya armado.

## Escalera reuse-first en un builder

1. **Armarlo con los widgets que ya trae el builder, configurados.** Sin código. En un builder este
   escalón alcanza mucho más lejos que en cualquier otro sabor, y es lo que el cliente podrá seguir
   manteniendo solo.
2. **Una plantilla global / template part del builder**, para que el cambio se propague donde se usa
   en vez de repetirse a mano en 12 páginas.
3. **Los estilos globales del builder** (Global Colors, Global Fonts de Elementor; los presets de Divi).
   Ahí es donde se integran los fundamentos de diseño del proyecto — es el `theme.json` de este sabor.
4. **CSS propio acotado**, en el CSS del child theme, con selectores anclados a una clase que le
   pusimos nosotros al widget (`{prefix}-hero`), **nunca** a las clases autogeneradas
   (`.elementor-element-a3f9d2`): ese id cambia si el cliente rehace el elemento.
5. **Widget/módulo propio en código** — último recurso, cuando hace falta lógica o datos que ningún
   widget expresa. Se registra desde el mu-plugin o un plugin propio, no desde el tema.

## Reglas duras

- **Nunca se edita el plugin del builder.** Se extiende por sus hooks
  (`elementor/widgets/register`, `elementor/frontend/after_enqueue_styles`, los `et_` de Divi…).
- **Nunca se estiliza contra las clases autogeneradas.** Se le pone una clase propia al elemento desde
  el panel del builder (Advanced → CSS Classes) y se estiliza contra esa. Documentar en el ticket qué
  clase se puso y dónde, porque no está en el repo.
- **El CSS del builder gana casi siempre** porque es inline y muy específico. La respuesta correcta es
  configurar en el builder, no escalar la especificidad. Si de verdad hay que pisar algo del plugin,
  ese es el único caso donde el núcleo permite `!important`, y va comentado con el porqué.
- **Nada de "Custom CSS" pegado dentro del builder** salvo que el proyecto lo declare como su
  convención. Lo que vive solo en la DB no se revisa en un PR, no se despliega y se pierde en la
  siguiente importación.
- Los widgets propios llevan **prefijo** y su propio namespace de clases.

## Blast radius — aquí es obligatorio y es distinto

Cambiar un global style o una plantilla global **repinta páginas publicadas al instante**. Antes de
tocar cualquier cosa global:

```bash
wp db search "{clase|nombre-de-widget|id-de-plantilla}" --stats
wp post list --post_type=elementor_library --format=table    # o la CPT del builder que toque
```

Y se declara en el plan **cuántas páginas** lo usan. Si son muchas, el cambio global lo autoriza el dev.

**Antes de tocar el diseño de una página existente en el builder: backup de esa página.** Los builders
guardan revisiones, pero no siempre; y un `wp db export` antes de una sesión de cambios cuesta diez
segundos.

## Performance — el punto débil de este sabor

Los builders cargan mucho de más. Lo que sí está en nuestras manos:

- Desactivar en el builder lo que el proyecto no use (iconos, animaciones, Google Fonts remotas si las
  fuentes son propias).
- No añadir un plugin más "para optimizar" sin medir antes.
- Imágenes: los tamaños correctos, `loading="lazy"` fuera del fold. Las que sube el cliente se revisan.
- Medir con Lighthouse **antes y después** de lo que tocamos, y reportar el número real. Un builder
  lento no es excusa para empeorarlo, pero tampoco se promete lo que la plataforma no da.

## Fidelidad al Figma

Se mide igual que en cualquier otro sabor: render real en el navegador contra el nodo de Figma, con
`/eden:attention-detail` o `/eden:test-visual`. La diferencia es **dónde se aplica la corrección**: primero en el
panel del builder (que es configuración), y solo si el panel no lo puede expresar, en CSS propio
acotado.

## Qué se documenta al cerrar

Como parte del diseño no está en el repo, el PR **no cuenta la historia completa**. En el cierre se
declara siempre:

- Qué se cambió **en el builder** (página, plantilla, widget, qué clase propia se agregó).
- Qué se cambió **en código** (eso sí va en el PR).
- Si se tocó algo global, qué páginas se ven afectadas.
