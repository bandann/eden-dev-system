---
name: w2shopify
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:w2shopify <url…>` o pide de forma explícita "duplica el diseño de este sitio en Shopify". Pegar una
  URL no es una invocación. — Qué hace cuando SÍ se invoca: reproduce en un tema Shopify (Horizon) el
  diseño de una página web hecha en cualquier tecnología. Primero confirma que el dev tiene derecho a
  reproducir ese diseño; luego mide el sitio en vivo con Playwright en cada breakpoint (capturas, estilos
  computados, secciones), lo trata como el Design Spec de la tarea, propone el mapeo a secciones de
  Horizon (reuse-first) y —con cada aprobación— levanta los fundamentos, construye las secciones y mide la
  paridad visual contra el original hasta 1:1. No migra productos ni contenido, no copia HTML ni CSS, no
  descarga assets sin permiso y no publica nada.
argument-hint: "<url> [url…] [--breakpoints 375,768,1440] [--inspiration]"
disable-model-invocation: true
---

## w2shopify — de una web a un tema Shopify

Argumento recibido: `$ARGUMENTS`

**La idea:** no se copia el código del sitio (suele venir minificado, atado a su framework y a sus
clases). Se **mide lo que el navegador renderiza** y se reconstruye limpio en Shopify, con las reglas de
Eden: tokens del proyecto, BEM, theme blocks, Web Components en Light DOM, accesibilidad, reuse-first.
La medición del sitio hace el papel del Figma: es la **fuente de diseño** de la tarea
(`rules/eden-design-rules.md`). Si además existe un Figma, **Figma manda**.

**Equipo:** el del stack Shopify (`teams/shopify/roster.md`) más `eden:web-extractor` para medir. Tú
(la sesión principal) decides, verificas y hablas con el dev; los agentes miden y construyen.

> **Nada corre sin aprobación**, y cada fase pide la suya: alcance → medición → plan → fundamentos →
> construcción. El dev puede parar en cualquiera.

---

### Paso 0 — Derecho, alcance y proyecto (antes de abrir el sitio)

1. **Derecho a reproducir el diseño.** Pregunta, y espera la respuesta:

   ```
   🔐 ¿Este sitio es del cliente, o tienes derecho a reproducir su diseño (p. ej. una migración a Shopify)?
      · sí  → modo clone: se mide y se reproduce 1:1
      · no / no sé → modo inspiration: solo estructura y patrones, sin colores, tipografías, textos ni
        imágenes exactos — el diseño final sale de los fundamentos del proyecto o de una propuesta aprobada
   ```

   Un diseño ajeno no se clona: el layout, los textos, las fotos, las fuentes con licencia y la marca son
   de su dueño. Con `--inspiration` en el argumento, el modo ya está elegido.

2. **Alcance:** las URLs y qué es cada una (home → `templates/index.json`, producto → `product.json`,
   colección → `collection.json`, página → `page.{nombre}.json`), y los breakpoints (por defecto 375, 768
   y 1440). Solo páginas públicas: nada detrás de un login.

3. **Proyecto:** tiene que ser un tema Shopify (`project.stack: shopify`, o la detección de
   `scripts/eden_stack.py`). Si no hay tema, ofrece `/eden:shopify-setup` antes y detente. **La rama base
   se pregunta** (`rules/eden-git-rules.md`), y se crea la rama de trabajo.

4. **Playwright:** este skill necesita el **MCP de Playwright** conectado. Si no responde, dilo y
   detente — no se mide leyendo el HTML del servidor.

### Paso 1 — Medir el sitio (solo lectura, delegado)

Delega en `eden:web-extractor` con el encargo de cinco partes (`rules/eden-model-strategy-rules.md`): las
URLs, los breakpoints, el modo y la carpeta `.claude/context/w2s/{sitio}/`. Devuelve capturas, el JSON de
`references/extract.js` por página y breakpoint, y un informe destilado.

**Verifica** el informe: abre dos o tres capturas y contrasta con el JSON que las secciones, el
contenedor y los cambios entre breakpoints son reales. Lo que no cuadre, se vuelve a medir.

### Paso 2 — Plan de mapeo (espera aprobación)

Con el rol `architect` (`eden:shopify-architect`, modo `decide`), por cada sección medida:

| Sección del sitio | Escalón reuse-first | Destino en el tema |
|---|---|---|
| {hint · qué es} | 1 tal cual · 2 configuración/preset · 3 extender con default neutro · 4 código mínimo · 5 sección nueva | {sección/bloques de Horizon o `sections/{prefix}-….liquid`} |

Más: las plantillas JSON de cada página, el header y el footer (grupos de secciones), y lo que **no** se
replica solo — interacciones complejas, configuradores, widgets de apps de terceros, formularios con
backend propio: se nombran y se decide con el dev (app de Shopify, funcionalidad nativa o fuera de
alcance).

Preséntalo con la `🛡️ Superficie` (`rules/eden-security-rules.md`): scripts de terceros que el sitio
cargaba y no se traen, formularios, embeds. **Espera el sí.**

### Paso 3 — Fundamentos (espera aprobación)

Los candidatos (paleta por uso, familias por rol, escala tipográfica y de espaciado, radios) van a
`/eden:create-fundaments` como **fuente "sitio medido"**: el mismo informe previo, el mismo mapeo a los
esquemas de color y al sistema de tokens del tema, nada escrito sin el sí del dev.

- **Fuentes:** si la familia está en la biblioteca de fuentes de Shopify, se usa esa. Si no, solo se sube
  la fuente si el dev confirma que tiene la licencia; si no, se propone la más cercana de la biblioteca.
- En modo **inspiration**, los fundamentos salen del proyecto o de una propuesta aprobada
  (`/eden:uiux-pro`), nunca del sitio.

### Paso 4 — Construir (por unidad, con el plan aprobado)

Cada unidad va a `create-new-section` o `section-mod` con el **Design Spec de la medición** como fuente
(en lugar del Figma): medidas por breakpoint, tipografía, color como token, contenedor, grillas y
estados. Lo construye el `implementer` del roster (`eden:shopify-theme-dev`, `eden:shopify-js-dev`), con
las reglas del stack.

- **Textos:** van a las traducciones del tema (`locales/`), nunca escritos en el Liquid; en modo
  inspiration, marcadores.
- **Imágenes y video:** el tema usa `image_picker`/`video` con marcador; descargar las del sitio y
  subirlas a Archivos de Shopify **solo con permiso explícito** (y en modo clone).
- **Nada del código del sitio** entra al tema: ni su CSS, ni sus clases, ni su JS.

### Paso 5 — Paridad visual (loop medir → corregir → medir)

Con el tema en `shopify theme dev` (lo levanta el dev o `eden:shopify-devops` con su autorización):

1. `test-visual` arma el **baseline desde la medición del sitio** (no desde Figma): por sección y
   breakpoint, las medidas del JSON.
2. `eden:design-auditor` mide el preview de Shopify en los mismos breakpoints y devuelve las diferencias
   en píxeles, elemento por elemento.
3. El implementer corrige; se vuelve a medir. Se para en **1:1** o cuando lo que queda está **nombrado y
   justificado** (una fuente sustituida, una interacción fuera de alcance, un dato que el tema resuelve
   distinto).

### Paso 6 — Reporte

```
🌐 w2shopify — {sitio} → {tema} · modo {clone|inspiration}

Páginas        {url → plantilla} …
Secciones      {n} · reutilizadas {n} · extendidas {n} · nuevas {n}
Fundamentos    {aplicados | pendientes} · fuentes {biblioteca | licenciadas | sustituidas}
Paridad        375 {✅ | n diferencias} · 768 … · 1440 …
Fuera de alcance {interacciones, apps, formularios con backend, contenido/productos}
Assets         {marcadores | subidos con permiso}
Archivos       .claude/context/w2s/{sitio}/
```

La entrega sigue por `/eden:turnoff-task` (revisión, seguridad, tests, sello, commit y PR con el sí del
dev). Este skill **no commitea, no pushea y no publica**.

### Qué NO hace

- Clonar un diseño ajeno sin que el dev confirme que tiene derecho.
- Migrar productos, colecciones, clientes, pedidos, blogs ni redirecciones (eso es una migración de
  datos, otro trabajo).
- Copiar HTML, CSS, JS o textos del sitio al tema, o descargar sus assets sin permiso.
- Iniciar sesión, rellenar formularios o cambiar estado en el sitio de origen.
- Publicar el tema, hacer `shopify theme push` o tocar `config/settings_data.json` sin el sí del dev.
