# Estrategia de componentes — Eden (reuse-first)

El objetivo de toda tarea es alcanzar el diseño **con el menor código posible** y **sin romper lo que ya
está en uso**. Código nuevo es el último recurso, no el primer movimiento.

Antes de crear un archivo, recorre la escalera **en orden** y detente en el primer escalón que resuelva.
En el plan se declara en qué escalón te quedaste y **por qué los anteriores no alcanzaban**.

## La escalera

**1 — Con lo que ya existe, tal cual.**
¿Se puede armar el requerimiento con componentes/secciones/bloques existentes usando solo la
configuración disponible? Si sí, no hace falta código. Es siempre el mejor resultado.

**2 — Configuración o preset.**
Una variante configurada de algo existente (un preset con nombre, una combinación de opciones ya
soportadas). Sigue sin ser código.

**3 — Extender por configuración (schema/props/settings).**
Si tal cual no llega, ¿se llega agregando opciones y configurándolas? Prefiere cambios **aditivos** de
configuración antes que cambios de lógica.

Extender algo compartido es seguro **solo si haces las dos cosas**:

- **Mides el blast radius primero.** Si el proyecto tiene cerebro (`eden-brain-rules.md`),
  `graphify affected "{lo que se toca}" --depth 2` encuentra las relaciones reales que el texto no ve —
  **se suma al grep, nunca lo sustituye**, porque cada fuente ve lo que la otra no.
  Busca todos los lugares donde se usa antes de tocarlo y pesa el
  riesgo. Un componente en 20 páginas no es lo mismo que uno de una sola. Lo que encuentres va escrito
  en el plan.
  ```bash
  grep -rn "{nombre-del-componente}" .
  ```
- **El default de la opción nueva reproduce el comportamiento actual.** Toda instancia existente debe
  renderizar **exactamente igual que antes** de que la opción existiera. El cambio es invisible hasta
  que alguien lo configura. Después se pone el valor distinto solo en la instancia que la tarea pide.

**Tipografía responsive.** Los bloques de texto se reutilizan en todas partes y Figma casi siempre
especifica tamaños distintos en mobile y desktop. Si el componente expone un solo control de tamaño,
mobile nunca puede quedar 1:1 — eso es un **hueco de configuración**, no un motivo para saltar a
código. Revisa qué controles ya tiene; si Figma difiere entre breakpoints y no hay control móvil,
**evalúa agregar una variante móvil** siguiendo el patrón del propio proyecto (pares de settings, o
`clamp()` fluido — lo que el proyecto ya use), con el default neutro de arriba. **Propónselo al dev con
tu recomendación** y procede con su confirmación.

**4 — Código mínimo y acotado.**
Si la configuración no alcanza, escribe la menor cantidad de código posible afectando **solo** el
componente en el que trabajas. Estilos acotados a ese bloque. Nada se filtra a lo global ni a otros
componentes, salvo que la tarea pida explícitamente un cambio global.

**5 — Componente nuevo (último recurso).**
Solo si 1–4 realmente no pueden. Duplicando el más parecido y modificando la copia, o desde cero.
Duplicar no debe dañar el original ni a nadie que lo consuma: la copia lleva su propio nombre, su propio
identificador, su propio namespace de clases y sus propios assets.

## Guardas en todos los escalones

- **Global vs local.** Si la tarea es un cambio global deliberado (rediseño de todos los botones),
  tocar código compartido es lo correcto. Si es un componente puntual, el cambio queda contenido.
- **Revisa los consumidores antes de tocar código compartido.** Siempre, sin excepción.
- **Sigue los patrones del proyecto**, no tus preferencias: dónde viven los estilos, cómo se registran
  los componentes, cómo se nombran los archivos.
- **Nunca rompas lo que ya está en producción** por conveniencia de la tarea actual.

## Nombres de campos y datos estructurados

Cuando una tarea necesita un campo, metadato o estructura de datos nueva, no inventes el nombre en
silencio. En el plan:

- Propón 2 opciones de nombre y recomienda una, con el motivo.
- Especifica dónde vive, de qué tipo es y qué pasa cuando está vacío (fallback).
- Explica qué tiene que crear el cliente/merchant en su panel, si aplica.
- Sigue las convenciones vigentes de la plataforma — verifícalas en la documentación actual, no de
  memoria.

## Verificar antes de asumir

Las plataformas cambian: etiquetas, opciones de schema, APIs, filtros. Ante cualquier duda o error,
consulta la **documentación vigente** en vez de confiar en la memoria, y contrástalo con cómo lo hace
**este** proyecto.
