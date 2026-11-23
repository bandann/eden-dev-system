---
name: section-mod
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:section-mod` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable
  de cambiar, ajustar o arreglar una sección: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: modifica una sección que YA EXISTE, sin rehacerla. Pide la URL del ticket
  (Asana, SMG Hub o ClickUp) y la del Figma si existen, además de lo que el dev quiera aportar;
  inventaría la sección
  actual, mide su blast radius (quién más la usa), extrae el Design Spec de lo que debe cambiar, aplica
  el cambio mínimo posible con defaults neutros y verifica que nada de lo existente se rompió. No
  commitea ni pushea.
argument-hint: "[sección] [| url-del-ticket] [| url-figma] [| qué hay que cambiar]"
disable-model-invocation: true
---

## Section Mod — modificar una sección existente

**En `/eden:go --auto`** (modo orquestador, `skills/go/SKILL.md`): las preguntas **no bloqueantes** de este skill no detienen el trabajo — se toma el supuesto más reversible, se anota en `.claude/context/questions-{tarea}.md` y se sigue. Las **bloqueantes** (las de la tabla de `go`) esperan al dev como siempre.

Argumento recibido: `$ARGUMENTS`

Aquí **no se construye de cero: se modifica**. La sección ya existe, probablemente está en producción y
casi seguro la usa alguien más. El trabajo es lograr el cambio pedido **sin romper nada de lo que ya
funciona**, con el diff más pequeño que lo consiga.

> **Idioma:** al dev, en español. Todo lo que quede escrito, en inglés.

**Lo que NO hace:** commitear, pushear, abrir PRs ni comentar en el tracker — eso es `turnoff-task`.

**Testing — test-first, y nada se entrega sin test** (`rules/eden-testing-rules.md`). El criterio de
aceptación se escribe **antes** que el código: del Figma sale el baseline visual (`test-visual
baseline`) y del requerimiento salen los tests de comportamiento (`test-code spec`). Ambos deben
**fallar primero** — un test que pasa antes de implementar no mide nada. Después se implementa hasta
verde.


**Modelos — la sesión principal planifica, los agentes ejecutan** (`rules/eden-model-strategy-rules.md`). La sesión principal
decide, verifica y habla con el dev; **el trabajo de traer datos o producir cambios se delega a agentes
(nivel `fast`)**, por rol: `explorer` (escanear e inventariar), `design-extractor` (Design Spec), `implementer`
(escribir), `design-auditor` (medir), `reviewer` (revisar). Los agentes se resuelven por rol con el roster del stack del proyecto
(`teams/{stack}/roster.md`, ver `rules/eden-team-rules.md`); si el stack no tiene roster, se usa
`teams/_generic/roster.md`. Lo que reporta un agente
es una afirmación: se verifica antes de darlo por bueno.


**Stack — antes de nada, saber en qué plataforma estás** (`rules/eden-stack-rules.md`). Lee
`project.stack` de `.claude/project-config.json`. Lo que aquí se llama "sección" no es lo mismo en cada
plataforma, y el módulo correspondiente es de lectura obligatoria:

| Stack | Módulo | Qué es una sección |
|---|---|---|
| **shopify** | `rules/shopify/eden-shopify-rules.md` | Una section/block de Liquid |
| **wordpress** | `rules/wordpress/eden-wordpress-rules.md` **+ el sabor** de `flavors/{wordpress.flavor}.md` | Pattern o bloque (FSE) · template part (clásico) · widget/plantilla (builder) · componente del front (headless) |
| otro | el núcleo + las convenciones del repo | Lo que el proyecto llame así |

Qué agente cumple cada rol (`explorer`, `implementer`, `reviewer`…) no lo dice esta tabla: lo dice el
roster del stack (`teams/{stack}/roster.md`); si el stack no tiene roster, `teams/_generic/roster.md`.

**En WordPress, si `wordpress.flavor` no está declarado, se pregunta antes de escribir código** — o se
propone correr `/eden:wp-setup`. Construir un bloque en un proyecto de tema clásico es trabajo tirado.


---

### Paso 1 — Recolectar el contexto (una sola pregunta)

```
Para modificar la sección necesito lo que tengas — lo que no haya, lo trabajo sin ello:

1. ¿Qué sección? (archivo, nombre o dónde la ves en el sitio)
2. URL del ticket (Asana, SMG Hub o ClickUp)  → {requerimientos y subtareas}
3. URL del Figma (con node-id) → {el diseño AL QUE DEBE LLEGAR}
4. Cualquier cosa que quieras aportar: qué está mal hoy, qué debe cambiar exactamente, qué NO
   se debe tocar, casos que ya fallaron, restricciones del cliente.
