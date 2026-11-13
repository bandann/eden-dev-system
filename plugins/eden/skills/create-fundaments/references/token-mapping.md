# Referencia — Extraer y mapear el design system de Figma

Cómo sacar cada fundamento del archivo y convertirlo en tokens del proyecto sin romper lo que ya existe.

## 1. Dónde vive el design system en Figma

No siempre está donde uno espera. Búscalo en este orden:

1. **Variables del archivo** (`figma_get_variables`) — lo más fiable. Colecciones y modos.
2. **Variables de librería** (`figma_get_library_variables`) — si el DS vive en un archivo compartido.
3. **Estilos** (`figma_get_styles`, `figma_get_text_styles`) — sistemas más antiguos, previos a
   variables.
4. **Página "Design System" / "Foundations" / "Styles"** del archivo — `figma_get_file_data` para
   localizarla.
5. **Medición de los frames reales** — último recurso, cuando el DS no está formalizado. Se declara
   como tal: son valores observados, no declarados.

`figma_get_design_system_kit` y `figma_get_design_system_summary` dan el panorama rápido; úsalos
primero para saber con qué te vas a encontrar.

## 2. Color

```
figma_get_variables       → colección de color, con sus modos
figma_get_token_values    → valores resueltos por modo (light/dark, brand A/B)
figma_get_styles          → estilos de color, si no hay variables
```

Registra por cada color: nombre en Figma, valor por modo, opacidad, y si es **primitivo** (un color
crudo de la paleta) o **semántico** (un rol: texto, fondo, borde, acento).

- **Primitivos** → `--color-{familia}-{escala}` (`--color-brand-500`).
- **Semánticos** → `--color-{rol}-{variante}` (`--color-text-primary`, `--color-surface-muted`).
- **Los componentes consumen semánticos.** Si un semántico no existe para un rol que el diseño usa, es
  un hueco: se reporta.

Modos (light/dark) → se mapean al mecanismo que el proyecto ya tenga para temas o esquemas de color.
Nunca se inventa un mecanismo nuevo si el proyecto ya resuelve eso.

## 3. Tipografía

```
figma_get_text_styles
```

Por cada estilo: familia, peso, tamaño, line-height (px o %), letter-spacing, text-transform,
y **a qué breakpoint pertenece**.

Lo importante: **la misma escala suele tener valores distintos en mobile y desktop.** Extrae ambos y
decide con el dev cómo lo expresa el proyecto:

- **Pares de tokens** (`--font-h1--size` / `--font-h1--size-mobile`), o
- **Fluido** (`clamp()` entre el valor móvil y el de escritorio).

**Manda cómo está construido el proyecto.** Si es fluido, no le impongas una escala fija, y viceversa.

## 4. Espaciado

Rara vez está declarado como variables. Si no lo está, dedúcelo de los frames: recolecta los valores de
padding y gap del auto-layout de los componentes principales y busca el patrón (múltiplos de 4 u 8).

Se documenta **cómo se obtuvo**: "declarado en variables" vs "inferido de N componentes". No es lo
mismo y el equipo debe saberlo.

## 5. Breakpoints y grid

- Los **anchos exactos** de los frames de cada tamaño (375 / 768 / 1440 son habituales, pero se leen,
  no se asumen). Estos anchos son la regla de medir del `design-auditor` (rol): si están mal, todo el QA de
  diseño queda mal.
- Los **layout grids** de cada frame: número de columnas, gutter, margen exterior, ancho máximo del
  contenedor.

## 6. Radios, bordes, sombras, iconos

- Radios y anchos de borde: normalmente variables numéricas.
- Sombras: estilos de efecto, con nombre de elevación.
- Iconos: `figma_search_components` sobre el set de iconos — tamaños canónicos y grosor de trazo.

## 7. Estados

Las variantes de los componentes base (botón, input, link) contienen hover, focus, disabled, error.
`figma_analyze_component_set` sobre esos componentes da las combinaciones. Los estados se documentan
como parte de los fundamentos: son tan sistema como los colores.

## 8. Conflictos: cómo se resuelven

| Situación | Qué hacer |
|---|---|
| El token existe en el proyecto con otro nombre | **Se usa el del proyecto.** Se documenta la equivalencia. Nunca dos tokens para lo mismo. |
| Mismo nombre, distinto valor | ⚠️ **Se para y se pregunta.** Cambiarlo repinta todo el sitio. |
| Figma tiene un valor que rompe el patrón del resto (un gris de más) | Se reporta como posible inconsistencia del diseño; se pregunta al diseñador antes de canonizarlo. |
| El proyecto tiene un token que Figma no define | Se conserva y se anota como "fuera del design system". |
| Figma no define algo que el proyecto necesita | Es un **hueco**: va al reporte para el diseñador. No se inventa. |

## 9. Lo que nunca se hace

- Inventar un valor porque "falta uno en la escala".
- Renombrar tokens existentes del proyecto para que coincidan con Figma.
- Reemplazar el valor de un token en uso sin autorización explícita.
- Documentar como "declarado" algo que en realidad se midió a ojo.
