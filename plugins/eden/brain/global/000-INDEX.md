---
type: index
scope: global
updated: "{{DATE}}"
---

# 🧠 Cerebro global — Eden

Lo que hemos aprendido **como equipo**, a través de todos los proyectos. Cada cliente tiene además su
propio cerebro en `{proyecto}/.claude/brain/`.

> **Cómo se lee esto:** vista de grafo (`Ctrl+G`). Verde lo que es verdad, naranja cómo se hace, morado
> qué pasó, azul grisáceo los proyectos.

## La regla que hace útil este vault

**Nada llega aquí sin la aprobación del dev.**

Con 40+ tiendas, un caso particular promovido a regla general se propaga a todas — y ese es
exactamente el fallo que hace inservible una memoria automática. Un hecho sube de local a global
cuando:

- se ha **confirmado en dos o más proyectos**, o
- es del **stack**, no del cliente (Shopify, WordPress, Liquid, PHP, el editor de bloques…),

y en ambos casos `/eden:brain promote` lo **propone** y espera el sí.

## Por dónde entrar

- **[[working-style]]** — cómo trabaja el dev. Se carga solo al iniciar cada sesión.
- **`inbox/`** — lo que el cerebro aprendió solo y espera tu aprobación (`/eden:brain inbox`).
- **[[MOC-shopify]]** — lo que sabemos de Liquid, Horizon, schema, Theme Check.
- **[[MOC-wordpress]]** — sabores, seguridad, el blast radius que incluye la base de datos.
- **[[MOC-clientes]]** — diferencias entre clientes que **parecen iguales**. De las notas más rentables.
- **[[MOC-gotchas]]** — lo que mordió una vez, en cualquier proyecto.

## Las capas

### 🟢 Semántico — qué es verdad
`semantic/` · Afirmaciones, sin narrativa. **Cada hecho lleva de dónde salió y dónde se verificó**: un
hecho sin respaldo es una suposición con formato de certeza, y eso es peor que no tenerlo.

### 🟠 Procedural — cómo se hace
`procedural/` · Recetas y secuencias que aún no son un skill.
> **Usado 3 veces → deja de ser memoria.** Se convierte en skill o en regla del kit. Esta capa es la
> antesala del kit, no un cajón paralelo.

### 🟣 Episódico — qué pasó
`episodic/` · Solo lo que **también le pasaría a otro cliente**. Lo particular se queda en su proyecto.

### 🔵 Proyectos
`projects/` · Una nota por cliente que **apunta** a su cerebro local. No lo absorbe: lo referencia.
Aquí nunca hay código de clientes — se cita proyecto y ruta, nunca el contenido.

## Higiene

- **Un hecho equivocado es peor que ninguno.** Si algo resulta falso, se corrige o se borra — no se
  matiza.
- Si dos notas se contradicen, **gana la realidad del repo**, y se corrige la nota.
- Lo que lleva mucho sin verificarse se marca como dudoso, no se deja pasar por cierto.
- **Nunca**: secretos, tokens, credenciales, datos personales de clientes.
