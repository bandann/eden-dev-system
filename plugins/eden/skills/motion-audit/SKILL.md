---
name: motion-audit
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa cuando el dev escribe
  `/eden:motion-audit`, o cuando `/eden:motion` (modos audit y optimize) o un flujo de Eden lo llama con el
  sí del dev. — Qué hace cuando SÍ se invoca: audita el rendimiento de las animaciones de una página,
  sección o proyecto. Corre el análisis estático del código (transition: all, propiedades de layout,
  listeners de scroll, setInterval, will-change permanente, sin prefers-reduced-motion, GSAP sin limpieza,
  autoplay sin pausa) y MIDE en un navegador real con la interacción que dispara la animación (scroll,
  hover, clic, tecla), en desktop y móvil, con la CPU ralentizada y con movimiento reducido: fps, cuadros
  lentos, tareas largas, layouts, CLS al animar, input más lento, LCP y qué propiedades se animan. Entrega
  hallazgos por impacto y, si se optimizó algo, la tabla de antes y después. No edita código.
argument-hint: "[URL de preview o dev server] [| rutas de código] [--scroll] [--hover SEL] [--click SEL] [--mobile] [--compare antes.json]"
disable-model-invocation: true
---

## Motion audit — cuánto cuestan las animaciones, medido

Argumento recibido: `$ARGUMENTS`

Lo hace el agente `eden:motion-perf-auditor` (o la sesión, si es una sola página). Reglas y presupuesto:
`rules/eden-motion-rules.md`. Herramientas: `scripts/eden_motion.py` (estático y comparación) y
`scripts/motion/measure.mjs` (navegador headless, sin paquetes de npm; Node 22+ y Chrome o Edge).

> Al dev, en español. Las mediciones van a `.claude/context/motion/` del proyecto.

### Paso 1 — Qué y dónde

La URL (preview del tema, dev server local, staging) y **qué interacción** dispara la animación. Si no se
dijo, se deduce del tipo: secciones y parallax → scroll; menú → clic en el botón y `Escape`; slider → clic en
siguiente; hover → el selector. **Nunca** producción con datos de clientes, ni formularios.

### Paso 2 — Estático

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_motion.py" lint {rutas}
```

Hallazgos por severidad con archivo:línea, porqué y arreglo. Son sospechas.

### Paso 3 — Medir

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_motion.py" measure {url} --scroll --out .claude/context/motion/{nombre}-desktop.json
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_motion.py" measure {url} --scroll --mobile --throttle 4 --out .claude/context/motion/{nombre}-mobile.json
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_motion.py" measure {url} --scroll --reduced --out .claude/context/motion/{nombre}-reduced.json
```

Cambia `--scroll` por `--hover SEL`, `--click SEL`, `--key Escape` o `--wait MS` según la interacción (se
pueden encadenar). El resultado trae el presupuesto con `pass`/`warn`/`fail` por chequeo: fps, cuadros
lentos, tareas largas, trabajo de layout, CLS al animar y al cargar, input más lento, propiedades de layout
animadas y, con `--reduced`, si algo sigue desplazándose.

### Paso 4 — Cruzar y reportar

Cada sospecha del estático queda **confirmada** o **descartada** por la medición. Los hallazgos se ordenan
por impacto (lo que falla el presupuesto primero) con su arreglo y su escalón de
`eden-motion-rules.md`. Si el dev quiere arreglarlos, eso es `/eden:motion optimize` con este informe como
punto de partida.

### Antes y después (optimizaciones)

Se mide el estado de partida **antes** de cambiar nada, con las mismas acciones y viewport, y al terminar:

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_motion.py" compare .claude/context/motion/{nombre}-antes.json .claude/context/motion/{nombre}-despues.json
```

### Reporte

```
📈 MOTION AUDIT — {página} · {fecha}

            Desktop        Móvil ×4 CPU     Reducido
fps         {n}            {n}              —
lentos      {n}            {n}              —
tareas      {n}            {n}              —
layouts     {n} ({ms})     {n} ({ms})       —
CLS anim.   {v}            {v}              {v}
input       {ms}           {ms}             —
se mueve    —              —                {nada | qué}

Hallazgos (por impacto)
 1. ❌ {regla} — {archivo:línea} — {qué cuesta} → {arreglo} (confirmado por la medición)
Antes→después {tabla}
Sin medir     {qué y por qué}
```

### Lo que NO hace

Editar código, instalar herramientas, medir producción con datos de clientes, llenar formularios o dar un
número sin decir cómo se midió.
