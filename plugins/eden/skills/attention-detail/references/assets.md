# Referencia — Imágenes: comparar y exportar del Figma

Las imágenes son la parte del QA que más se salta, y la que más se nota cuando falla: un hueco, un
placeholder gris o una foto estirada arruinan una sección que por lo demás está perfecta.

## 1. Qué se compara en una imagen

| Aspecto | Qué mirar |
|---|---|
| **Presencia** | ¿Está la imagen que el diseño define, o hay un hueco/placeholder? |
| **Tamaño renderizado** | Ancho y alto reales en pantalla vs. el nodo de Figma |
| **Aspect-ratio** | ¿Se deforma? Es el defecto más visible de todos |
| **Ajuste** | `object-fit` / `object-position` — ¿recorta donde debe? |
| **Densidad** | ¿Sirve una versión 2x en pantallas densas, o se ve borrosa? |
| **Calidad técnica** | `width`/`height` presentes (evitan CLS), `srcset`, `loading="lazy"` bajo el fold |
| **Accesibilidad** | `alt` descriptivo; vacío **solo** si es puramente decorativa |

Una imagen del tamaño correcto pero sin `width`/`height` **es un hallazgo**: pasa el ojo y falla en
Core Web Vitals.

## 2. Cuándo se exporta del Figma

Cuando la sección **no tiene** la imagen que el diseño define:

- Hay un placeholder, un hueco o un color de relleno donde debería ir.
- La imagen que hay es visiblemente distinta a la del diseño.
- Falta una variante que el diseño sí especifica (por ejemplo, la versión móvil).

**No se exporta** cuando la imagen es claramente contenido del cliente (una foto de producto, un banner
de campaña): ahí el hallazgo es "falta el contenido", y lo carga el merchant. Se reporta, no se
sustituye con el mockup del diseñador.

## 3. Cómo se exporta

```
figma_get_component_image  → imagen del nodo
figma_capture_screenshot   → alternativa cuando el nodo no exporta bien
```

Criterios:

- **Resolución**: 2x sobre el tamaño del diseño, para pantallas densas.
- **Formato**: PNG si tiene transparencia; si no, el formato que el proyecto ya use. Si el proyecto
  sirve WebP/AVIF por su CDN, exporta el original y deja que la plataforma lo convierta.
- **Nombre**: descriptivo, en inglés, kebab-case, con breakpoint y densidad cuando aplique:
  `hero-banner-desktop@2x.png`, `value-props-icon-shipping.svg`.
- **Iconos**: SVG siempre que el nodo lo permita — no PNG.

## 4. Dónde se dejan

1. **Si el proyecto sirve assets locales y la imagen es parte del diseño** (iconos, ilustraciones,
   fondos decorativos) → directo a la carpeta de assets del proyecto (`assets/` en Shopify), y se
   referencia desde la sección con el sistema de imágenes del proyecto.
2. **Si no se puede colocar automáticamente** → se deja igualmente descargada, en una carpeta clara del
   proyecto, y **se le dice al dev dónde está y qué hacer con ella**.

Casos típicos del punto 2, y por qué:

| Situación | Por qué no se puede automatizar |
|---|---|
| La imagen se sube desde el admin (setting `image_picker`) | Vive en la tienda, no en el repo |
| Es contenido de un producto, colección o metafield | La carga el merchant |
| El proyecto no sirve assets locales para eso | Va por CDN o por un gestor de medios |

El reporte tiene que ser accionable, no un aviso genérico:

```
🖼️ IMÁGENES

✅ Colocadas en el proyecto ({n})
   assets/value-props-icon-shipping.svg  ← nodo 12:455

⚠️ Hay que subirlas a mano ({n})
   {ruta-de-descarga}/hero-banner-desktop@2x.png  ← nodo 12:118 · 2880x1200
   → Súbela en: Editor de temas › Home › Hero banner › Image
   Motivo: es un setting image_picker, se guarda en la tienda y no en el repo.
```

## 5. Lo que nunca se hace

- Sustituir una imagen del cliente por el mockup del diseñador y darlo por resuelto.
- Dejar un placeholder haciéndolo pasar por el diseño.
- Exportar en 1x y decir que coincide, cuando en pantalla densa se ve borrosa.
- Commitear imágenes pesadas sin avisar del peso — se reporta el tamaño de lo que se agrega.
- Borrar o pisar una imagen que ya existía en el proyecto sin que el dev lo apruebe.
