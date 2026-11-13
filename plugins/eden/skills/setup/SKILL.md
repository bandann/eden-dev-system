---
name: setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA. Prepara la máquina del dev para el plugin Eden y muestra su estado:
  sincroniza las reglas completas del kit en ~/.claude/rules, crea el cerebro y la config opcionales,
  detecta y configura el proveedor de IA (automático o manual), y migra una instalación antigua por copia
  de archivos. Siempre muestra primero qué haría y solo aplica con el sí del dev.
argument-hint: "[status | rules | brain | config | ai [auto | set … | test] | githooks [--remove] | hosts [install|uninstall …] | migrate]"
disable-model-invocation: true
---

## Eden Setup — dejar la máquina lista para el plugin

Argumento recibido: `$ARGUMENTS` (vacío = `status`)

El plugin funciona **sin nada de esto**: las reglas llegan por el resumen que inyecta el hook de inicio,
y sin cerebro el aprendizaje simplemente no corre. Este skill es para quien quiere más: las reglas
completas siempre activas, el cerebro que aprende, y una máquina limpia de la instalación antigua.

> **La regla de oro:** nada se escribe, se mueve ni se borra sin el sí explícito del dev. Cada modo
> corre primero **en seco**, se le enseña al dev la lista exacta, y solo con su sí se repite con
> `--apply`. Todo lo que se reemplaza o se retira queda respaldado en `~/.claude/backups/`.

