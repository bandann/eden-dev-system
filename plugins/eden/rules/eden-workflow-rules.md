# Reglas de flujo — Eden (no negociables)

Cómo trabaja el equipo, en cualquier proyecto y con cualquier stack. `ignition-task` las asume;
`turnoff-task` las verifica antes de que algo salga.

## Idioma

La regla es simple: **español solo para hablarle al dev. Todo lo demás, en inglés.**

- **Español — únicamente la conversación con el dev en la consola**: narración, planes que se le
  presentan, preguntas, reportes de QA, hallazgos y explicación de errores. El equipo es
  hispanohablante y tiene que entender qué está pasando sin traducir.
- **Inglés — absolutamente todo lo demás**, sin excepción:
  - Código, nombres de variables, comentarios de código.
  - Mensajes de commit, nombres de rama, título y cuerpo del PR.
  - Documentación en `docs/` (incluidos `design-system.md` y `sitemap.md`).
  - **El comentario de cierre en el tracker** (`task.comment`, ver `eden-tracker-rules.md`) — el único que
    el flujo publica. Lo lee el PM y el resto del equipo, y el estándar del proyecto es inglés.
  - Nombres de tokens, de settings, de archivos y de secciones.
- Las plantillas de este kit (🚀 PLAN DE IGNICIÓN, 📋 REPORTE DE CIERRE, etc.) definen **estructura, no
  idioma**: lo que se le muestra al dev se renderiza en español; lo que se publica en el tracker o en el
  PR, en inglés. Emojis, campos, rutas y valores técnicos se conservan igual en ambos casos.
- Si una herramienta imprime en inglés (linters, git, npm), se le explica al dev en español qué
  significa cuando importa. No se deja un muro sin traducir.

> Dicho corto: **si lo lee el dev en la consola, va en español; si queda escrito en algún lado, va en
> inglés.**

## Tracker de tareas y tiempo

El kit no depende de un gestor concreto: los skills piden **operaciones** (`task.read`, `task.move`,
`task.comment`, `time.add`…) y el tracker del proyecto —Asana por defecto, SMG Hub o ClickUp— dice qué
herramienta las cumple. Leer es libre; escribir se confirma; nunca se cierra un ticket. Qué hace cada
operación, cómo se resuelve el tracker y las puertas, en `eden-tracker-rules.md`. La empresa que opera
el proyecto es `company.name` (project-config, perfil o `eden-config.json`); el kit es neutro.

## Activación del kit

**El flujo Eden lo activa el dev, nunca Claude por su cuenta.** Eden es un plugin y sus comandos se
invocan como `/eden:<nombre>`. Todos —`go` (el enrutador), `shopify` (líder del equipo Shopify),
`shopify-setup`, `ignition-task`, `create-fundaments`, `create-sitemap`, `create-new-section`,
`section-mod`, `figma-expert`, `attention-detail`, `qa-pixel-perfect`, `download-figma-img`,
`test-visual`, `test-code`, `pastel-sync`, `mydaily`, `estimate-time`, `time-report`, `launch-check`,
`security-check`, `antislop`, `brain`, `memory`, `context`, `setup`, los de WordPress (`wp-setup`, `wp-local`,
`wp-import`, `wp-feature`), los de React (`react`, `react-setup`, `react-component`, `next-route`,
`react-data`), los de PHP (`php`, `php-setup`, `laravel-feature`, `laravel-api`), los de
Node (`node`, `node-setup`, `node-api`, `node-data`), los móviles (`mobile`, `mobile-setup`,
`mobile-screen`, `mobile-native`, `mobile-release`), los de apps de Shopify (`shopify-app`,
`shopify-app-setup`, `shopify-app-admin`, `shopify-app-extension`, `shopify-app-webhook`,
`shopify-app-deploy`) y `turnoff-task`— se ejecutan solo cuando el dev los escribe o los pide por
su nombre (llevan `disable-model-invocation: true`, salvo `mydaily`, que también lanza su rutina
programada). Una URL de ticket pegada (Asana, SMG Hub o ClickUp), una mención a Figma, un "ya terminé" o un pedido de commit **no**
son invocaciones. Si parece que uno aplicaría, se pregunta; no se ejecuta.

Fuera del flujo invocado, se trabaja de forma normal. Las reglas de esta carpeta siguen aplicando
cuando el proyecto las declara en su `CLAUDE.md`.

## Ciclo de vida de una tarea

Cuando **el dev decide** trabajar con el flujo del kit:

- **La tarea empieza con `ignition-task` y termina con `turnoff-task`.** Incluso un arreglo de una
  línea. Incluso sin ticket formal.
