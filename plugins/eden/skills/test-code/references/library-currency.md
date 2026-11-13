# Referencia — Verificar que lo que usamos es lo vigente

El error que este procedimiento evita: **usar una API que ya no es la recomendada**. Pasa el linter,
funciona hoy, y falla en producción meses después cuando la plataforma la retira.

> **La regla:** la memoria del modelo no es una fuente. Las plataformas cambian etiquetas, filtros,
> firmas y opciones, y el conocimiento entrenado tiene fecha. Se verifica contra la documentación
> actual, siempre.

## Cuándo se verifica

No en todo — eso sería insostenible. Sí en:

- Una API, filtro o método que **no sea trivial** y que no hayamos usado ya en este proyecto.
- Cualquier cosa donde el modelo dude, o donde haya varias formas de hacerlo.
- Cuando algo **falla sin motivo claro** — muchas veces es una firma que cambió.
- Antes de introducir una **librería nueva**.

Lo trivial y estable (un `map`, un `padding`) no necesita verificación.

## Cómo, con context7

```
1. resolve-library-id  → obtener el id de la librería
2. query-docs          → preguntar por lo concreto: la sintaxis, las opciones, el reemplazo
```

Se pregunta por lo **específico** ("cómo se declara hoy un color_scheme en el schema de una sección"),
no en general ("documentación de Shopify"): la respuesta útil es la que se puede contrastar con la línea
de código que vas a escribir.

**Si context7 no tiene la librería** —o no responde— se va a la documentación oficial del año en curso,
y si tampoco, **se reporta como no verificado**. No se rellena con lo que uno cree recordar.

## Qué verificar por stack

### Shopify / Liquid

Lo que más cambia, y lo que más silenciosamente rompe:

- **Tags y filtros de Liquid** — `{% include %}` está deprecado (`{% render %}`); los filtros de imagen
  y de dinero se han movido y renombrado varias veces.
- **Opciones de `schema`** — tipos de setting, `color_scheme_group`, límites de bloques, la forma de los
  presets.
- **Theme blocks** — la arquitectura de bloques anidables es reciente y ha ido cambiando.
- **Admin API (metafields/metaobjects)** — versión de la API, namespaces reservados, reglas de nombres.
- **Etiquetas de imagen** — `image_tag` y sus atributos (`fetchpriority`, `sizes`) han ido creciendo.

Fuentes: `shopify.dev` del año en curso y el **changelog** — y contrastarlo con **cómo lo hace este
tema**, que a veces va por detrás.

### JavaScript / Web Components

- Firmas y opciones de la librería.
- Métodos movidos de paquete o renombrados.
- APIs del navegador con soporte cambiante.
- Que la versión instalada (`package.json`) coincida con la doc consultada — **verificar la versión
  antes de leer la doc**, o se lee la de otra versión.

### Cualquier stack

- Dependencias con vulnerabilidades conocidas o sin mantenimiento.
- Peer dependencies rotas tras una actualización.

## Qué se hace con lo que se encuentra

| Hallazgo | Qué hacer |
|---|---|
| Lo que vamos a escribir está deprecado | **Se usa lo vigente**, desde el principio |
| Algo que el proyecto ya usa está deprecado | **Se reporta**; arreglarlo es alcance nuevo y lo decide el dev |
| La doc contradice cómo lo hace el tema | Se declara la contradicción y se pregunta — puede que el tema esté atrasado, o que tenga una razón |
| No se pudo verificar | Se reporta como **no verificado**, con el motivo |

**No se arregla de paso.** Encontrar tres cosas deprecadas mientras haces un botón no convierte la tarea
en una modernización: se anotan, se reportan, y el dev decide si abre ticket.

## Cómo se reporta

```
📚 ACTUALIDAD

✅ Verificado vigente
   · {API} — {fuente consultada, fecha}

⚠️ Deprecado, en uso en el proyecto
   · {qué} — {archivo:línea}
     Vigente hoy: {reemplazo}
     Fuera del alcance de esta tarea → ¿abro ticket?

❓ No verificado
   · {qué} — {por qué}
```

La sección **❓** es la que da valor al resto: si todo aparece como verificado sin haberlo comprobado,
el informe entero deja de ser fiable.
