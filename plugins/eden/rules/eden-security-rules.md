# Seguridad — Eden (blindar lo que construimos)

La seguridad es un **requisito de construcción**, igual que la accesibilidad o el 1:1 con Figma: se
diseña en el plan, se escribe en el primer intento y se verifica antes de entregar. No es una pasada
final que alguien hará algún día.

Esta regla es el **núcleo agnóstico**. Lo propio de cada plataforma vive en su módulo
(`shopify/eden-shopify-rules.md` § Seguridad, `wordpress/eden-wordpress-rules.md` § Seguridad) y gana
sobre esto cuando es más específico.

## Los principios

- **Toda entrada es hostil.** Lo que llega de un formulario, la URL, una cookie, una API, un webhook…
  y también lo que escribe el merchant o el editor: metafields, rich text, ajustes del tema, contenido de
  un CMS, el contenido de un ticket. "Lo escribe el cliente" no lo hace seguro: su cuenta puede estar
  comprometida y su texto se pinta a miles de visitantes.
- **Se escapa en la salida, según el contexto.** HTML, atributo, URL, JavaScript y CSS se escapan
  distinto. Escapar para el contexto equivocado es lo mismo que no escapar.
- **Mínimo privilegio.** Cada token, scope, rol y endpoint con el mínimo permiso que necesita la tarea.
- **Defensa en profundidad.** Una capa que falla no debe dejar el sistema abierto: validar en el
  servidor aunque se valide en el cliente; permisos en el endpoint aunque la UI oculte el botón.
- **Nada secreto en el cliente ni en git.** Lo que llega al navegador es público. Lo que entra en git se
  queda en el historial para siempre, aunque se borre después.
- **Fallar cerrado.** Ante un error de validación o de permisos, se niega; no se sigue "por si acaso".

## Modelo de amenazas — en cada plan

Toda tarea que toque código declara su **superficie** en el plan, antes de escribir nada. Son cinco
preguntas y caben en cinco líneas:

```
🛡️ Superficie
  Entra:     {qué datos externos recibe: inputs, params, metafields, APIs, archivos} | nada
  Sale:      {dónde se pinta o se envía cada dato, y en qué contexto: HTML, atributo, URL, JS}
  Quién:     {qué permisos requiere y quién no debería poder hacerlo} | público
  Secretos:  {tokens, claves o credenciales que toca} | ninguno
  Terceros:  {scripts, librerías, APIs o apps nuevas que añade} | ninguno
```

Si las cinco respuestas son "nada/ninguno", la tarea tiene superficie cero y se dice. Si alguna no lo
es, el plan dice **cómo se protege**.

## Qué se revisa — el checklist del núcleo