- **Modo autónomo (`/eden:go --auto`), opt-in por tarea.** Invocarlo autoriza lo **local y reversible dentro de la rama de trabajo** (leer, planear, escribir código, testear, medir, encadenar skills) sin esperar el sí de cada paso; las dudas no bloqueantes se suponen y se anotan en el tablero de preguntas. **Todo lo que sale de la máquina o no se puede deshacer** (commit, push, PR, tracker, borrar, dependencias, tienda, excepciones de seguridad) sigue esperando el sí explícito. Detalle en `skills/go/SKILL.md`.
- **Se planea antes de codear.** `ignition-task` produce un plan y espera la aprobación del dev. Sin
  aprobación no se escribe código. **El plan es proporcional al trabajo**: para un cambio pequeño y claro
  basta una línea con qué se toca y cómo se prueba; el plan con unidades, equipo y `🛡️ Superficie`
  completa es para el trabajo que lo necesita. Lo que no cambia con el tamaño es la aprobación.
- La tarea se mueve a "in progress" cuando el trabajo realmente empieza.
- Se registra el tiempo: hora de inicio en la ignición, duración reportada y confirmada en el cierre.
  Fuera de ese camino, lo carga `time-report` — que **siempre pregunta antes de escribir**, porque el
  tiempo registrado es visible para el PM, entra en la facturación y corrige mal.

### El reparto entre los dos comandos — no se cruza

| | `ignition-task` | `turnoff-task` |
|---|---|---|
| **Hace** | Entiende la tarea, mide el diseño, prepara la base de desarrollo (rama, artefactos) e **implementa** | Verifica, audita, y tras confirmación **commitea, pushea y abre el PR** |
| **Tracker** | Solo **lee**; mueve el status y arranca el cronómetro | **Escribe**: el único comentario de la tarea |
| **Reportes** | Al dev en consola, en español | El **reporte formal** de cierre |

- **`ignition-task` no comenta en el tracker, no commitea, no pushea y no abre PRs.** Al terminar de
  implementar, el trabajo queda en la rama sin commitear.
- **El único comentario que el flujo publica en una tarea es el de cierre**, y **describe qué se hizo**:
  descripción, lo que quedó fuera, PR y preview. El detalle técnico (QA, pasos de prueba, capturas) va
  en el PR, no en el ticket.

## Git

- **La rama base siempre se pregunta.** Nunca se asume `main` ni `develop`.
- **Nunca push directo a una rama protegida.** `main`, `master` y `develop` están siempre protegidas; un
  proyecto puede proteger más en su `CLAUDE.md`. Todo cambio a ellas entra por PR revisado.
- **Un PR contra `main` o `develop` requiere autorización explícita del dev en el momento.** La
  autorización para pushear la rama de trabajo **no** incluye la de abrir ese PR.
- Nunca force-push a ramas compartidas.
- Una rama por tarea; no se mezclan trabajos distintos.
- Nunca se commitean `.env`, secretos, `node_modules/` ni archivos generados.

Detalle en `eden-git-rules.md`.

## Cómo se construye

- **Ningún proyecto trabaja sin fundamentos de diseño.** Los tokens del proyecto (color, tipografía,
  espaciado, breakpoints, radios, sombras) salen del Figma del cliente y están integrados al proyecto
  antes de construir sobre ellos. `ignition-task` lo valida en cada arranque; `create-fundaments` los
  levanta. Un proyecto sin fundamentos obliga a estimar en cada tarea.
- **El proyecto tiene un mapa, y las tareas se ubican en él.** `docs/sitemap.md` dice qué páginas y
  secciones lo componen, de qué nodo de Figma sale cada una (**NODE-SECTION**) y cuáles están
  construidas. Lo levanta `create-sitemap`. Cuando existe, el plan de cada tarea cita el NODE-SECTION
  que toca y su blast radius real, y el cierre actualiza su estado.
- **Reuse-first.** Se resuelve con lo que ya existe antes de escribir código nuevo. Detalle en
  `eden-component-strategy-rules.md`.
- **Los datos de diseño se miden, no se estiman.** Las medidas salen de Figma por el MCP; los valores
  de tokens, del proyecto. Un número inventado hace que "pixel-perfect" no signifique nada.
- **Si Figma difiere entre breakpoints, Figma manda.** Una diferencia entre mobile y desktop es un
  requerimiento, no un error del diseñador.
- **Cualquier opción nueva tiene default neutro**: las instancias existentes se ven exactamente igual
  que antes del cambio.
