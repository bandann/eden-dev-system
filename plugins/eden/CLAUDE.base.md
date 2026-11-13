<!--
  CLAUDE.base.md — bloque base para el archivo de instrucciones de cada proyecto de Eden: CLAUDE.md en
  Claude Code, AGENTS.md en Codex / OpenCode / Cursor / Kimi / Grok, GEMINI.md, QWEN.md (rules/eden-stack-rules.md).
  Cópialo/adáptalo cerca del inicio de ese archivo para que se lea cada sesión.
  Lo específico del cliente (paleta, tipografía, Figma, entornos) se agrega abajo, por proyecto.
-->

## Flujo de trabajo — Eden

Este proyecto sigue el kit `dev-system-eden`. Estas reglas no son negociables y aplican en cada sesión.

**Idioma — español SOLO para hablarle al dev; todo lo demás en inglés.** En español: la narración, los
planes que le presentas, las preguntas, los reportes de QA, los hallazgos y la explicación de errores
—es decir, lo que él lee en la consola. **En inglés, sin excepción, todo lo que queda escrito**:
código, variables, comentarios de código, commits, ramas, PRs (título y cuerpo), la documentación en
`docs/`, y **el comentario de cierre en el tracker**. Las plantillas del kit
(🚀 PLAN DE IGNICIÓN, 📋 REPORTE DE CIERRE) definen **estructura, no idioma**: al dev se le renderizan
en español; lo que se publica, en inglés. Emojis, campos y valores técnicos se conservan igual.

**Comandos del kit — SOLO por invocación explícita del dev. Nunca los actives por tu cuenta.**

