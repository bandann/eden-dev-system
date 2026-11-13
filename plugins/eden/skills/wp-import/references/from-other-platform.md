# Migrar desde otra plataforma hacia WordPress

Migrar no es importar: **los modelos de datos no coinciden**, y la mitad del trabajo es decidir a qué
se mapea cada cosa. Eso se decide **antes** de mover un solo registro, con el dev, y queda escrito.

## Paso previo, siempre: el mapeo

```
🗺️ MAPEO — {plataforma origen} → WordPress

{entidad origen}  →  {post type / taxonomía / campo}   {qué se pierde}
…

Se pierde / no viaja
  {lo que no tiene equivalente y hay que resolver aparte}

Redirecciones
  {patrón de URL viejo} → {patrón nuevo}
```

**Lo que no viaja hay que decirlo antes de empezar**, no descubrirlo al final. Es lo que cambia la
estimación y, a veces, la decisión de migrar.

## Desde Shopify

| Shopify | WordPress |
|---|---|
| Product | CPT `product` de WooCommerce |
| Variants | Variaciones de producto |
| Collections | Categorías de producto |
| Product metafields | Meta / campos ACF / atributos |
| Pages | Páginas |
| Blog posts | Entradas |
| Customers · Orders | **Caso aparte** — datos personales, ver abajo |

- La vía razonable: **export CSV de Shopify → importador CSV de WooCommerce**, mapeando columnas a
  mano. Los importadores "mágicos" de un click suelen dejar variaciones rotas.
- **Las imágenes se descargan de la CDN de Shopify** y se suben como adjuntos. Hay que verificar que
  cada producto quedó con su galería, no solo con la principal.
- **Los clientes y los pedidos casi nunca deberían migrarse.** Son datos personales, el histórico rara
  vez se usa, y las contraseñas no son portables (los usuarios tendrán que restablecerla igual). Se
  propone no migrarlos; si el cliente los quiere, se trata como su propio proyecto con su propio
  consentimiento.
- **Las URLs cambian de forma** (`/products/x` → `/producto/x`). Sin redirecciones 301 el cliente pierde
  su posicionamiento: el mapa de redirecciones es **parte de la migración**, no un extra.

## Desde Wix / Squarespace

- No hay export real de contenido estructurado. Lo que hay: el **RSS del blog** (parcial) y raspar las
  páginas.
- El contenido de las páginas se **rehace**: sus editores generan markup propio que no significa nada en
  WordPress. Migrar el HTML tal cual produce páginas imposibles de editar después.
- Lo que sí se conserva y hay que planificar: textos, imágenes, estructura de URLs y SEO.
- **Se estima como construcción, no como migración.** Prometer "traemos el sitio" y entregar páginas
  rotas es el fallo típico de estos proyectos.

## Desde otro WordPress

El caso fácil, si es el mismo modelo de datos: WXR (`content-import.md`) o migración completa
(`from-production.md`). Se complica cuando el origen usa otro tema o otro builder:

- **El contenido de un builder no viaja a otro.** Elementor → bloques es rehacer. Si el destino cambia
  de sabor, el diseño se reconstruye; solo viajan textos e imágenes.
- Los campos ACF viajan si se exportan los grupos (`acf-json/`) **y** el contenido, en ese orden.
- Los shortcodes de plugins que no estén en el destino quedan como texto crudo en las entradas. Se
  buscan antes: `wp db search "[nombre-del-shortcode" --stats`.

## Redirecciones — no es opcional

Toda migración que cambie URLs necesita su mapa 301. Se prepara **antes** del lanzamiento y se verifica
después:

- Se exporta la lista de URLs vivas del origen (sitemap.xml, Search Console, Screaming Frog).
- Se mapea una a una, o por patrón donde sea regular.
- Se implementa en el servidor (nginx/apache) o con un plugin de redirecciones, según el hosting.
- **Se prueba una muestra real** tras el deploy, incluidas las URLs con más tráfico.

Es parte de `/eden:launch-check`, pero el mapa se construye aquí.

## Verificación de una migración

- Conteo por entidad, origen vs destino, con el número esperado **declarado antes** de migrar.
- Una muestra manual de 5–10 registros de cada tipo, revisados de verdad: campos, imágenes,
  taxonomías, precios y variantes si es comercio.
- Las URLs con más tráfico responden 200 o redirigen 301 al equivalente correcto.
- Los medios existen como archivos, no solo como filas.
- Los shortcodes o bloques huérfanos: `wp db search "[" --stats` y revisar lo raro.