- Se sigue el patrón del proyecto, no las preferencias de quien escribe.
- **La sesión principal planifica, los agentes ejecutan** (niveles `strong` / `fast`). La sesión principal decide, verifica y habla con el dev; los
  agentes `eden-*` traen datos y producen cambios. Así el contexto de la sesión guarda el requerimiento y
  el plan, no volcados de archivos. Detalle en `eden-model-strategy-rules.md`.
- **La seguridad es requisito de construcción**, no una pasada final: el plan declara su superficie
  (`🛡️ Superficie`) y se escribe seguro desde el primer intento. Detalle en `eden-security-rules.md`.

## Trabajo de una sola sección

No toda tarea necesita el ciclo completo. Para una sección puntual:

- **`create-new-section`** construye una que no existe. Antes de escribir código recorre la escalera
  reuse-first: que el comando se llame "create" no significa que haya que crear.
- **`section-mod`** modifica una que ya existe. Mide el **blast radius** antes de tocar nada, y toda
  opción nueva lleva **default neutro** para que las instancias existentes se vean igual que antes.
- **`figma-expert`** traduce un diseño de Figma a código con el protocolo pixel-perfect completo:
  extrae y congela el Design Spec antes de escribir nada, implementa con los tokens del proyecto, y
  **valida el render con Playwright** en un loop medir→corregir→medir. Nada se estima.
- **`attention-detail`** verifica el resultado 1:1 contra Figma, midiendo el render real en el navegador.
- **`qa-pixel-perfect`** hace lo mismo sobre la **página completa** y, a diferencia del resto,
  **corrige**: aplica lo seguro, pregunta ante cualquier cosa compartida y declara lo que no se puede
  igualar. No hay punto medio — o queda 1:1, o queda escrito qué falta.
- **`download-figma-img`** baja los assets del diseño (fotos, ilustraciones, logos, iconos) nombrados
  por sección y con manifiesto, para no ir sacándolos a mano uno por uno.

Ninguno commitea ni pushea: el trabajo queda en la rama y lo cierra `turnoff-task`.

## Plataformas — el núcleo es agnóstico, el módulo es del stack

El kit no es un kit de Shopify: es un kit de **cómo trabajamos**, y encima se monta el módulo de la
plataforma. Hoy hay dos, `rules/shopify/` y `rules/wordpress/`. La escalera reuse-first, el default
neutro, "Figma manda", el blast radius y la puerta de calidad valen igual en Liquid que en PHP; lo que
cambia es cómo se expresan.

- **El stack se lee, no se supone**: `project.stack` en `.claude/project-config.json`, o el marcador
  `<!-- eden-stack: -->` del `CLAUDE.md`. Si no está y la detección es ambigua, **se pregunta**.
- **Si el stack no tiene módulo, el trabajo no se bloquea**: se aplica el núcleo y las convenciones del
  repo, y se declara en una línea.
- **La verdad del proyecto gana sobre el módulo.** Un módulo describe la buena práctica de la
  plataforma; el proyecto describe cómo está construido de verdad.
- Detalle y precedencia completa en `eden-stack-rules.md`.

## Trabajo en WordPress

WordPress **no es una plataforma, son cuatro formas de construir** (block theme/FSE, tema clásico, page
builder, headless), y no se mezclan. Por eso:

- **`wp-setup` es el primer comando de todo proyecto WordPress.** Decide el sabor y el entorno local, y
  lo escribe en `project-config.json` y en el `CLAUDE.md`. **Sin sabor declarado no se escribe código**:
  se pregunta. Construir un bloque en un proyecto de tema clásico es trabajo tirado.
- **`wp-local`** opera el entorno del día a día y diagnostica **leyendo el log antes de tocar**.
- **`wp-import`** mueve sitios: producción→local, contenido/WXR, migración desde otra plataforma, y el
  camino de vuelta a staging. Backup antes de escribir, `--dry-run` antes de ejecutar.
- **`wp-feature`** construye funcionalidad (CPTs, taxonomías, campos, endpoints, WooCommerce).
- Las secciones van por `create-new-section` / `section-mod`, ruteados al sabor del proyecto.

Tres cosas de WordPress que el resto del kit da por supuestas y aquí hay que decir explícitamente:

1. **El blast radius incluye la base de datos.** Parte del sitio no está en el repo. Renombrar un
   bloque, un shortcode o una clase que ya está en contenido publicado **rompe páginas que nadie va a
   revisar**. Se mide con `wp db search`, siempre, además del `grep`.
2. **La funcionalidad va al mu-plugin del sitio, no al tema.** Si mañana cambia el diseño y se cambia el
   tema, el cliente pierde sus datos. La presentación sí va al child theme.
