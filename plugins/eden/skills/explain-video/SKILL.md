---
name: explain-video
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA O CON EL SÍ DEL DEV — NUNCA EN AUTOMÁTICO. Se usa cuando el dev escribe
  `/eden:explain-video`, o cuando `turnoff-task` le preguntó «¿hago un video explicativo?» y respondió que
  sí. No lo actives porque una tarea esté terminada ni porque haya capturas. — Qué hace cuando SÍ se
  invoca: arma un video corto que explica un ticket ya hecho, a partir de lo que pidió el ticket, el plan,
  el diff y el QA: escribe el guion por beats (lo que se dice + una acción visual), lo muestra y espera el sí,
  captura las páginas reales por breakpoint, anima el código y las anotaciones en el navegador y lo
  renderiza con subtítulos. Todo queda fuera del repo del cliente; publicarlo o subirlo se pregunta aparte.
argument-hint: "[URL o ID del ticket | rama | PR] [--lang en|es] [--format vertical|horizontal]"
disable-model-invocation: true
---

## Explain video — el ticket hecho, explicado en un video corto

Argumento recibido: `$ARGUMENTS`

Un video corto (20–45 s, vertical) que cuenta **qué se pidió, qué se hizo y cómo se ve**, para el cliente, el PM o el
equipo. Lleva **voz en off** por beat: cada beat dura exactamente lo que se dice en él, y los subtítulos
cinéticos van con la voz.

Piezas (todas del kit, sin dependencias de npm):

- `${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py` — carpeta, validación, guion legible, subtítulos.
- `${CLAUDE_PLUGIN_ROOT}/scripts/video/render.mjs` — maneja Chrome/Edge por el protocolo de DevTools
  (Node 22+): capturas reales y render cuadro a cuadro del reproductor.
- `${CLAUDE_PLUGIN_ROOT}/scripts/video/player.{html,css,js}` — las escenas animadas, en HTML/CSS/JS.

> **Idioma.** Al dev, en español. El video (títulos y narración) en **inglés** por defecto, como todo lo
> que va al cliente; `--lang es` o `video.lang` en `.claude/project-config.json` lo cambian.

---

> **Desde `turnoff-task`** (Paso 8b): el material del Paso 2 ya está en el reporte de cierre; se empieza en el
> Paso 3. El sí del dev al video no es el sí al guion: la tabla de beats se aprueba igual.

### Paso 1 — ¿Hay con qué?

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/video/render.mjs" tools
```

Necesita Node 22+, Chrome/Edge/Chromium y ffmpeg. Con el ffmpeg que trae Playwright sale `.webm`; con un
ffmpeg completo, `.mp4`. Si falta ffmpeg, **no lo instales tú**: díselo al dev
(`winget install Gyan.FFmpeg` en Windows, `brew install ffmpeg` en macOS) y detente.

### Paso 2 — Juntar el material (solo leer)

Del ticket (`task.read`), del checkpoint y el plan aprobado, del diff de la rama
(`git diff {base}...HEAD --stat` y los hunks clave), del reporte de cierre de `turnoff-task` si existe
(completitud, QA, medidas), y de las URLs de preview de la página exacta del cambio. Del cerebro, lo que
el recall traiga del proyecto. **No se inventa nada**: lo que no está en esas fuentes no va al guion.

### Paso 3 — Carpeta del video

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py" init --name {ticket-id o rama} --cwd {proyecto}
```

Crea `~/.claude/eden-videos/{proyecto}/{nombre}/` con `video.json` y `shots.json` de plantilla. **Nunca
dentro del repo del cliente.**

### Paso 4 — El guion por beats (y se espera el sí)

El estilo es el de los videos cortos de motion graphics: **vertical (9:16)**, fondo oscuro, **un solo color
de acento**, íconos de línea, y subtítulos cinéticos grandes en el centro. Un video son **beats**: cada beat
es **una cosa que se dice** (`say`) y **una acción visual** (`actors`). Reglas del guion, en este orden:

