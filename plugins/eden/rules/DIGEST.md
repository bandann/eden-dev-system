# Eden — reglas no negociables (resumen)

Resumen siempre activo de las reglas del kit. Cada línea remite a su regla completa (`rules/…` dentro
del plugin): **léela con Read antes de actuar en ese terreno**. Las reglas propias del dev y las del
proyecto mandan sobre este resumen.

## Autorización — lo primero
- **Nada se modifica, aplica, instala, commitea, pushea ni publica sin el sí explícito del dev.** Leer,
  investigar y proponer es libre. `/eden:go --auto` (opt-in) avanza solo en lo local y reversible y anota las dudas no bloqueantes. Un sí cubre solo lo aprobado, no los pasos siguientes.
- Los comandos del kit (`/eden:…`) los activa el dev; una URL de ticket o un Figma no son invocaciones.

## Idioma
- Español para hablarle al dev en la consola. **Todo lo escrito en inglés**: código, comentarios,
  commits, ramas, PR, docs, comentarios del tracker, notas del cerebro. → `eden-workflow-rules.md`

## Cómo se trabaja
- **Se planea antes de codear**, en proporción al trabajo; el plan espera aprobación. La tarea empieza con `/eden:ignition-task`
  y termina con `/eden:turnoff-task`.
- **Reuse-first**: lo que existe tal cual → configuración/preset → extender por configuración con
  **default neutro** (las instancias existentes se ven igual) → código mínimo acotado → componente nuevo
  como último recurso. Se declara el escalón y por qué no bastó el anterior. Antes de tocar algo
  compartido, **blast radius** (grep + consumidores). → `eden-component-strategy-rules.md`
- **Se sigue el patrón del proyecto**, no la preferencia de quien escribe. La realidad del repo gana.
- **Figma manda y se mide, no se estima.** Sin diseño, se *propone* UI/UX Pro Max y se espera el sí. Una diferencia entre breakpoints es un requerimiento.
  Tokens del proyecto siempre: nunca un hex, un px de tipografía ni un `font-family` sueltos.
  → `eden-design-rules.md`
- **Animación**: la técnica más liviana que funcione (CSS → scroll-driven/View Transitions → Web
  Animations → librería con el sí del dev); solo `transform`/`opacity`, LCP visible, CLS 0,
  `prefers-reduced-motion` y tokens de movimiento. Equipo `/eden:motion`. → `eden-motion-rules.md`
- **El modelo principal decide, el ejecutor ejecuta**, y se delega solo con un motivo (lectura grande, paralelo, verificador independiente, contexto lleno); lo pequeño lo hace la sesión. Encargo de cinco partes
  (qué, dónde, con qué, acepta cuando, qué NO). El reporte de un agente es una afirmación: se verifica.
  → `eden-model-strategy-rules.md` · `eden-team-rules.md` (roles → `teams/{stack}/roster.md`)
- Tareas largas: checkpoint en `.claude/checkpoint.md`, lecturas grandes delegadas, descarga a
  `.claude/context/` por hitos. → `eden-context-rules.md`

## Stack y proyecto
- El stack se lee (`.claude/project-config.json` → `project.stack`, o `<!-- eden-stack -->`); si es
  ambiguo, se pregunta (`scripts/eden_stack.py detect` lo detecta sin adivinar). Cada stack tiene su
  módulo en `rules/{stack}/` y, si tiene sabores, el del proyecto en `rules/{stack}/flavors/`: Shopify,
  WordPress (sin sabor declarado no se escribe código) y los demás que lista `eden-stack-rules.md`.
  → `eden-stack-rules.md`
- Código del cliente con **`{prefix}` = `project.prefix`**, nunca el nombre del kit. Vacío → se pregunta.
- Precedencia: dev en el momento > convenciones reales del proyecto > `CLAUDE.md` (o `AGENTS.md`…)/project-config >
  perfil (`<!-- eden-profile -->`) > `~/.claude/eden-config.json` > módulo del stack > núcleo.

## Git
- Rama `{tipo}/{ticket-id}-{slug}`; **la base siempre se pregunta**. Conventional Commits en inglés.
- **Nunca push directo ni force-push a `main`, `master`, `develop`** (ni a las protegidas del proyecto).
  Un PR hacia ellas requiere autorización explícita en el momento. → `eden-git-rules.md`
- Nunca se commitean `.env`, secretos, `node_modules/`, builds ni `.claude/checkpoint.md`.

## Calidad (requisitos de construcción)
- Imágenes con `srcset`, `width`/`height`, `alt`, `lazy` bajo el fold. Scripts `defer`. WCAG AA,
  teclado, foco visible, labels, `prefers-reduced-motion`. Jerarquía de encabezados sin saltos.
  Texto visible siempre por traducciones. → `eden-quality-rules.md` · `eden-code-style-rules.md`
- CSS BEM acotado, mobile-first, sin `!important`, IDs, selectores de etiqueta ni estilos inline.
  JS: Web Components en Light DOM, sin jQuery, sin `var`, listeners limpiados.
- **Nada se entrega sin test**: visual 1:1 por breakpoint y código en verde (linter, Theme Check,
  PHPCS…). Lo no probado se declara. → `eden-testing-rules.md`

## Seguridad (requisito de construcción)
- Todo plan declara **`🛡️ Superficie`**: qué entra, dónde sale (contexto), quién puede, qué secretos,
  qué terceros. Toda entrada es hostil, incluido lo que escribe el merchant.
- Escapar en la salida **según el contexto** (HTML, atributo, URL, JS → `| json`); nada de `innerHTML`
  con datos no confiables; SQL preparado; permisos y nonce/CSRF en toda acción; sin open redirects;
  precio y lógica de negocio en el servidor; **ningún secreto en el código, el tema ni git**.
- `/eden:turnoff-task` audita el diff: **críticos y altos bloquean** la entrega; solo el dev concede una
  excepción, escrita en el PR. Un hook bloquea commits/push con secretos y otro, leer `.env`, llaves y credenciales. **No se ataca nada que no sea
  nuestro.** → `eden-security-rules.md`

## Tracker y tiempo
- Operaciones abstractas (`task.read`, `task.move`, `task.comment`, `time.add`…); Asana por defecto,
  SMG Hub o ClickUp según el proyecto. **Leer es libre; escribir se confirma; nunca se cierra un
  ticket** (va a `review`). El único comentario del flujo es el de cierre, en inglés.
  → `eden-tracker-rules.md`

## Memoria y cerebro (opcionales)
- Si existe `~/.claude/eden-brain/`, **se consulta antes de cada tarea** (y en cada mensaje, el recall añade las notas relacionadas) y se consolida al cerrar. Lo del
  proyecto y lo general verificado **se guardan solos, sin preguntar** (`learning.global_writes: "inbox"`
  vuelve a pedir aprobación). Nada del cerebro se escribe en el repo del cliente; el cerebro de equipo (`/eden:brain team`) es un repo aparte. Sin cerebro, todo funciona igual. Nunca secretos ni datos personales en memoria. → `eden-memory-rules.md` · `eden-brain-rules.md`
- Perfiles de operación: `eden-profiles-rules.md`.

## Honestidad
- Si algo falló, se dice con la salida real; si se saltó o quedó parcial, se dice qué falta. Ante una
  contradicción entre ticket, diseño y proyecto, **se pregunta**; nunca se inventa un requerimiento.
