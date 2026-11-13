---
name: attention-detail
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:attention-detail` o lo pide de forma explícita e inequívoca, o encadenado desde
  `create-new-section` / `section-mod` para verificar lo recién construido. NO lo actives porque haya
  un Figma de por medio o porque el trabajo parezca terminado: si no lo pidió por su nombre, no se usa.
  — Qué hace cuando SÍ se invoca: QA exhaustivo de UNA sección contra su diseño. Mide el render real
  en el navegador con Playwright y el nodo de Figma con Figma Console, y compara 1:1 y en profundidad
  ancho, alto, tipografía, espaciados, padding, margins, colores e imágenes, por breakpoint y elemento
  por elemento. Si a la sección le faltan imágenes del diseño, las exporta del Figma y las deja listas
  en el proyecto. Mide y reporta; no da por bueno nada que no haya medido.
argument-hint: "<sección o URL de la página> [| url-figma] [| breakpoints]"
disable-model-invocation: true
---

## Attention Detail — QA de fidelidad, en profundidad

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre.

Argumento recibido: `$ARGUMENTS`

Una sola pregunta, respondida con números: **¿esta sección es idéntica al Figma, y si no, en cuánto se
diferencia?**

Este skill **no opina** sobre si el diseño es bueno ni si la diferencia "se nota". Mide, reporta con el
delta exacto y señala dónde está el código responsable. Corregir es del dev (o del skill que lo invocó).

> **Idioma:** al dev, en español. Los nombres de archivo de los assets exportados, en inglés.

**Modelos:** la medición la ejecuta un agente (nivel `fast`) (el `design-auditor`, o este mismo skill corriendo
en un agente); la sesión principal decide qué se mide, verifica los números y decide qué se corrige.
Ver `rules/eden-model-strategy-rules.md`. Los agentes se resuelven por rol con el roster del stack del proyecto (`teams/{stack}/roster.md`, ver
`rules/eden-team-rules.md`); si el stack no tiene roster, se usa `teams/_generic/roster.md`.

### La regla que sostiene todo

**Nada se estima.** Cada número viene de una medición real: del Figma por su MCP, o del navegador por
Playwright. Si algo no se pudo medir, **se reporta como no medido** — jamás se rellena con un valor
plausible. Un dato inventado convierte "1:1" en una frase vacía.

---

### Paso 1 — Preparar la medición

Necesitas tres cosas; pide en una sola intervención las que falten:

```
1. ¿Qué sección? (archivo, o la URL donde se ve)
2. URL donde está renderizada (preview, staging o local) — sin render no hay medición
3. Figma con node-id — si no está en el argumento, lo busco en docs/sitemap.md o project-config.json
4. ¿Breakpoints? (por defecto los del proyecto: mobile y desktop, tablet si el diseño lo define)
```

Los **anchos exactos** salen de `.claude/project-config.json` → `breakpoints`, que a su vez salen de
los frames de Figma. Si no están, `create-fundaments` los establece. **No inventes un ancho**: medir con
una regla equivocada invalida todo el informe.

Si el proyecto tiene `docs/sitemap.md`, el NODE-SECTION ya trae el node-id por breakpoint.

**Dependencia:** este skill necesita el **MCP de Playwright** conectado. Si no responde, dilo y detente
— no sustituyas la medición real por una inspección del código, porque el CSS escrito y el CSS
computado no son lo mismo.

---

### Paso 2 — Lado Figma

**Caché primero** (`rules/on-demand/eden-design-cache-rules.md`): si el nodo está en la caché de diseño
y `check-file` dice `same`, los valores esperados salen del spec guardado y este paso no llama a Figma.
Si no, por cada breakpoint (`ignition-task/references/figma-extraction.md`):

```
figma_navigate                            → al node-id de ese breakpoint
figma_get_component_for_development_deep  → el árbol con todas las medidas
figma_get_token_values / figma_get_text_styles → los tokens que usa
figma_capture_screenshot                  → referencia visual
```

Por elemento, anota: ancho, alto, posición relativa al contenedor, padding (4 lados), margin, gap,
tipografía completa (familia, tamaño, peso, line-height, letter-spacing, transform), color de texto y
fondo, bordes y radios, sombras, y **cada imagen** con su tamaño, aspect-ratio y ajuste.

---

### Paso 3 — Lado implementación (Playwright)

Procedimiento y snippets en `references/measuring.md`. En resumen:

1. `browser_resize` al **ancho exacto** del frame de Figma.
2. `browser_navigate` a la URL y esperar a que cargue todo (fuentes e imágenes incluidas — medir antes
   de que carguen las fuentes da tipografía falsa).
3. `browser_snapshot` para ubicar los elementos de la sección.
4. `browser_evaluate` para leer, por elemento, `getBoundingClientRect()` y `getComputedStyle()`: ancho,
   alto, paddings, margins, gaps, tipografía, colores, bordes, radios.
5. `browser_take_screenshot` de la sección, para el cotejo visual.

Se mide **lo computado y lo renderizado**, no lo que dice el CSS: un `padding: var(--x)` no dice cuánto
mide en pantalla.

---

### Paso 4 — Comparar, elemento por elemento

Emparejar cada elemento del Figma con el del DOM y calcular el delta en cada dimensión:

| Grupo | Qué se compara |
|---|---|
| **Dimensiones** | ancho, alto, ancho máximo del contenedor |
| **Espaciado** | padding (4 lados), margin (4 lados), gap |
| **Tipografía** | familia, tamaño, peso, line-height, letter-spacing, transform, alineación |
| **Color** | texto, fondo, bordes — y si sale de un **token** o está hardcodeado |
| **Bordes y efectos** | ancho, color, radio por esquina, sombras |
| **Imágenes** | presencia, tamaño renderizado, aspect-ratio, ajuste, `alt` |

Tolerancias y cómo tratar los redondeos, en `references/measuring.md`. Regla base: **diferencias por
debajo de 1px se ignoran; todo lo demás se reporta.**

Un hallazgo especial que siempre se marca: un color correcto **pero hardcodeado** en vez de venir del
token. Coincide en pantalla y aun así está mal.

---

### Paso 5 — Imágenes: comparar y, si faltan, traerlas

Si la sección **no tiene** una imagen que el diseño sí define (placeholder, hueco o imagen distinta):

1. **Expórtala del Figma** — `figma_get_component_image` sobre el nodo de la imagen, en la resolución
   adecuada (2x para pantallas densas).
2. **Déjala en el proyecto**, en la carpeta de assets que el proyecto use (`assets/` en Shopify), con
   nombre descriptivo en inglés y en kebab-case: `hero-banner-desktop@2x.png`.
3. **Si no se puede colocar automáticamente** —porque la imagen la sube el merchant desde el admin, o
   es un campo de contenido, o el proyecto no sirve assets locales— **déjala igualmente descargada** en
   una carpeta clara y **dile al dev exactamente dónde está y qué tiene que hacer con ella**:

```
🖼️ IMÁGENES EXPORTADAS DEL FIGMA ({n})
   {archivo}  ← nodo {node-id} · {ancho}x{alto}
   Guardadas en: {ruta}
   ⚠️ Estas hay que subirlas a mano: {cuáles y por qué}
      → {dónde: admin de Shopify, campo del editor, metafield…}