```

El punto 4 importa especialmente aquí: **"qué NO se debe tocar"** es la mitad del encargo cuando se
modifica algo vivo.

---

### Paso 2 — Inventario de lo que existe hoy

Antes de mirar el diseño nuevo, entiende lo que hay. **Delega el inventario y el blast radius al
`explorer` (rol)** (`rules/eden-context-rules.md`): te devuelve el resumen, no el volcado de los archivos.
Al terminar, descárgalo a `.claude/context/inventory-{sección}.md`.

```bash
# la sección y todo lo que arrastra
sed -n '1,200p' sections/{seccion}.liquid
grep -n "render\|include\|section\|asset_url" sections/{seccion}.liquid
```

Registra: su schema completo (settings actuales y sus defaults), presets, dónde viven sus estilos, su
JS, sus traducciones, sus snippets/bloques hijos, y su marcado.

**El comportamiento actual es el contrato.** Antes de cambiar nada, sabe exactamente cómo se ve y se
comporta hoy: es contra eso que se mide si algo se rompió.

---

### Paso 3 — Blast radius (obligatorio, no opcional)

Quién más consume esto:

```bash
grep -rn "{section-type}" templates/*.json 2>/dev/null
grep -rn "{nombre-de-la-seccion}\|{clase-css}\|{funcion-js}" --include="*.liquid" --include="*.js" --include="*.css" --include="*.json" .
```

- ¿En cuántas páginas/plantillas está montada?
- ¿Qué instancias existen y con qué valores configurados?
- ¿Sus estilos o su JS los comparte con otra sección?

Si el proyecto tiene `docs/sitemap.md`, ahí está el blast radius ya calculado — verifícalo igual.

**Un cambio en una sección de 20 páginas no es el mismo trabajo que en una de una sola.** Lo que
encuentres se declara en la propuesta.

**Si el proyecto tiene grafo** (`rules/eden-brain-rules.md`), añade la fuente que el texto no ve:

```bash
graphify affected "{la sección o su clase}" --depth 2
```

Encuentra relaciones reales —quién la renderiza, quién importa su JS, qué depende de ella— que un grep
no puede ver. **Se suma al grep, no lo sustituye**, y el reporte dice qué fuente encontró cada cosa.

⚠️ **En WordPress el blast radius nunca es una sola búsqueda.** Parte del sitio vive en la base de datos
y el `grep` del repo no la ve — delega al `explorer` (rol), que en WordPress mira código y base de datos:

```bash
grep -rn "{nombre}" wp-content/themes/{child} wp-content/mu-plugins
{wp} db search "{shortcode|clase|wp:{prefijo}/{bloque}}" --stats
```

Renombrar un bloque, un shortcode o una clase que **ya está en contenido publicado** rompe páginas que
nadie va a revisar: el contenido guarda el nombre viejo. Si el sabor es **page-builder**, además, el
diseño entero está en la DB y una plantilla global repinta al instante todas las páginas que la usan.

---

### Paso 4 — El diseño al que debe llegar

Si hay Figma, se mide (`ignition-task/references/figma-extraction.md`), por breakpoint. Y luego, la
pregunta que define el trabajo:

**¿Qué difiere entre lo que hay y lo que debe haber?** Elemento por elemento, con números:

```
{elemento}  hoy: padding-top 24px · font-size 16px
            debe: padding-top 32px · font-size 18px
            Δ    +8px · +2px
```

Eso es el alcance real. Todo lo demás **no se toca**.

**Fuente de diseño y anti-slop.** Si el cambio toca UI o textos al usuario final, lee
`${CLAUDE_PLUGIN_ROOT}/rules/on-demand/eden-antislop-rules.md`. Sin Figma, captura, imagen ni documento
de dirección, primero salvo que el proyecto declare `uiux.mode: off`, **propón** UI/UX Pro Max con el bloque 🎨 de `skills/uiux-pro/SKILL.md` y **espera la respuesta**; solo con un sí sigue ese skill (nunca lo corras por tu cuenta). Con un no, sigue como hasta ahora; después aplica `antislop.mode`: con `ask`, muestra el bloque 🧹 de la regla y espera la respuesta.

**Animación.** Si la unidad incluye una animación que no sea una transición simple de hover o foco (un menú que se abre, un hero animado, un slider, apariciones al hacer scroll, texto animado) o toca una animación que ya existe, esa parte va al **rol `motion`** ([`teams/motion/roster.md`](../../teams/motion/roster.md), líder `/eden:motion`) y sigue [`rules/eden-motion-rules.md`](../../rules/eden-motion-rules.md): escalera de técnicas, solo `transform`/`opacity`, LCP visible, CLS 0, `prefers-reduced-motion` y tokens de movimiento. El plan declara el escalón; una librería de animación nueva es un sí aparte del dev.
Se anota en la propuesta del Paso 6.

---

### Paso 5 — Elegir el escalón (el más barato que funcione)

`rules/eden-component-strategy-rules.md`, aplicado a modificar:

| Escalón | Cuándo | Riesgo |
|---|---|---|
| **Configurar** | La sección ya puede hacerlo con sus settings actuales | Ninguno — se cambia el valor en la instancia |
| **Extender el schema** | Falta una opción; se agrega **con default = comportamiento actual** | Bajo, si el default es neutro de verdad |
| **Código acotado** | Ni configurando ni con settings; cambio dentro de esta sección | Medio — verificar que no se filtre |
| **Duplicar** | El cambio solo aplica a UNA instancia y rompería a las demás | Alto — copia con nombre, `type`, clases y assets propios |

**La regla que evita el desastre:** si la sección se usa en varias páginas y el cambio solo debe verse
en una, **no se cambia el comportamiento por defecto**. Se agrega la opción con default neutro y se
activa solo en esa instancia (desde el JSON de la plantilla o el editor).

**Tipografía responsive:** si Figma pide un tamaño distinto en mobile y la sección solo tiene un
control, es un hueco de settings — se propone la variante móvil siguiendo el patrón del proyecto,
**no** un override CSS.

---

### Paso 6 — Proponer y esperar el visto bueno

```
🔧 MODIFICAR SECCIÓN — {nombre}

Qué cambia
   {elemento} — hoy {x} → debe {y}   (Δ {z})

Escalón          {configurar | schema | código acotado | duplicar} — por qué
Archivos         {lista cerrada}
Settings nuevos  {nombre} · default {valor} ← reproduce el comportamiento actual

⚠️ Blast radius
   Montada en: {n} plantillas → {lista}
   Instancias existentes: {n} — ninguna cambia de aspecto {o: cambian estas y por qué}
   Comparte estilos/JS con: {lista o "nada"}

🚫 Lo que NO se toca
   {lo que queda explícitamente fuera}

🧹 Anti-slop: funcional · estética {sí|no} ({motivo})

🛡️ Superficie
   Entra:     {datos externos: settings, metafields, params} | nada
   Sale:      {dónde se pinta cada dato y en qué contexto}
   Quién:     {permisos} | público
   Secretos:  {…} | ninguno
   Terceros:  {…} | ninguno
   {Si no es superficie cero: cómo se protege cada punto}

❓ {lo que sigue sin resolverse}

¿Lo aplico así?
```

La superficie se declara según `rules/eden-security-rules.md`; el cambio sigue la sección de seguridad
del módulo del stack.

Si el cambio implica alterar el comportamiento por defecto de algo compartido, **dilo en grande**: es
una decisión del dev, no tuya.

---

### Paso 6b — Tests primero (🔴), y el baseline de regresión

Modificar tiene una exigencia extra: **hay que poder demostrar que lo que no debía cambiar, no cambió.**

1. **Baseline de regresión, ANTES de tocar nada** — `test-visual baseline` sobre las **instancias
   existentes** que deben quedar idénticas. Ese baseline es la prueba objetiva de que el default neutro
   funcionó.
2. **Baseline objetivo** — del Figma nuevo, para la instancia que sí cambia.
3. `test-code spec` para el comportamiento nuevo, si lo hay.
4. Se corren: el de regresión **debe pasar** (nada ha cambiado todavía) y el objetivo **debe fallar**.

---

### Paso 7 — Aplicar el cambio mínimo

- **Si el perfil lo exige** (`shopify.backup_before_customizing`), guarda copia del
  código original de la sección antes de tocarla — comentario o archivo de respaldo, según lo que el
  proyecto ya use.
- Se tocan **solo** los archivos de la lista. Si aparece otro, se para y se reporta.
- **No se reformatea código heredado.** Solo lo que se modifica queda limpio; el resto se deja como
  está aunque tenga el formato inconsistente del tema.
- Nada de "ya que estoy": refactors, renombres o mejoras no pedidas se anotan y se proponen aparte.
- Valores del Design Spec, tokens del proyecto, textos por traducciones.
- Si la tarea viene de `/eden:w2shopify`, el Design Spec es la medición del sitio
  (`.claude/context/w2s/{sitio}/`); Figma, si existe, manda sobre ella.

---

### Paso 8 — Verificar que no se rompió nada

En este orden, porque el riesgo aquí es la regresión, no el bug nuevo:

1. **Las instancias existentes se ven igual que antes** — `test-visual run` contra el **baseline de
   regresión** del Paso 6b. Sigue en verde = el default neutro funcionó. Cualquier rojo aquí es un bug,
   no un ajuste: es una regresión medida, no una impresión.
2. **Diseño 1:1** en la instancia objetivo: `attention-detail` sobre la sección, o el `design-auditor` (rol).
3. **Las otras páginas que la montan** siguen funcionando (estilos, JS, consola limpia).
4. **Validación del stack** — Theme Check / linter / tests.
5. Estados: vacío, sin imagen, texto largo, un ítem, muchos.
6. Sin `console.log`, `debugger` ni código muerto.

Para un cambio con blast radius real, pásalo por el `reviewer` (rol) y **verifica lo que reporte**.

---

### Paso 9 — Documentar y reportar

- Si se agregaron settings o lógica no obvia → actualiza el doc de la sección en `docs/`.
- Si el proyecto tiene `docs/sitemap.md`, actualiza el estado de la sección.

```
✅ SECCIÓN MODIFICADA — {nombre}
   Escalón:    {cuál} — {qué se evitó tocar}
   Cambios:    {lista con el Δ real}
   Archivos:   {lista}
   Settings:   {n} nuevos con default neutro
   Regresión:  {✅ las {n} instancias existentes se ven igual | ⚠️ detalle}
   Diseño:     {✅ 1:1 | diferencias pendientes}
   Validación: {salida real}
   Sin commitear — `/eden:turnoff-task` para auditar y cerrar
```
