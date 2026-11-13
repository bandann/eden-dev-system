# Caché de diseño — Eden (Figma se mide una vez y se recuerda)

Regla **bajo demanda**: la leen los flujos que consumen Figma (`figma-extractor`, `design-auditor`,
`ignition-task`, `create-new-section`, `section-mod`, `figma-expert`, `attention-detail`,
`create-fundaments`, `create-sitemap`, `download-figma-img`). No se carga en todas las sesiones.

**El problema que resuelve:** cada tarea volvía a recorrer el mismo nodo de Figma por el bridge, aunque
nadie lo hubiera tocado. Eso gasta contexto, tiempo y la conexión con Figma Desktop. Con la caché, lo
que ya se midió se recuerda, y **solo se vuelve a medir lo que cambió**.

## Dónde vive

`python -I "${CLAUDE_PLUGIN_ROOT}/hooks/eden_design.py" where` lo dice. En este orden:

| Si el proyecto… | La caché está en |
|---|---|
| tiene vault local (`/eden:brain init`) | `{proyecto}/.claude/brain/design/` — se versiona con el repo |
| no tiene vault, pero existe el cerebro global | `~/.claude/eden-brain/projects/{proyecto}/design/` |
| no tiene ningún cerebro | `~/.claude/eden-cache/design/{proyecto}/` |

**Nunca se crean archivos en el repo de un cliente sin vault.** Dentro:

- `manifest.json` — por archivo de Figma (`file_key`): su estado (`lastModified`, `version`) y sus
  nodos; por nodo: sección, breakpoints, spec, capturas, fecha y **el estado del archivo del que se
  extrajo**. Por sección: sus nodos (mobile y desktop pueden ser nodos distintos).
- `specs/{file_key}/{node}.json` — el Design Spec (`skills/figma-expert/references/design-spec.md`) en
  JSON, con la misma estructura que el YAML. Es lo que se compara.
- `specs/{file_key}/{node}.md` — el mismo spec legible, **generado** desde el JSON: no se edita.
- `specs/{file_key}/{node}.prev.json` — el anterior, tras un cambio.
- `shots/` — las capturas de referencia. **Fuera de git** (el script escribe el `.gitignore`).

## El protocolo — caché primero

Ante cualquier enlace o nodo de Figma, **antes de llamar a una herramienta de extracción**:

1. **`lookup`** — `eden_design.py lookup "{url}"` (o `{file_key} {node}`, o el nombre de la sección).
   - `cached: false` → se extrae como siempre (paso 4).
   - `cached: true` → paso 2.
2. **Una sola llamada barata para saber si el nodo cambió: la huella.**
   `eden_design.py fingerprint-js {nodos}` imprime un script **de solo lectura**; se ejecuta con
   `figma_execute` (Desktop Bridge, sin token REST). Recorre el árbol de cada nodo en Figma y devuelve
   solo un hash corto por nodo: el árbol nunca llega al contexto. Los nodos son los del `lookup`
   (`node_id`, o `check_nodes` cuando el enlace apunta a un contenedor). El resultado se guarda tal
   cual en `.claude/context/figma-fp.json` y:
   `eden_design.py check-nodes {file_key} .claude/context/figma-fp.json`.
   *(Respaldo, solo si el bridge no puede ejecutar código pero hay token REST: `figma_get_file_data`
   `depth: 1` → `check-file {file_key} {meta.json} {node}`, que compara `lastModified`.)*
3. Según el veredicto de cada nodo (`nodes` en `check-nodes`, `node_verdict` en `check-file`):
   - **`same`** → **no se vuelve a medir nada.** Se dice al dev en una línea:
     `🎨 El diseño de {sección} es igual al guardado (extraído el {fecha}) — uso la caché.`
     y se trabaja con el `spec`/`md` de la caché (y sus capturas, si las hay).
   - **`changed`** o **`unknown`** → se vuelve a extraer **solo ese nodo** (paso 4). Los demás nodos
     del archivo no se tocan hasta que una tarea los necesite.
4. **Extraer y guardar.** El extractor devuelve el spec; la sesión lo escribe en
   `.claude/context/design-spec-{sección}.json` y lo guarda:
   `eden_design.py save {spec.json} --section {sección} --url "{url}" --fingerprint .claude/context/figma-fp.json
   [--alias {nodo del enlace}] [--shots {carpeta}]`. La huella se toma **antes** de extraer (paso 2,
   también la primera vez) para que la próxima comparación tenga contra qué. `--alias` va cuando el
   enlace apunta a un contenedor (una SECTION con los frames de mobile y desktop): así el mismo enlace
   encuentra la caché la próxima vez.
   - `first_time: true` → `🎨 Guardé el diseño de {sección} en la caché ({n} breakpoints).`
   - `same: true` → el archivo cambió, pero **este nodo no**: `🎨 {sección}: el archivo de Figma cambió,
     pero esta sección está igual.`
   - `same: false` → se le enseña al dev la lista `summary` **traducida a una frase por cambio**:
     ```
     🎨 {sección} cambió en Figma desde el {fecha anterior}:
        · desktop · título: 64 → 72 px
        · nuevo: botón secundario (160 px de ancho en desktop)
        · quitado: el botón de 180 px
     ```
     La caché **ya quedó actualizada** (el anterior está en `.prev.json`). Si hay trabajo hecho sobre el
     spec viejo, se dice qué partes del código afecta cada cambio.

**Sin conexión con Figma** (el bridge no responde): se trabaja con la caché y **se declara**:
`⚠️ No pude comprobar si el Figma cambió; uso el diseño guardado el {fecha}.` Nunca se presenta lo
guardado como verificado.

## Lo que la caché NO cambia

- **Figma sigue siendo de solo lectura** (`eden-design-rules.md`). La huella es un `figma_execute` que
  solo lee; probar que la caché detecta un cambio se hace en las pruebas, **nunca editando el archivo**.

- **Figma sigue mandando.** La caché es una copia de Figma, no una fuente propia: ante cualquier duda
  de un valor, o si el dev dice que el diseño cambió, se re-extrae. Nunca se edita un spec a mano para
  que cuadre con el código (`eden-testing-rules.md`).
- **El test visual** (`test-visual`) sigue midiendo el render contra Figma; la caché le ahorra la
  extracción cuando el nodo no cambió, no la medición del render.
- El dev puede forzar la medición: "vuelve a leer el Figma" → se salta el paso 3.

## Por qué la huella y no el diff de versiones ni `lastModified`

- `figma_get_changes_since_version` / `figma_diff_versions` **no ven** paddings sin variable, colores
  sin token, radios ni cambios de layout (lo dice su propia documentación). No sirven para afirmar
  "este nodo no cambió".
- `lastModified` va por la API REST: necesita un token personal vigente (comprobado: con uno caducado
  falla con 403) y es del archivo entero, así que cualquier edición en otra página invalida todo.
- La huella (`hooks/figma-fingerprint.js`) cubre tamaño, auto-layout, paddings, gaps, radios, textos,
  tipografía, fills, strokes, efectos, variables y propiedades de instancia de **todo el subárbol**, por
  nodo, y funciona solo con el bridge. Renombrar una capa también cambia la huella: entonces se
  re-extrae y el diff dice que solo cambió un nombre. Medido en un nodo real de 857 capas: la respuesta
  son 16 caracteres y es estable entre ejecuciones.