El script es `${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py`:

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" {modo}            # en seco: qué haría
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" {modo} --apply    # solo tras el sí del dev
```

### Modos

| Modo | Qué hace |
|---|---|
| `status` | Versión del plugin, estado de las reglas en `~/.claude/rules` (al día · desactualizadas · sin sincronizar), si hay cerebro y config, qué proveedor de IA usa el destilador y qué CLIs y claves hay, qué escáneres de seguridad hay, y si queda algo de la instalación antigua |
| `rules` | Copia o actualiza las reglas Eden completas en `~/.claude/rules`, para que estén **siempre activas** en todas las sesiones. Las que estaban desactualizadas se respaldan antes. Las reglas propias del dev (cualquier otro archivo de esa carpeta) **no se tocan** |
| `brain` | Crea `~/.claude/eden-brain` (vault de Obsidian) y `~/.claude/eden-memory` si no existen, o completa sus carpetas. **Activa el aprendizaje automático**: desde ese momento el cerebro carga lo aprendido al iniciar y destila al cerrar. Para destilar hace falta un proveedor de IA: el CLI `claude` con sesión por defecto, o el que deje `ai` |
| `ai` | Detecta los proveedores de IA de la máquina y recomienda uno (solo lee). Subcomandos: `ai auto` (configuración automática), `ai set <proveedor> …` (manual), `ai test` (una llamada de prueba). Ver abajo |
| `config` | Crea `~/.claude/eden-config.json` (empresa, tracker por defecto, aprendizaje) si no existe. Nunca pisa uno existente |
| `githooks` | Instala el guard de secretos y de firma de la IA como **hooks de git** del repo actual (`pre-commit`, `commit-msg`, `pre-push`): protege cada commit y push **lo haga quien lo haga** — cualquier IA (aunque su herramienta no tenga hooks o no pueda bloquear) o el propio dev. Si el repo ya tenía un hook, lo conserva y lo sigue corriendo primero. Si el repo usa `core.hooksPath` (husky…), no escribe nada y le dice al dev qué línea añadir. Sobrevive a las actualizaciones del plugin. `githooks --remove` los quita y restaura lo anterior. Con `review.precommit.enabled: true` en `.claude/project-config.json`, el `pre-commit` además pide una revisión de IA del diff al proveedor de `ai` y bloquea solo hallazgos graves (opt-in: gasta tokens en cada commit). Se salta una vez con `git … --no-verify` (solo si el dev lo pide) |
| `hosts` | Lleva Eden a **otras herramientas de IA**. `hosts` detecta cuáles hay en la máquina (Codex, Cursor, Gemini/Antigravity, OpenCode, Kimi Code, Crush; Claude Code, Qwen Code y Grok Build cargan el plugin tal cual). `hosts install <herramienta…>` (o `--detected`) muestra qué escribiría y, con `--apply`, instala: el kit compartido en `~/.eden/kit`, los skills en `~/.agents/skills/eden-*` (la carpeta estándar que esas herramientas leen) y, por herramienta, sus agentes, sus hooks y su manifiesto. `hosts uninstall <herramienta…>` quita exactamente lo que escribió. Eden registra el hash de cada archivo: solo reemplaza o borra lo suyo sin tocar; lo que ya existía o lo que el dev modificó se respalda en `~/.eden/backups` (y lo que existía se restaura al desinstalar). `hosts doctor` revisa que todo siga en su sitio, sin tocado y al día (y que `python` exista); `hosts sync` reinstala todo tras actualizar el plugin. Codex carga el plugin de Claude de forma nativa, así que en Codex solo se agregan los agentes. Lo que Eden no puede tocar solo (confiar en los hooks de Codex con `/hooks`, la config de Kimi) se lo dice al dev en una línea |
| `migrate` | Retira lo que dejó el instalador antiguo por copia (skills y agentes `eden-*` copiados en `~/.claude`, la carpeta `~/.claude/eden/hooks`, plantillas y rosters copiados, y los hooks de Eden en `settings.json`), para que no se dupliquen con el plugin. **Conserva** las reglas, el cerebro, la memoria y la config |

### Proveedor de IA (`ai`)

El destilador del cerebro necesita un modelo. Eden puede usar **cualquiera**: un CLI (`claude`, `codex`,
`gemini`, `qwen`) o una API con formato Anthropic u OpenAI (OpenAI, Gemini, Kimi, GLM, MiniMax, DeepSeek,
Qwen, Grok, OpenRouter, Ollama local, o una propia). Hay dos caminos; **pregúntale al dev cuál prefiere
solo si no lo dijo**: "automático" para quien no quiere pensar en esto, "manual" para quien sabe qué quiere.

```bash
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" ai                        # detecta y recomienda (solo lee)
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" ai auto [--pick N]        # en seco: qué escribiría
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" ai set deepseek --model M # manual, en seco
python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_setup.py" ai test                   # en seco: qué llamaría
# … y cada uno con --apply solo tras el sí del dev
```

**Automático** (el camino por defecto para quien no sabe configurarlo):
1. Corre `ai`. Detecta, sin escribir nada: los CLIs de IA en el PATH (y si `claude` tiene sesión), las
   claves de API definidas en el entorno o en el bloque `env` de `~/.claude/settings.json`, si Claude Code
   ya apunta a un proveedor (`ANTHROPIC_BASE_URL` de Kimi, GLM, MiniMax, DeepSeek o Qwen) y si hay un
   ollama local. Para las APIs con clave pide la lista de modelos al propio proveedor y elige el más
   rápido. **Nunca muestra el valor de una clave.**
2. Enséñale al dev la lista en lenguaje llano: cuál recomiendas y por qué, en una línea. Si quiere otro,
   `ai auto --pick N`.
3. Corre `ai auto` en seco, muestra qué cambia en `~/.claude/eden-config.json` y pregunta **¿lo aplico?**
4. Con el sí, `ai auto --apply` (respalda la config anterior en `~/.claude/backups/`). Luego ofrece
   `ai test`: es una llamada real y corta, así que gasta unos pocos tokens. Pide el sí antes de correrla.
5. Si no detectó nada listo, explícale qué le falta en concreto (instalar o iniciar sesión en un CLI, o
   definir la variable con su clave) y pásale al camino manual. **Nunca le pidas que pegue la clave en
   el chat** ni la escribas en ningún archivo: la clave va en una variable de entorno que define él.

**Manual** (avanzado): `ai set <proveedor>` con lo que el dev decida: `--model`, `--key-env` (el nombre de
la variable, no la clave), `--base-url` y `--api anthropic|openai` para un proveedor propio o un servidor
local (vLLM, LM Studio…). Mismo ciclo: en seco, sí, `--apply`, `ai test`. Quien prefiera editar el JSON a
mano tiene el bloque `ai` documentado en `config/eden-config.example.json`.

Aviso de privacidad en una línea, la primera vez que elige una **API**: la sesión condensada (ya
redactada) y las notas del proyecto se envían a ese proveedor para destilarlas.

### Cómo se presenta

1. Corre el modo en seco y muestra la salida al dev en español, agrupada y sin muros.
2. Explica en una línea qué cambia para él (p. ej. "las reglas pasan a estar siempre activas").
3. Pregunta: **¿lo aplico?** — y espera.
4. Con el sí, corre con `--apply`, muestra el resultado real y dónde quedó el respaldo.
5. Si algo falla, se dice con la salida real; no se reintenta por otra vía sin preguntar.

Tras `rules` o `migrate`, recuerda que los cambios en `~/.claude/rules` y en `settings.json` se ven en la
**siguiente sesión**.
