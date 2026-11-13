---
name: download-figma-img
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:download-figma-img` o lo pide de forma explícita e inequívoca. NO lo actives porque se
  hable de imágenes, iconos o assets: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se
  invoca: descarga TODAS las imágenes de un Figma —fotos, ilustraciones, logos e iconos, en jpg, png y
  svg—, las nombra según la sección a la que pertenecen y las guarda en una carpeta organizada del
  proyecto, con un manifiesto que enlaza cada archivo con su node-id. Elige el formato por tipo de
  asset, exporta en la densidad correcta, deduplica lo repetido y nunca sobrescribe nada sin avisar.
argument-hint: "[url-de-figma] [| sección o página] [| carpeta destino]"
disable-model-invocation: true
---

## Download Figma Img — bajar los assets del diseño

Argumento recibido: `$ARGUMENTS`

Sacar las imágenes de un Figma a mano es lento y produce nombres como `image-12.png` que nadie sabe a
qué pertenecen tres semanas después. Este skill baja **todo** el lote, **con nombres que dicen de dónde
salió cada archivo** y un manifiesto que permite volver al nodo exacto.

> **Idioma:** al dev, en español. **Los nombres de archivo y el manifiesto, en inglés** — son artefactos
> escritos.

**Lo que NO hace:** commitear, pushear, ni referenciar los assets desde el código. Descarga, nombra y
organiza; usarlos es de `create-new-section` / `section-mod`.

**Modelos:** la descarga y el renombrado los ejecuta un agente (nivel `fast`); la sesión principal decide el
alcance, la convención de nombres y la carpeta destino, y verifica el resultado
(`rules/eden-model-strategy-rules.md`).

---

### Paso 1 — Alcance (una sola pregunta)

```
Para bajar los assets necesito:

1. URL del Figma (con node-id si es una sección concreta)
2. ¿Qué alcance?
   · una sección     → solo sus imágenes
   · una página      → todas las secciones de esa página
   · todo el archivo → el lote completo (puede ser mucho: te digo cuántos son antes de bajar)
3. ¿Carpeta destino? (por defecto: design-assets/{page}/{section}/)
4. ¿Incluyo iconos? (por defecto sí, en SVG)
```

Si el proyecto tiene `docs/sitemap.md`, los NODE-SECTION ya te dan las secciones y sus node-ids: úsalos
en vez de recorrer el archivo a ciegas.

---

### Paso 2 — Inventariar antes de bajar

**Primero se cuenta, después se descarga.** Recorre el alcance y arma la lista de assets exportables:

```
figma_get_file_data                       → estructura, páginas y frames
figma_navigate                            → al frame de cada sección
figma_get_component_for_development_deep  → el árbol: qué nodos son imagen, vector o icono
figma_search_components                   → el set de iconos, si existe como librería
```

Qué cuenta como asset exportable (detalle en `references/naming-and-formats.md`):

| Tipo | Qué es | Formato |
|---|---|---|
| **Foto** | Nodo con fill de imagen (fotografía, render) | JPG, o PNG si necesita transparencia |
| **Ilustración** | Gráfico vectorial complejo, dibujo | SVG si el nodo lo permite; si no, PNG |
| **Icono** | Vector simple, normalmente de un set | **SVG siempre** que se pueda |
| **Logo** | Marca, del cliente o de terceros | SVG; PNG como respaldo |
| **Fondo / textura** | Decorativo detrás del contenido | JPG o PNG según transparencia |

**No son assets** y no se descargan: rectángulos de color plano, placeholders grises, cuadrículas de
layout y máscaras. Si dudas de uno, inclúyelo en la lista y **márcalo** para que el dev decida.

Presenta el inventario **antes** de descargar nada:

```
📦 ASSETS ENCONTRADOS — {alcance}

{sección}                     {n} assets
   photo    {nombre propuesto}.jpg   ← nodo {id} · {ancho}x{alto}
   icon     {nombre propuesto}.svg   ← nodo {id}
…

Total: {n} archivos · ~{peso estimado}
Destino: {carpeta}
⚠️ {duplicados detectados} · {dudosos} · {ya existen en el proyecto}