```

Nunca se sustituye una imagen por otra "parecida", ni se deja un placeholder haciéndolo pasar por el
diseño. Detalle en `references/assets.md`.

---

### Paso 6 — El reporte

Por breakpoint, ordenado por cuánto se nota la diferencia:

```
🔎 ATTENTION DETAIL — {sección}

📱 MOBILE @ {ancho}px
   ✅ {elemento} — coincide
   ❌ {elemento}
      Figma:  width 343 · padding 24/16/24/16 · font 18/600/1.4 · color {token}
      Actual: width 343 · padding 16/16/16/16 · font 16/600/1.4 · color #1a1a1a
      Δ       padding-top -8px · padding-bottom -8px · font-size -2px · color hardcodeado
      Dónde:  {archivo:línea}

🖥️ DESKTOP @ {ancho}px
   …

🖼️ Imágenes
   {estado de cada una · exportadas · las que hay que subir a mano}

📊 Resumen
   {n} elementos medidos · {n} coinciden · {n} con diferencias
   Por grupo: dimensiones {n} · espaciado {n} · tipografía {n} · color {n} · imágenes {n}

⚠️ No se pudo medir
   {qué y por qué}
```

Cuando todo coincide, se dice sin adornos: `✅ 1:1 con Figma en todos los breakpoints medidos` — pero
solo después de haber medido de verdad, y diciendo **cuántos** elementos se midieron.

---

### Paso 6b — Reglas de negocio del perfil

Si hay perfil activo con reglas que afecten a esta sección, se verifican junto con las medidas. Las
reglas son las que declare el perfil (`business_rules`), si existen: cada una que aplique se comprueba
**en todos los lugares** donde el tema la pinta, no solo aquí. Es el fallo más común y no se ve
mirando una sola página.

---

### Paso 7 — El loop

Este skill se usa en ciclo: **medir → corregir → volver a medir**, hasta que no queden diferencias. La
corrección la aplica el dev o el skill que invocó (`create-new-section`, `section-mod`); `attention-detail`
vuelve a medir y confirma.

No cierres el loop "porque ya quedó cerca". O es 1:1, o el reporte dice exactamente qué falta y por qué
se decidió dejarlo así.