1. **Primero se propone una acción visual por bloque, después se construye.** Escribe la lista de beats
   (qué se dice → qué pasa en pantalla) y muéstrala antes de llenar coordenadas.
2. **Una idea por beat**: `say` corto (≤ 16 palabras; mejor 4–10). Los subtítulos salen solos, **4 palabras
   como máximo** a la vez, cortando en la puntuación. `*palabra*` la resalta con el acento.
3. **Cada beat cambia algo en pantalla**: algo entra, sale, se mueve o cambia. `check` rechaza un beat sin
   acción.
4. **Se conservan elementos entre escenas**: el mismo `key` en beats seguidos **persiste** y se transforma
   (posición, tamaño, contenido), no se corta. Una captura que pasa de navegador a teléfono, un contador que
   sube de 38 a 66, una insignia que cambia de texto.
5. **Se muestran las magnitudes**: un número del ticket o del QA va como `counter` o `bars`, no solo dicho.
6. **No se repite el subtítulo** con un `text` igual en pantalla: el texto en pantalla complementa.
7. Lenguaje del cliente, voz activa, nada que no esté en el ticket, el diff o el QA. 20–45 s en total.

Actores (`kind`, coordenadas `x`/`y` = centro en % de la pantalla, `w` ancho en %, `h` alto en % cuando
aplica; `scale`, `opacity` opcionales):

| `kind` | Para qué | Campos |
|---|---|---|
| `badge` | Etiqueta corta (ticket, sección) | `text` |
| `text` | Titular grande (`*palabra*` en acento) | `text`, `size` |
| `icon` | Ícono de línea que se dibuja | `name`: check, code, bug, mobile, desktop, page, link, image, cart, clock, sparkle, layers, search, bolt, arrow, eye, shield, gauge |
| `shot` | Captura en un marco `browser` o `phone`; con `before` hace la cortina antes/después | `src`, `before`, `device`, `marks[{x,y,w,h,at}]` en % de la captura, `pan` |
| `counter` | Una magnitud que cuenta | `value`, `from`, `label`, `prefix`, `suffix`, `decimals` |
| `bars` | Varias magnitudes comparadas | `items[{label,value,hi}]` |
| `code` | El cambio clave, escribiéndose | `file`, `lines[{t:"+"/"-"/" ", s}]` (pocas líneas, sin secretos) |
| `prompt` | Una caja que se escribe (una instrucción, una búsqueda) | `text` |
| `card` | Una tarjeta (un componente, un paso) | `title`, `text` o `lines` |
| `list` | Lo hecho, con check que se dibuja | `items` |

Arriba del todo: `format` (`vertical` por defecto o `horizontal`), `accent` (el color de la marca del cliente o
de la agencia, si el proyecto lo tiene en sus tokens), `lang`. `duration` por beat es opcional: sale de lo que
dice (~155 palabras por minuto) hasta que hay voz; con voz, sale del audio de cada beat.

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py" script {carpeta}/video.json
```

Muestra la tabla **Dice → Acción visual → segundos**. **Preséntala al dev y espera su sí** antes de capturar o
renderizar: corregir texto es barato, volver a renderizar no.

### Paso 5 — Capturas reales

Llena `shots.json` (nombre, URL de preview **de la página exacta**, viewport, `mobile`, `wait`, `fullPage`,
`hide`/`blur` con selectores) y:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/video/render.mjs" shots {carpeta}/shots.json
```

Privacidad: solo páginas públicas o de preview. **Nunca** el admin con pedidos, clientes o datos
personales; si una página los muestra, `blur`/`hide` por selector y revisa la captura con Read antes de
usarla. No se llenan formularios ni se hace clic en nada.