| Comando | Qué hace | Cuándo se ejecuta |
|---|---|---|
| **`/eden:go`** | Enrutador: entiende el pedido, elige el comando del kit y lo **propone** — no corre nada sin el sí del dev | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:shopify`** | Líder del equipo Shopify: proyecto nuevo, onboarding o tarea, repartido a especialistas de principio a fin | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:shopify-setup`** | Base de un proyecto Shopify: tema, CLI, entornos, Theme Check, `project-config` — **nunca `theme push`** | Solo si el dev lo escribe, o encadenado desde `/eden:shopify` |
| **`/eden:react`** · **`/eden:react-setup`** | Líder del equipo React (SPA con Vite o Next.js) y el setup del entorno — **nunca despliega** | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:react-component`** · **`/eden:next-route`** · **`/eden:react-data`** | Un componente · una ruta de Next · la capa de datos, test primero | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:php`** · **`/eden:php-setup`** | Líder del equipo PHP (PHP sin framework y Laravel) y el setup del entorno — **nunca despliega ni toca bases reales** | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:laravel-feature`** · **`/eden:laravel-api`** | Una funcionalidad completa · endpoints con contrato, test primero | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:node`** · **`/eden:node-setup`** | Líder del equipo Node (Express, NestJS o sin framework) y el setup del entorno — **nunca despliega ni toca bases reales** | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:node-api`** · **`/eden:node-data`** | Endpoints con contrato · esquema, acceso a datos y colas, test primero | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:mobile`** · **`/eden:mobile-setup`** | Líder del equipo móvil (React Native con Expo o bare, Ionic con Capacitor) y el setup del entorno — **nunca publica ni envía OTA a producción** | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:mobile-screen`** · **`/eden:mobile-native`** · **`/eden:mobile-release`** | Una pantalla · una capacidad nativa · preparar la versión (publica el dev) | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:shopify-app`** · **`/eden:shopify-app-setup`** | Líder del equipo de apps de Shopify y el setup del entorno — **nunca `shopify app deploy` ni toca tiendas reales** | Solo si el dev lo escribe, o si `/eden:go` lo propone y el dev confirma |
| **`/eden:shopify-app-admin`** · **`-extension`** · **`-webhook`** · **`-deploy`** | Una pantalla del admin · una extensión o función · un webhook · preparar la versión (libera el dev) | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:ignition-task`** | Arranque **e implementación**: ticket del tracker + Figma + artefactos + rama + plan + build | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:create-fundaments`** | Levanta el design system del Figma al proyecto | Solo si el dev lo pide, o encadenado desde `ignition-task` |
| **`/eden:create-sitemap`** | Mapa de páginas y secciones (NODE-SECTION) con su nodo de Figma y su estado | Solo si el dev lo pide, o encadenado desde `ignition-task` |
| **`/eden:create-new-section`** | Construir UNA sección nueva, sin el ciclo completo | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:section-mod`** | Modificar una sección existente sin romper a quien la usa | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:figma-expert`** | Implementar un diseño de Figma 1:1: extracción medida, Design Spec, build y validación con Playwright | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:attention-detail`** | QA de fidelidad 1:1 contra Figma, medido en el navegador | Solo si el dev lo pide, o encadenado desde los dos anteriores |
| **`/eden:download-figma-img`** | Bajar todas las imágenes e iconos del Figma, nombrados por sección | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:pastel-sync`** | Trabajar los comentarios visuales de QA (Pastel) | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:mydaily`** | Reporte diario: bilingüe, con bloqueantes y su solución (+ formato del equipo si el perfil lo declara) | Solo si el dev lo escribe, o por su rutina programada L–V |
| **`/eden:estimate-time`** | Estimar y cargar tiempos por subtarea y sección, con desarrollo + pruebas | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:time-report`** | Registrar tiempo trabajado en el tracker — **siempre pregunta antes de cargar** | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:launch-check`** | Lanzamiento (P9) y garantía de 30 días (P10) | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:security-check`** | Auditoría de seguridad: diff, sección, proyecto, secretos o dependencias. Críticos y altos bloquean el cierre | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:qa-pixel-perfect`** | QA de la **página completa** vs Figma — mide **y corrige** hasta 1:1 | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:test-visual`** | TDD visual: baseline desde Figma y test 1:1 del render | Solo si el dev lo pide, o encadenado desde los skills de sección y el cierre |
| **`/eden:test-code`** | TDD de código + verificar que las APIs son las vigentes (context7) | Solo si el dev lo pide, o encadenado desde los skills de sección y el cierre |
| **`/eden:memory`** | Consultar, guardar y consolidar la memoria del kit | Solo si el dev lo escribe; los demás comandos la usan por su cuenta |
| **`/eden:context`** | Descargar contexto a disco en tareas largas, y recuperarlo | Solo si el dev lo escribe; los demás comandos descargan en sus hitos |
| **`/eden:wp-setup`** | WordPress: decidir sabor y entorno local del proyecto, y dejar la base lista | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:wp-local`** | WordPress: levantar el entorno local, tareas de WP-CLI y diagnóstico | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:wp-import`** | WordPress: bajar un sitio a local, importar contenido, migrar, o subir a staging | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:wp-feature`** | WordPress: CPTs, taxonomías, campos, endpoints, WooCommerce | Solo si el dev lo escribe o lo pide por su nombre |
| **`/eden:brain`** | El cerebro del proyecto: grafo de Graphify + vault de Obsidian con la memoria | Solo si el dev lo escribe; los demás comandos lo consultan por su cuenta |
| **`/eden:turnoff-task`** | Cierre: auditoría + commit/push + PR + el único comentario en el tracker | Solo si el dev lo escribe o lo pide por su nombre |

**No los dispares por contexto.** Que el dev pegue una URL de ticket (Asana, SMG Hub o ClickUp), mencione Figma, empiece una
tarea, diga que terminó o pida un commit **no** es una invocación. Si te parece que uno aplicaría,
**pregúntale** — no lo ejecutes. Sin el flujo Eden invocado, trabajas de forma normal.

Lo mismo para los agentes `eden-*`: son piezas de este flujo, no la forma por defecto de implementar o
revisar.

**Modelos — la sesión principal planifica, los agentes ejecutan.** La sesión principal (nivel `strong`) entiende, decide el alcance,
planea, reparte y **verifica**; los agentes (nivel `fast`) ejecutan: `eden:explorer` escanea e inventaría,
`eden:figma-extractor` extrae el Design Spec, `eden:implementer` escribe, `eden:design-auditor` mide y
`eden:qa-reviewer` revisa. **En proyectos WordPress se usan sus especialistas**: `eden:wp-explorer`
(inventario y blast radius, que ahí incluye la base de datos), `eden:wp-implementer`, `eden:wp-qa-reviewer`
(escapes, nonces, capabilities, contenido publicado) y `eden:wp-migrator` (importaciones y entorno). Todo trabajo de traer datos o producir cambios se delega, para que el contexto
de la sesión guarde el requerimiento y el plan en vez de volcados. Lo que reporta un agente es una
afirmación: se verifica. Nunca se delega hablar con el dev, decidir el alcance, ni commitear/pushear.

**Git — no se rompen nunca:**

- **La rama base siempre se pregunta.** No hay default.
- **Sin push directo a rama protegida.** `main`, `master` y `develop` están siempre protegidas; las
  demás se listan en el marcador de abajo.
- **Un PR contra `main` o `develop` requiere autorización explícita del dev en el momento** — es una
  autorización distinta a la de pushear la rama de trabajo.
- Sin force-push a ramas compartidas. Sin `.env`, secretos ni generados en el repo.
- Rama: `{tipo}/{ticket-id}-{slug}`; commits con Conventional Commits y trailer `Ticket:`; la URL del
  ticket guardada en la rama (`git config branch.<rama>.ticket-url`).

<!-- protected-branches: main, develop -->
<!-- eden-stack: shopify -->
<!-- ↑ Plataforma principal: shopify | wordpress | next | astro | custom. Determina qué módulo lee el
     kit (rules/shopify/ o rules/wordpress/). Si el stack no tiene módulo, se aplica el núcleo y se
     declara. Ver rules/eden-stack-rules.md -->
<!-- eden-wp: pendiente -->
<!-- ↑ Solo en proyectos WordPress. Lo reemplaza /eden:wp-setup por:
     eden-wp: flavor={block-theme|classic-theme|page-builder|headless} env={localwp|ddev|wp-env|docker}
            theme={ruta-child} mu-plugin={ruta} updated=YYYY-MM-DD
     Mientras esté "pendiente", el proyecto NO tiene sabor declarado: se pregunta antes de escribir
     código de WordPress, o se propone correr /eden:wp-setup. -->
<!-- eden-brain: pendiente -->
<!-- ↑ Cerebro del proyecto. Lo reemplaza /eden:brain init por:
     eden-brain: vault=.claude/brain graph=graphify-out/graph.json built=YYYY-MM-DD
     Tres capas: grafo de código (generado, desechable), vault de Obsidian (curado, se versiona) y
     memoria de trabajo (efímera). Ver rules/eden-brain-rules.md -->
<!-- Tracker (Asana por defecto, SMG Hub o ClickUp): se declara en .claude/project-config.json → tracker,
     no aquí. Ver rules/eden-tracker-rules.md -->
<!-- eden-profile:  -->
<!-- ↑ Perfil de operación (p. ej. acme-retail), creado a partir de profiles/_template/.
     Trae estados del tracker, ramas, roles, umbrales de QA y reglas de negocio, para que el kit no
     tenga que preguntarlos. Precedencia: dev > proyecto > perfil > ~/.claude/eden-config.json > default. Si algo se sale del
     perfil, se aplica el default y se declara. Ver rules/eden-profiles-rules.md -->

**Cómo construimos:**

- **Escalera reuse-first:** lo existente tal cual → preset/configuración → extender por settings →
  código mínimo acotado → componente nuevo (último recurso). El menor código posible; nunca romper lo
  que ya está en uso.
- **Los datos de diseño se miden, no se estiman.** Salen de Figma por el MCP de Figma Console. Si falta
  un valor, se pregunta — no se elige un número plausible, porque una regla de medir inventada hace que
  "pixel-perfect" sea inverificable.
- **Si Figma difiere entre breakpoints, Figma manda.** Un tamaño móvil distinto al de desktop es un
  requerimiento; se alcanza con una opción responsive de default neutro, nunca con un override CSS
  sobre un componente compartido.
- **Todo setting nuevo tiene default que reproduce el comportamiento actual.**
- Web Components en Light DOM, sin Shadow DOM. BEM acotado al bloque, tokens en vez de valores
  hardcodeados. Se sigue el patrón de este proyecto.

**Toda tarea cierra con:** QA en mobile/tablet/desktop, PR con el detalle técnico, y **un** comentario
en el tracker que **describe qué se hizo**, con lo que quedó fuera, el **link del PR** y el **link de
preview apuntando a la página exacta del cambio** (uno por página tocada, nunca la home). `ignition-task`
no comenta en el ticket ni commitea: eso es de `turnoff-task`. El dev decide el estado siguiente y a
quién se asigna.

**Testing — nada se entrega sin test.** El criterio de aceptación se escribe **antes** que el código:
del Figma sale el baseline visual y del requerimiento los tests de comportamiento, y ambos deben fallar
primero. Visual: colores (**y que vengan del token**), tipografía, espaciados, paddings, margins,
dimensiones, animación con `prefers-reduced-motion`, y **todo eso en cada breakpoint**. Código: tests,
linter, type-check, Theme Check, y las APIs verificadas como **vigentes** con context7 — nunca de
memoria. `turnoff-task` no cierra en rojo. Ver `eden-testing-rules.md`.

**Seguridad — requisito de construcción.** Todo plan declara su `🛡️ Superficie` (qué entra, qué sale,
quién puede, secretos, terceros). `turnoff-task` audita el diff con `security-auditor`: **críticos y altos
bloquean**; solo el dev puede aceptar una excepción y queda escrita en el PR. Un hook de commit bloquea
secretos. Ver `eden-security-rules.md`.

**Contexto en tareas largas.** Toda lectura grande —escaneo, árbol de Figma, diff largo, inventario—
**se delega a un agente**, que devuelve conclusiones; la sesión nunca ve el volcado. Lo trabajado se
descarga a `.claude/context/` en los hitos (al cerrar cada unidad, tras extraer Figma, tras auditar) y
en contexto queda el puntero. **Nunca** se sueltan el requerimiento, el plan, las decisiones ni lo
pendiente, y **nada se suelta sin haberlo escrito**. Ver `eden-context-rules.md`.

**Memoria — cuatro capas, dentro del cerebro.** Trabajo (`.claude/checkpoint.md`), episódica, semántica
y procedural, en dos ámbitos: `~/.claude/eden-brain/` (global) y `{proyecto}/.claude/brain/memory/`
(local). Se consulta al arrancar y se consolida al cerrar. **Lo local se escribe solo; lo global espera
la aprobación del dev.** No se memoriza lo que ya está en el repo — se enlaza. Ver `eden-memory-rules.md`.

**El cerebro del proyecto — tres capas.** El **grafo de código** (Graphify, generado y desechable), el
**vault de Obsidian** (curado, se versiona, notas enlazadas con `[[wikilinks]]`) y la **memoria de
trabajo** (efímera). Lo generado y lo curado **nunca se mezclan**: `brain/code/` y `graphify-out/` se
regeneran con un comando y **no se editan a mano jamás**.
Dos usos que cambian el día a día: antes de mandar a leer medio repo se pregunta al grafo
(`graphify query "..." --budget N`), y el blast radius suma `graphify affected` al grep — **sumando,
nunca sustituyendo**, porque cada fuente ve lo que la otra no (y en WordPress hace falta además
`wp db search`). ⚠️ **Un grafo desactualizado no parece desactualizado**: si es más viejo que el último
commit que toca lo preguntado, se dice y se verifica. Ver `eden-brain-rules.md`.

**Archivos de reglas (instalados con el kit):** `eden-workflow-rules.md`,
`eden-component-strategy-rules.md`, `eden-code-style-rules.md`, `eden-design-rules.md`,
`eden-quality-rules.md`, `eden-git-rules.md`, `eden-model-strategy-rules.md`, `eden-profiles-rules.md`,
`eden-memory-rules.md`, `eden-context-rules.md`, `eden-testing-rules.md`, `eden-stack-rules.md`,
`eden-brain-rules.md`, `eden-tracker-rules.md`, `eden-security-rules.md`, y el módulo de
la plataforma: `shopify/eden-shopify-rules.md` en proyectos Shopify, o
`wordpress/eden-wordpress-rules.md` **más su sabor** (`wordpress/flavors/{flavor}.md`) en proyectos
WordPress.

---

## Sistema de diseño de este proyecto

> **Lo rellena `create-fundaments` leyendo el Figma de este cliente** — no se escribe a mano y nunca se
> arrastra de otro proyecto. Mientras esté vacío, el proyecto **no tiene fundamentos** y cada
> `ignition-task` propondrá levantarlos. El detalle completo vive en `docs/design-system.md`.

- **Figma (desktop):** …
- **Figma (mobile):** …
- **Breakpoints:** mobile … px · tablet … px · desktop … px  ← anchos exactos de los frames de Figma
- **Tokens en código:** … (ruta)
- **Color:** … (familias de tokens primitivos y semánticos)
- **Tipografía:** … (escala fija o fluida — cuál usa este proyecto)
- **Escala de espaciado:** …
- **Doc completo:** `docs/design-system.md`
- **Sitemap del proyecto:** `docs/sitemap.md` (páginas, secciones y sus NODE-SECTION)

<!-- eden-fundaments: pendiente -->
<!-- Lo reemplaza create-fundaments por: eden-fundaments: updated=YYYY-MM-DD figma={key} version={id} -->

## Entornos

- **Repositorio:** …
- **Rama de integración:** …
- **Preview / staging:** …
