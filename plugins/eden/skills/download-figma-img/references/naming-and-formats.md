# Referencia — Qué se exporta, en qué formato y con qué nombre

Las tres decisiones que hacen que un lote de assets sea utilizable o basura organizada.

## 1. Identificar qué es cada nodo

Recorriendo el árbol con `figma_get_component_for_development_deep`:

| Señal en el nodo | Es | Formato |
|---|---|---|
| Fill de tipo `IMAGE` sobre un rectángulo o frame | **Foto** | JPG · PNG si hay transparencia |
| Vector o grupo de vectores, tamaño pequeño (16–48px), en un set | **Icono** | **SVG** |
| Vector complejo, varios paths, tamaño grande | **Ilustración** | SVG si exporta limpio; PNG si no |
| Componente llamado `logo`, `brand`, `isotipo` | **Logo** | SVG · PNG de respaldo |
| Fill de imagen a ancho completo detrás de contenido | **Fondo / textura** | JPG · PNG con transparencia |

**No se exportan:**

- Rectángulos de color plano — eso es un token de color, no una imagen.
- Placeholders grises y cajas de "imagen aquí".
- Cuadrículas de layout, guías, máscaras y capas de anotación del diseñador.
- Nodos de texto, por decorativos que sean.

Ante la duda, **inclúyelo en el inventario marcado como dudoso** y deja que el dev decida. Es más barato
descartar un archivo de más que descubrir que faltaba uno.

## 2. Formato: por qué importa

- **SVG para todo lo vectorial.** Escala sin perder calidad, pesa poco y se puede recolorear por CSS —
  un icono en PNG obliga a exportar una copia por cada color y tamaño.
- **JPG para fotos.** PNG para una foto multiplica el peso sin ganar nada visible.
- **PNG solo cuando hay transparencia real** o el asset es un gráfico plano con bordes duros.
- Si el proyecto sirve **WebP/AVIF por su CDN** (Shopify lo hace), exporta el original en JPG/PNG y deja
  que la plataforma convierta. No exportes ya convertido: pierdes la fuente.

Un SVG exportado de Figma suele traer basura (ids generados, grupos vacíos, `clip-path` innecesarios).
No hace falta optimizarlo aquí, pero **anótalo en el reporte** si el archivo sale desproporcionadamente
grande para lo que dibuja — es señal de un vector mal construido en el diseño.

## 3. Densidad

- Fotos e ilustraciones rasterizadas → **`@2x`** sobre el tamaño del diseño, para pantallas densas.
- Si el diseño ya está hecho a 2x (frames de 2880px para un desktop de 1440), exporta a **1x**: el
  tamaño del frame ya es la densidad. Verifica el ancho del frame antes de multiplicar — exportar 4x por
  error produce archivos de varios MB.
- SVG nunca lleva densidad.

## 4. Nombres

```
{section-slug}--{qué-es}[--{variante}][@2x].{ext}
```

Reglas duras:

- **Inglés, kebab-case.** Sin espacios, sin acentos, sin mayúsculas, sin `ñ`.
- Doble guion (`--`) separa la sección de la descripción; guion simple dentro de cada parte.
- El `section-slug` sale del NODE-SECTION del sitemap cuando existe. Es lo que mantiene coherentes los
  nombres entre el diseño, el código y los assets.
- **Los iconos compartidos no llevan sección**: viven en `icons/` con su nombre propio
  (`icon-shipping.svg`), porque pertenecen al sistema, no a una sección.
- Numera solo cuando hay una serie real (`avatar-01`, `avatar-02`), y con cero a la izquierda para que
  ordenen bien.

### Cuando el nombre en Figma es inútil

`Image 24`, `Rectangle 7`, `Group 12` no dicen nada. Propón un nombre por **lo que se ve y dónde está**,
y **regístralo en la tabla "Renamed by us"** del manifiesto. Esa tabla es lo que permite, meses después,
encontrar el nodo original a partir de nuestro archivo.

## 5. Duplicados

El mismo icono o la misma foto aparece en varias secciones más veces de las que uno espera. Antes de
descargar, compara los nodos por su imagen de referencia:

- **Mismo asset en varias secciones** → se descarga **una vez**, va a `icons/` o a una carpeta común, y
  el manifiesto anota en qué secciones se usa.
- **Assets parecidos pero distintos** (dos fotos del mismo producto en ángulos distintos) → son dos
  archivos, con nombres que los distingan.

Bajar el mismo archivo cinco veces con cinco nombres distintos es el fallo más común de este trabajo, y
el que hace que después nadie sepa cuál usar.

## 6. Peso

Reporta el peso total y marca cualquier archivo que pase de ~500 KB. Un hero de 4 MB pasa desapercibido
en la carpeta y arruina el LCP de la página cuando alguien lo usa tal cual.