### Paso 5b — Voz en off

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py" voice {carpeta}/video.json
```

Narra cada beat por separado (`audio/beat-NN.wav`) y arma la pista (`audio/voice.wav`); desde ahí cada
beat dura lo que dura su audio (+ un respiro). Si cambias una línea del guion, solo se vuelve a narrar esa.
Proveedor en `video.tts` de `~/.claude/eden-config.json` (o `--provider`/`--voice`):

| `provider` | Calidad | Coste y datos |
|---|---|---|
| `auto` (por defecto) | Kokoro si está instalado; si no, la voz del sistema | Gratis, local. **Nunca elige una API de pago sola** |
| `system` | Voz del sistema (Windows SAPI, macOS `say`, `espeak-ng`): robótica | Gratis, sin red |
| `kokoro` | Natural (Kokoro-82M, Apache-2.0), inglés y español | Gratis, local; vive en su propio entorno (`~/.eden/tts/venv`, Python 3.12) que crea `python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_voice.py" setup-kokoro` cuando el dev lo pide (~1 GB con el modelo) |
| `openai` | Muy natural (`gpt-4o-mini-tts`) | De pago; el texto sale de la máquina; clave en `OPENAI_API_KEY` |
| `elevenlabs` | Muy natural; `voice` = id de la voz | De pago; el texto sale; clave en `ELEVENLABS_API_KEY` |

Un proveedor de pago solo se usa si el dev lo configuró. Las claves salen siempre de variables de entorno.
`eden_voice.py status` dice qué proveedor se usará. En Windows con Smart App Control, `setup-kokoro` instala versiones de
`regex`, `spacy` y `transformers` que el sistema deja cargar (las más nuevas se bloquean hasta ganar reputación).

### Paso 6 — Validar y renderizar

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py" check {carpeta}/video.json
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_video.py" render {carpeta}/video.json
```

Para revisar un momento sin renderizar todo, o sacar la portada (`poster.png`):

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/video/render.mjs" still {carpeta}/video.json --at {segundos} --out {carpeta}/poster.png
```

Mírala con Read antes de renderizar: es la forma barata de ver que las capturas, las anotaciones y los
textos caen donde deben.

Con voz, `render` saca el video sin sonido y luego **une la voz** si hay un ffmpeg completo (mp4 con AAC). Con el
ffmpeg que trae Playwright (no tiene audio) deja el video, `audio/voice.wav` y un `preview.html` que los
reproduce juntos; `eden_video.py preview {carpeta}/video.json` lo regenera. Para un solo archivo con voz, el dev
instala ffmpeg (`winget install Gyan.FFmpeg`).

`check` lista lo que falta (archivos, campos, plantillas sin llenar). `render` escribe los subtítulos
(`video.srt`, `video.vtt`) y `script.md`, y renderiza. Si devuelve `run`, ejecuta ese comando en la shell
(pasa cuando el Python de la máquina no ve el ffmpeg de Playwright). Renderizar tarda: corre en segundo
plano y se avisa al terminar.

### Paso 7 — Revisar y entregar

Revisa el resultado (duración, que no falten beats) y dale al dev la ruta del video y de los subtítulos.
**Subirlo** al ticket, a un drive o enlazarlo en el comentario de cierre **es otra acción y se pregunta**.

---

### Lo que NO hace

- Correr sin la invocación del dev o su sí en `turnoff-task`.
- Escribir nada en el repo del cliente, ni instalar ffmpeg u otras herramientas.
- Capturar datos personales, el admin con datos de clientes, o páginas que no sean públicas o de preview.
- Publicar, subir o adjuntar el video sin preguntar.
- Inventar requerimientos o resultados que no estén en el ticket, el diff o el QA.

### Reporte

```
🎬 EXPLAIN VIDEO — {ticket}

Guion     {n} beats · {segundos} s · {formato} · {idioma}   (aprobado por el dev)
Capturas  {n} — {páginas y breakpoints}
Video     {ruta} ({formato}, {MB})
Subtítulos {ruta .srt} · {ruta .vtt}

Siguiente  {¿lo adjunto al ticket / lo enlazo en el cierre? — se pregunta}
```