3. **La seguridad es parte de construir, no una pasada posterior**: escapar en la salida, sanitizar en
   la entrada, **nonce Y capability** en toda acción, `permission_callback` real en cada ruta REST. Es
   donde WP se rompe de verdad, y `eden:wp-qa-reviewer` lo trata como crítico.

Y dos que nunca: no se edita el core, un plugin de terceros ni el tema padre; y **no se instala un
plugin sin preguntarle al dev**. Detalle en `rules/wordpress/eden-wordpress-rules.md` y en el sabor.

## Contexto en tareas largas

Una tarea larga no debe obligar a comprimir el contexto ni a abrir sesión nueva. Dos disciplinas lo
evitan: **toda lectura grande se delega** a un agente (la sesión recibe conclusiones, nunca volcados) y
**lo trabajado se descarga a `.claude/context/` en los hitos** — al cerrar cada unidad, tras extraer
Figma, tras cada auditoría — dejando en contexto solo el puntero.

Nunca se sueltan el requerimiento, el plan, las decisiones ni lo pendiente. Y **nada se suelta sin
haberlo escrito antes**. Detalle en `eden-context-rules.md`.

## Memoria

El kit recuerda entre sesiones y entre proyectos, en **cuatro capas**: trabajo (`checkpoint.md`),
episódica (qué pasó), semántica (qué es verdad) y procedural (cómo se hace). Lo del proyecto se guarda
solo; **lo que aplicaría a todos los clientes se propone y espera la aprobación del dev** — con 40+
tiendas, un caso particular promovido a regla general se propaga a todas.

Se consulta **al arrancar** una tarea y se consolida **al cerrarla**. No se memoriza lo que ya está en
el código, en `docs/` o en git: eso se cita, no se duplica. Detalle en `eden-memory-rules.md`.

## Perfiles de operación

El núcleo es agnóstico; las verdades concretas de una operación (estados reales del tracker, ramas,
roles, umbrales de QA, reglas de negocio) viven en un **perfil** que el proyecto activa. El kit lo
consulta antes de preguntar o de asumir un default.

**Precedencia:** el dev en el momento > el proyecto > el perfil > la config global del dev
(`~/.claude/eden-config.json`) > el default del núcleo. **Si algo no lo
cubre el perfil, se aplica el default y se declara** — nunca se bloquea el trabajo. Si el perfil
contradice la realidad del repo, gana la realidad. Detalle en `eden-profiles-rules.md`.

## Puerta de calidad (la verifica `turnoff-task`)

- **Ninguna tarea se entrega sin test.** Visual en verde (todos los nodos 1:1, todos los breakpoints) y
  código en verde (tests, linter, type-check, Theme Check), con las APIs verificadas como vigentes.
  Los tests se escriben **antes** que el código. Detalle en `eden-testing-rules.md`.
- La tarea está realmente completa, requerimiento por requerimiento y subtarea por subtarea.
- Sin `console.log`, `debugger`, código muerto ni archivos de playground.
- Sin errores de consola; los estilos no se escapan; los componentes compartidos siguen funcionando.
- QA en mobile, tablet y desktop — y se declara explícitamente qué se probó y qué no.
- Las tareas de diseño se verifican 1:1 contra Figma.
- Accesibilidad (WCAG AA) y SEO se sostienen en todo lo que se tocó.
- Seguridad: superficie declarada en el plan, auditoría del diff, críticos/altos bloquean; detalle en
  `eden-security-rules.md`.
- Anti-slop: capa funcional siempre y bloquea lo duro; estética solo sin diseño y con el sí del dev;
  detalle en `rules/on-demand/eden-antislop-rules.md`.
- Lo nuevo con configuración o lógica no obvia queda documentado en `docs/`.

## Cierre (por tarea, no opcional)

- PR abierto contra la rama destino, con qué se hizo, cómo probarlo y checklist de QA — **el detalle
  técnico vive aquí**.
- Un comentario en el ticket del tracker (`task.comment`) que **describe qué se hizo**, con lo que quedó fuera, el **link
  del PR** y el **link de preview apuntando a la página exacta del cambio** (uno por página tocada,
  nunca la home).
- El dev decide el estado siguiente de la tarea y a quién se asigna. Claude no lo decide.

## Honestidad del reporte

- Si algo falló, se dice, con la salida real.
- Si algo se saltó, se dice.
- Si algo quedó parcial, se dice qué falta.
- Un reporte optimista que no coincide con el código cuesta más que uno incómodo.

## Cuando algo no está claro

Se pregunta. Si el ticket se contradice, o contradice cómo funciona el proyecto, o las instrucciones del
dev chocan con el ticket: se saca a la luz y se pide una decisión. **Nunca se inventa un requerimiento
para no tener que preguntar.**
