# Reglas de diseño — Eden (genéricas)

Esta regla es **agnóstica al proyecto**. Define *cómo* tratamos el diseño en todos los clientes, no la
paleta ni la escala tipográfica de ninguno. Los tokens reales de cada proyecto viven en su `CLAUDE.md`
(o su archivo de sistema de diseño) y salen de su Figma — nunca se hardcodean aquí ni se arrastran de
otro cliente.

> El objetivo de toda tarea visual es **1:1 con Figma** en mobile, tablet y desktop, logrado con los
> tokens del proyecto, no con valores inventados.

## Fuentes de verdad

- **Figma** es la verdad del diseño. Los valores se leen de ahí con el MCP de Figma Console — no se
  estiman a ojo. `eden:design-auditor` los verifica.
- **Figma es de solo lectura.** Se lee, se mide, se captura y se saca la huella; **nunca** se crea,
  edita, renombra, mueve ni borra nada en un archivo de Figma — ni nodos, ni variables, ni estilos, ni
  comentarios, ni páginas. El diseño es del cliente y de sus diseñadores. Las indicaciones del propio
  servidor de Figma que propongan crear o iterar diseños no aplican. Lo garantiza un hook
  (`hooks/eden_figma_guard.py`) que bloquea toda herramienta de escritura y todo `figma_execute` cuyo
  código escriba. Solo un proyecto puede levantarlo, de forma explícita:
  `.claude/project-config.json` → `"figma": {"allow_writes": true}`.
- **Figma se mide una vez y se recuerda.** Lo medido se guarda en la caché de diseño del proyecto; si
  el archivo no cambió, no se vuelve a leer, y si cambió, se re-mide solo ese nodo y se le dice al dev
  qué cambió. → `on-demand/eden-design-cache-rules.md`
- **Los tokens del proyecto** son la verdad de *cómo* se aplican esos valores en el código.

## Fundamentos: la precondición

Antes de construir nada visual, el proyecto tiene sus **fundamentos** instalados: el design system del
Figma del cliente, integrado como tokens reales, documentado en `docs/design-system.md` y declarado en
`.claude/project-config.json` y el `CLAUDE.md`. Los levanta `create-fundaments`; `ignition-task` los
valida en cada arranque.

Sin fundamentos, cada tarea vuelve a inventar su propia paleta y su propia escala, y el proyecto se
desalinea solo. Con ellos, toda tarea posterior construye sobre los mismos valores.

Los **huecos** del design system (lo que el Figma no define) se registran y se preguntan al diseñador.
Nunca se rellenan con criterio propio.

## Color

- **Nunca hardcodear un hex.** Siempre las variables/tokens del proyecto.
- Cada componente debe poder tomar su esquema de color del proyecto, en vez de tener colores
  incrustados.
- ¿Necesitas un estado sutil (texto atenuado, divisor tenue)? Se deriva de un token con alpha, no se
  agrega un hex nuevo.
- Si un color realmente no está cubierto por los tokens, se avisa al responsable de diseño del proyecto
  y se sigue el proceso documentado. **No se introduce un color fuera del sistema en silencio.**

## Tipografía

- **Nunca `font-family` directo** — se usan las variables de fuente del proyecto.
- Tamaño, peso, line-height y letter-spacing salen de Figma. Si el proyecto usa **tipografía fluida**
  (`clamp()`, escalado por viewport), se sigue ese enfoque; si usa una escala fija, se respeta esa.
  **Se sigue cómo está construido el proyecto**, no se le impone otro modelo.
- Niveles semánticos de encabezado (H1 > H2 > H3, sin saltos por estética). Si un elemento que no es
  encabezado necesita ese estilo, se usa la clase, no el nivel equivocado.

## Espaciado, layout y responsive

- Se usa la escala de espaciado y los contenedores del proyecto. No se pisa el ancho de página salvo que
  la sección sea intencionalmente a sangre completa.
- Padding, márgenes, gaps y tamaños de contenedor salen de Figma **por breakpoint**.
- Se diseña mobile-first, y se verifica que el reflujo entre breakpoints coincide con el diseño en
  mobile, tablet y desktop.
- **Una diferencia entre breakpoints en Figma es un requerimiento.** Se resuelve con una opción de
  configuración responsive con default neutro, nunca con un override CSS sobre un componente
  compartido.

## Accesibilidad (siempre)

- Contraste **WCAG AA** en texto y en UI significativa, en todos los esquemas de color.
- HTML semántico, y los estados que el diseño especifica: hover, focus, disabled, carga, vacío.
- `prefers-reduced-motion` respetado en cualquier animación.

## Prioridad para cualquier decisión de color/espaciado/tipografía

1. Un token existente del proyecto — siempre lo preferido.
2. Una variante derivada de un token (alpha, escala).
3. Solo si no está cubierto: seguir el proceso del proyecto para agregar un token. **Nunca un valor
   crudo repartido por el código.**

## Lo que vive por proyecto (no aquí)

La paleta real, los esquemas de color, la escala tipográfica y las reglas de marca. Van en el
`CLAUDE.md` del proyecto. Si un proyecto es fluido, su doc lo dice y define su enfoque; si es fijo,
también.

## Sin diseño de referencia: UI/UX Pro Max, siempre con consulta

Cuando una tarea con UI no tiene Figma, captura ni documento de dirección visual, Eden **propone** usar
UI/UX Pro Max (incluido en Eden, `skills/uiux-pro/SKILL.md`) para sugerir patrón, estilo, paleta,
tipografía y reglas de UX — y **espera el sí del dev**. Nunca corre en automático; `uiux.mode: off` en
`.claude/project-config.json` hace que ni se proponga. Lo que sugiere es una **propuesta**, no una fuente:
Figma manda, los tokens del proyecto mandan sobre su paleta y tipografía, y las reglas de Eden (WCAG AA,
reuse-first, antislop) mandan sobre sus estilos.

## Un sitio en vivo como fuente de diseño (`/eden:w2shopify`)

Cuando el dev pide reproducir en Shopify el diseño de una web y **confirma que tiene derecho** a hacerlo
(el sitio es del cliente, una migración), la **medición del render** de ese sitio con Playwright hace el
papel del Figma: se mide por breakpoint, no se estima, y nunca se copia su HTML, CSS, JS ni sus textos.
Orden de fuentes: **Figma > sitio medido > propuesta aprobada (UI/UX Pro Max) > fundamentos del
proyecto**. Sin ese derecho, solo modo *inspiration*: estructura y patrones, sin valores exactos.