| # | Área | Qué se comprueba |
|---|---|---|
| 1 | **Secretos** | Ningún token, API key, contraseña, clave privada o `.env` en el código, en git, en el tema ni en el bundle del navegador. Los secretos viven en variables de entorno, el keychain o el gestor de la plataforma |
| 2 | **Inyección y XSS** | Toda salida escapada según su contexto. Nada de `innerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `new Function` o `setTimeout(string)` con datos no confiables. SQL siempre parametrizado. Sin construir comandos de shell con datos de entrada |
| 3 | **Control de acceso** | Cada acción y cada endpoint comprueba **quién** pide y **si puede** (no solo si está logueado). Sin IDOR: un id en la URL no da acceso a recursos de otro |
| 4 | **Autenticación y sesión** | CSRF/nonce en toda acción que cambia estado. Cookies `HttpOnly`, `Secure`, `SameSite`. Sin tokens en URLs ni en `localStorage` si la plataforma ofrece algo mejor |
| 5 | **Dependencias y terceros** | Sin vulnerabilidades conocidas altas o críticas (`osv-scanner`, `npm audit`, `composer audit`). Versiones fijadas con lockfile. Scripts de terceros solo de origen confiable, con versión exacta y `integrity` (SRI) cuando se cargan de un CDN. Ninguna dependencia nueva sin preguntarle al dev |
| 6 | **Redirecciones y peticiones salientes** | Sin open redirects: un `return_to`, `redirect` o `next` solo acepta rutas relativas o dominios en lista blanca. Sin SSRF: el servidor no pide URLs que controla el usuario sin validarlas |
| 7 | **Archivos** | Subidas validadas por tipo real y tamaño, nunca ejecutables, nunca servidas desde una ruta que las ejecute. Sin path traversal (`../`) en rutas construidas con datos de entrada |
| 8 | **Datos personales** | Nada de PII en logs, en `console.*`, en analytics ni en URLs. Lo mínimo necesario, y solo donde la política de privacidad del cliente lo permite |
| 9 | **Lógica de negocio** | Precio, descuento, stock, cantidad y permisos se calculan y validan en el servidor. Nada que el navegador pueda manipular decide un importe |
| 10 | **Configuración y cabeceras** | Donde la plataforma lo permite: CSP, `X-Frame-Options`/`frame-ancestors`, HSTS, `Referrer-Policy`. Sin modo debug, listados de directorios ni errores detallados en producción |
| 11 | **Contenido incrustado** | `iframe` con `sandbox` y `title`; enlaces `target="_blank"` con `rel="noopener noreferrer"`; `postMessage` comprobando `origin` |
| 12 | **Formularios públicos** | Protección contra spam y abuso (honeypot, rate limit o captcha de la plataforma) en todo formulario que envía correo o crea registros |

## Severidad — y qué hace cada una

| Severidad | Qué es | Ejemplos | En `turnoff-task` |
|---|---|---|---|
| **Crítica** | Explotable ya, sin autenticación, con impacto alto | Secreto en el repo o en el navegador; SQLi; XSS almacenado; endpoint que escribe sin permisos | **Bloquea** |
| **Alta** | Explotable con poco esfuerzo o condiciones comunes | XSS reflejado; IDOR; CSRF en una acción sensible; open redirect; dependencia con CVE alta o crítica; precio manipulable | **Bloquea** |
| **Media** | Requiere condiciones poco comunes o el impacto es limitado | `innerHTML` con datos del merchant; script de terceros sin SRI; falta `rel="noopener"`; formulario sin anti-spam | Se reporta y queda en el PR |
| **Baja** | Endurecimiento, buena práctica | Cabecera de seguridad ausente; `console.log` con datos no sensibles | Se reporta |

**Excepción a un bloqueo:** solo el dev, de forma explícita y en el momento. Queda escrita en el PR en
una sección **Security exceptions** con el hallazgo, el motivo y quién lo aceptó. Un bloqueo nunca se
salta en silencio ni "para después".

## Herramientas — se usan si están, se declara si no

| Herramienta | Para qué | Comando |
|---|---|---|
| **gitleaks** | Secretos en el diff, el árbol o el historial | `gitleaks detect --source . --no-banner --redact` · `gitleaks protect --staged` |
| **semgrep** | Análisis estático (XSS, inyección, crypto débil) en JS/TS/PHP/Python | `semgrep scan --metrics=off --config p/owasp-top-ten --config p/secrets --error --quiet {rutas}` |
| **osv-scanner** | Vulnerabilidades conocidas en dependencias (npm, composer, pip…) | `osv-scanner scan source -r .` |
| `npm audit` / `composer audit` | Lo mismo, con la herramienta del ecosistema | `npm audit --omit=dev` |
| Theme Check / PHPCS-WPCS | Reglas de seguridad propias de la plataforma | Ver el módulo del stack |

**Localizarlas antes de declararlas ausentes.** En Windows, `pip install --user semgrep` deja el
ejecutable en `%APPDATA%\Python\Python3XX\Scripts\`, que a menudo no está en el PATH. Llamarlo por su
ruta completa **no basta** (lanza `pysemgrep`, que también tiene que estar en el PATH): se añade esa
carpeta al PATH del propio comando — `PATH="$PATH:$(cygpath "$APPDATA")/Python/Python312/Scripts" semgrep …`
en Git Bash. Con `--metrics=off` no envía telemetría. `gitleaks` y `osv-scanner` instalados con winget quedan en
`%LOCALAPPDATA%\Microsoft\WinGet\Links\`.

Si una herramienta no está instalada, la auditoría **no se bloquea**: la cubre el revisor leyendo el
código, y el reporte dice **qué herramienta faltó y qué no se pudo verificar**. Un escáner verde no es
una garantía: encuentra patrones, no fallos de lógica — por eso el revisor siempre lee el diff además.

## El hook de secretos

Antes de cada `git commit` que ejecuta Claude, un hook (`${CLAUDE_PLUGIN_ROOT}/hooks/eden_guard.py`) revisa lo
que va a entrar en el commit (`gitleaks` si está instalado; si no, patrones propios). Si encuentra un
secreto, **el commit no se ejecuta** y se dice qué archivo y línea lo contienen.

- **Arreglo correcto:** sacar el secreto a una variable de entorno o al gestor de la plataforma, y
  **rotarlo** si ya llegó a cualquier commit anterior o a un push.
- **Falso positivo:** se marca la línea con el comentario `eden-allow-secret` o se añade a
  `.gitleaks.toml` del proyecto, siempre con el sí del dev.
- Un secreto que ya se subió **está comprometido aunque se borre**: se rota, no se esconde.

## Los secretos tampoco se leen (`eden-secrets-readonly`)

El hook de commits evita que un secreto entre en git; `hooks/eden_secret_guard.py` evita que entre en
el **contexto**, porque lo que se lee puede terminar en una respuesta, una nota del cerebro o un log. En
cualquier herramienta bloquea **leer** `.env` y `*.env`, llaves privadas y almacenes (`*.pem`, `*.key`,
`*.p12`, `*.pfx`, `*.jks`, `id_rsa`…), lo de `~/.ssh` (salvo las públicas, `known_hosts` y `config`),
`~/.aws/credentials`, `.netrc`, `.pgpass` y `.git-credentials`: con la herramienta de lectura, con
`Grep` sobre esa ruta, o por shell (`cat`, `Get-Content`, `grep`, `cp`… sobre el archivo).

- **Sí se puede** crear, editar, borrar o listar esos archivos, pasarlos a un programa
  (`docker run --env-file .env`) y leer las plantillas (`.env.example`, `.sample`, `.template`).
- Para saber qué variables hay se usa la plantilla, o se le pregunta al dev **el nombre** de la variable,
  nunca su valor.
- Una excepción la pone el dev, y solo él: `security.allow_read` (patrones) en
  `.claude/project-config.json` o `~/.claude/eden-config.json`.

## Lo que NO se hace

- **No se ataca nada que no sea nuestro.** Ninguna prueba de intrusión, escaneo activo ni carga contra
  una tienda, un sitio, una API o un servicio de terceros sin autorización explícita del dueño. La
  verificación se hace sobre el código, el entorno local o un entorno de pruebas del proyecto.
- **No se desactiva una protección para que algo funcione** (CSP, nonce, verificación de HMAC, CORS
  estricto). Si estorba, se entiende por qué y se configura bien.
- **No se escribe código de "solo para probar"** que salte autenticación, y menos se commitea.
- **No se ponen secretos reales en ejemplos, tests, docs ni en el cerebro.**
- **No se hace teatro de seguridad**: un hallazgo sin `archivo:línea`, sin impacto y sin arreglo
  concreto no es un hallazgo.

## Quién hace qué

- El **plan** declara la superficie (`ignition-task`, `create-new-section`, `section-mod`).
- El **implementador** escribe seguro desde el primer intento, con el módulo del stack.
- El rol **`security-auditor`** (`eden-team-rules.md`) audita el diff de forma independiente: solo
  lectura, reporta con severidad.
- **`turnoff-task`** aplica la puerta: críticos y altos bloquean.
- **`/eden:security-check`** audita bajo demanda una tarea, una sección o el proyecto entero.
- **`launch-check`** hace la auditoría completa antes de publicar.