¿Los bajo así?
```

---

### Paso 3 — Nombres

La regla que hace útil todo esto: **el nombre dice a qué sección pertenece**.

```
{section-slug}--{qué-es}[--{variante}][@2x].{ext}
```

```
hero-banner--background@2x.jpg
value-props--icon-shipping.svg
product-card--placeholder.png
footer--logo-primary.svg
testimonials--avatar-01.jpg
```

- **En inglés, kebab-case, sin espacios, sin acentos, sin mayúsculas.**
- El `section-slug` sale del NODE-SECTION del sitemap si existe; si no, del nombre del frame,
  normalizado.
- Si el nombre del nodo en Figma es inútil (`Image 24`, `Rectangle 7`), **propón uno descriptivo** por lo
  que se ve y **anota que lo renombraste tú**.
- Los iconos de un set compartido no llevan prefijo de sección — van a `icons/` con su propio nombre
  (`icon-shipping.svg`), porque no pertenecen a una sección sino al sistema.
- Nunca dos archivos con el mismo nombre: si dos secciones usan la misma imagen, **se descarga una vez**
  y se anota dónde se reutiliza.

---

### Paso 4 — Carpeta destino

Por defecto, una carpeta de staging en el proyecto — **no** directamente en los assets del tema, para
no ensuciar el repo con archivos que quizá no se usen:

```
design-assets/
├── manifest.md
├── icons/
│   ├── icon-shipping.svg
│   └── icon-returns.svg
├── home/
│   ├── hero-banner--background@2x.jpg
│   └── value-props--illustration.svg
└── product/
    └── gallery--placeholder.png
```

Si el dev prefiere que vayan directo a la carpeta de assets del proyecto (`assets/` en Shopify), se
hace — pero se le dice **cuántos archivos y cuánto pesan** antes, porque eso sí entra al repo.

**Nunca se sobrescribe.** Si un archivo ya existe con ese nombre:

1. Compara: ¿es el mismo asset o uno distinto?
2. Si es distinto → agrega sufijo de versión y **repórtalo**, no lo pises.
3. Si es el mismo → sáltalo y anótalo como "ya estaba".

---

### Paso 5 — Descargar

Por cada asset del inventario aprobado:

```
figma_get_component_image  → imagen del nodo, en el formato y escala que corresponda
figma_capture_screenshot   → alternativa cuando el nodo no exporta bien
```

- **Densidad**: `@2x` para fotos e ilustraciones rasterizadas (pantallas densas). Los SVG no llevan
  densidad.
- **Los SVG se prefieren siempre** que el nodo sea vectorial: escalan, pesan menos y se pueden colorear
  por CSS.
- Si un nodo **falla al exportar**, no lo silencies: va al reporte con su node-id y el motivo.

---

### Paso 6 — Manifiesto

Un `manifest.md` en la raíz de la carpeta destino, **en inglés**. Es lo que convierte una carpeta de
imágenes en algo utilizable:

```markdown
# Figma assets — {project}

Source: Figma {url} · version {id} · exported {date}

| File | Type | Section | Figma node | Size | Dimensions | Notes |
|---|---|---|---|---|---|---|
| `home/hero-banner--background@2x.jpg` | photo | home/hero-banner | 12:118 | 340 KB | 2880x1200 | |
| `icons/icon-shipping.svg` | icon | shared | 45:12 | 2 KB | 24x24 | used in home, product |

## Renamed by us
| Figma name | Our name | Why |

## Not exported
| Figma node | Why |

<!-- eden-figma-assets: updated=YYYY-MM-DD figma={file_key} version={version_id} -->
```

Sin manifiesto, en un mes nadie sabe de qué nodo salió cada archivo ni si sigue vigente.

---

### Paso 7 — Reportar

```
✅ ASSETS DESCARGADOS — {alcance}
   {n} archivos · {peso total} · en {carpeta}
   Por tipo: {n} fotos · {n} ilustraciones · {n} iconos · {n} logos
   Por sección: {sección} {n} · {sección} {n}

♻️ Reutilizados (bajados una vez)
   {archivo} → se usa en {secciones}

✏️ Renombrados por nosotros ({n})
   {nombre en Figma} → {nuestro nombre}

⚠️ Ya existían en el proyecto ({n})
   {archivo} — {se saltó | se guardó como versión nueva}

❌ No se pudieron exportar ({n})
   {nodo} — {motivo}

Manifiesto: {carpeta}/manifest.md
```

Y una nota final para el dev: qué hacer con ellos — cuáles puede referenciar desde el código y cuáles
tendrá que subir por el admin porque son contenido del cliente.

---

### Relación con los otros comandos

- **`attention-detail`** exporta imágenes **puntuales** que faltan en una sección durante el QA. Este
  skill baja **el lote completo**, antes de construir.
- **`create-new-section` / `section-mod`** consumen lo que este dejó en la carpeta.
- Un manifiesto antiguo con el marcador `fl-figma-assets` se lee como `eden-figma-assets` y se propone
  migrarlo; nunca se reescribe en silencio. Se detecta con `grep -rnE "(eden|fl)-figma-assets" {carpeta}/manifest.md`.
- Si ya existe un `manifest.md` vigente, **no vuelvas a bajar todo**: compara contra la versión del
  Figma y baja solo lo nuevo o lo que cambió. Con la caché de diseño
  (`rules/on-demand/eden-design-cache-rules.md`), `check-file` dice qué nodos siguen `same` (sus assets
  no se bajan de nuevo) y cuáles hay que revisar (`nodes_to_recheck`).
