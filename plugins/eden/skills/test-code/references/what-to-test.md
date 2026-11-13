# Referencia — Qué se testea a nivel código

Los tests cubren **comportamiento**, no existencia de código. Un test por cada línea es mantenimiento
sin valor; un test por cada cosa que puede romperse, sí.

## Web Components / JS interactivo

Lo que hay que aseverar, por orden de lo que más rompe:

| Qué | Por qué |
|---|---|
| **Estado inicial** | Cómo se renderiza sin interacción, y con datos vacíos |
| **Respuesta a eventos** | Clic, teclado, cambio de valor — el comportamiento que el ticket describe |
| **Casos borde** | Cero ítems, uno, muchos, texto larguísimo, dato faltante, imagen rota |
| **Limpieza en `disconnectedCallback`** | Listeners y observers eliminados. **Es la fuga que nadie ve** hasta que la página se pone lenta navegando |
| **Datos desde la plantilla** | Que el JSON embebido se parsee, y qué pasa si viene malformado o vacío |
| **Accesibilidad del comportamiento** | Foco donde debe quedar, `aria-expanded` que cambia, Escape que cierra |

El de limpieza merece énfasis: es el único de la lista que **no se nota probando a mano** y que se
acumula en toda la sesión del usuario.

## Lógica pura

Entradas → salidas, con los extremos incluidos: vacío, uno, muchos, negativo, cero, malformado, nulo.

Si una función tiene una rama que ningún test recorre, o sobra la rama o falta el test.

## Plantillas (Liquid y similares)

No hay test unitario nativo. La red es:

1. **Theme Check** — sintaxis, schema malformado, tags deprecados, traducciones que faltan.
2. **Verificación de render** con tres juegos de datos: reales, vacíos y extremos. Que el marcado salga
   correcto en los tres.
3. **Los estados**: sin producto, sin imagen, sin variantes, colección vacía.

Lo que se verifica del marcado: jerarquía de encabezados sin saltos, `alt` presente, `label` asociado a
cada input, links con `href` real, y que el texto visible venga de traducciones y no esté hardcodeado.

## Integración

El flujo completo que el ticket describe, de punta a punta. Si el ticket dice "el usuario elige talla y
la talla llega al pedido", el test va **hasta el pedido** — no hasta que el `<select>` cambia de valor.

Si el perfil declara reglas de negocio (`business_rules`), esto es explícito: cada dato que debe
llegar al pedido se prueba hasta el pedido, y cada flujo con servicios externos, hasta su efecto real.

## Qué NO se testea

- **Que un archivo exista** o que una clase esté declarada.
- **La librería de terceros** — se asume que funciona; se testea *nuestro uso* de ella.
- **Estilos** — eso es `test-visual`, que mide el render real. Un test unitario que compara strings de
  CSS no prueba nada.
- **Lo que no puede fallar.** Si un aserto no tiene forma de romperse, es ruido.

## El runner

**Manda el proyecto.** Si ya tiene uno configurado, se usa ese, con sus convenciones de carpeta y
nombres.

Si no tiene nada: se **propone** (para JS de tema, algo ligero que corra sin build pesado) y **se espera
aprobación**. Montar un framework de tests cambia el `package.json`, el CI y la rutina del equipo — no
es una consecuencia silenciosa de implementar una sección.

Y si el dev prefiere no montar suite en este proyecto: se respeta, se deja constancia, y la puerta de
entrega se cubre con lo que sí hay (Theme Check, linter y verificación manual declarada). **Lo que no se
hace es marcar como testeado lo que nadie probó.**
