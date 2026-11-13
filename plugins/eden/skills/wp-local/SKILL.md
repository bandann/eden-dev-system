---
name: wp-local
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:wp-local` o lo pide de forma explícita e inequívoca. NO lo actives porque haya que
  levantar el sitio, porque algo falle en local o porque se mencione WP-CLI: si no lo pidió por su
  nombre, no se usa. —
  Qué hace cuando SÍ se invoca: opera el entorno local de WordPress del día a día. Levanta o repara el
  entorno (LocalWP / DDEV / wp-env / Docker), deja el sitio en condiciones de desarrollo (debug, Query
  Monitor, cachés fuera, correos y pagos apagados), ejecuta las tareas de WP-CLI que se le pidan, y
  diagnostica los fallos típicos —pantalla blanca, "no se aplica el cambio", permalinks rotos, error de
  conexión a la base de datos— buscando la causa en los logs en vez de probando a ciegas.
argument-hint: "[up | doctor | wp {comando} | reset] [| qué necesitas]"
disable-model-invocation: true
---

## WP Local — el entorno local, en condiciones

Argumento recibido: `$ARGUMENTS`

> **Idioma:** al dev, en español. Lo que quede escrito —scripts, docs— en inglés.

**Lo que NO hace:** tocar staging o producción (eso es `/eden:wp-import to-staging`), importar sitios (eso
es `/eden:wp-import`), commitear ni pushear.

**Requisito:** `/eden:wp-setup` ya corrió, así que `wordpress.local_env` está declarado. Si no lo está, se
dice y se ofrece correrlo — no se adivina el entorno.

---

### El prefijo de WP-CLI de este proyecto

Todo lo que hace este skill pasa por WP-CLI, y **cómo se invoca depende del entorno**:

| Entorno | Prefijo |
|---|---|
| LocalWP / WP-CLI global | `wp` |
| DDEV | `ddev wp` |
| wp-env | `npx wp-env run cli wp` |
| Docker propio | `docker compose exec wordpress wp --allow-root` |

Se lee de `wordpress.local_env` y **se usa el correcto en todos los comandos**. Un comando con el
prefijo equivocado falla con un error que no dice nada útil, y se pierden diez minutos.

---

### Modo `up` — levantar y dejar listo

1. **Levantar** según el entorno (`ddev start`, `npx wp-env start`, `docker compose up -d`, o abrir el
   sitio en LocalWP).
2. **Comprobar que responde de verdad**, no que el comando terminó:
   ```bash
   {wp} core version
   {wp} db check
   {wp} option get home
   curl -s -o /dev/null -w "%{http_code}" {site_url_local}
   ```
3. **Poner el sitio en modo desarrollo** — esto es lo que distingue un entorno listo de uno que va a
   dar sustos:
   - `WP_DEBUG`, `WP_DEBUG_LOG`, `SCRIPT_DEBUG` en `true`; `WP_DEBUG_DISPLAY` en `false`.
   - **Query Monitor** activo (si no está, se propone instalarlo: es lo que más tiempo ahorra en WP).
   - **Cachés y CDN desactivados.** Un plugin de caché en local produce el clásico "no se aplica el
     cambio" y hace perder una tarde.
   - **Correos, pagos y sincronizaciones apagados**, si el sitio vino de producción.
   - `blog_public = 0`.
4. **Reportar el estado** en cuatro líneas: URL, versiones de WP/PHP, tema activo, y qué se desactivó.

---

### Modo `doctor` — diagnosticar

**Primero se lee el error, después se toca.** Casi todos los fallos de WP dejan rastro; probar cambios
a ciegas es lo que convierte un problema de diez minutos en uno de dos horas.

```bash
tail -n 100 wp-content/debug.log
{wp} db check
{wp} plugin list --status=active
{wp} theme list --status=active --fields=name,parent
{wp} core verify-checksums
```

Los fallos típicos y su causa real están en `references/troubleshooting.md`. En corto:

| Síntoma | Dónde mirar primero |
|---|---|
| Pantalla blanca | `debug.log` — es un fatal de PHP, casi siempre un plugin o un typo propio |
| "No se aplica mi CSS" | La versión del enqueue (`filemtime`), caché, o el handle del padre mal puesto |
| Permalinks 404 | `wp rewrite flush`, y la config del servidor |
| Error de conexión a la DB | Credenciales de `wp-config.php` vs las del entorno; el contenedor caído |
| El cambio se ve en el front pero no en el editor | Los estilos del bloque no están encolados para el editor |
| Cambios que desaparecen | Se está editando un archivo que WordPress no carga: comprobar la plantilla real |

**Regla:** se identifica la causa y se dice cuál es, antes de proponer el arreglo. Un "prueba a
desactivar los plugins" sin haber leído el log es adivinar.

---

### Modo `wp {comando}` — ejecutar tareas

Ejecuta lo que se pida con el prefijo correcto. Dos guardas que no se saltan:

- **Todo lo que escribe se confirma antes**, diciendo qué va a cambiar y cuántos registros afecta.
  Los destructivos (`db reset`, `db import`, `post delete`, `search-replace` sin `--dry-run`,
  `plugin delete`) **exigen backup previo** y confirmación explícita.
- Lo que solo lee (`list`, `get`, `db search`, `--dry-run`) corre sin ceremonia.

Las tareas frecuentes están en `references/wp-cli.md`.

---

### Modo `reset` — volver a empezar

Reinstalar el sitio local desde cero. **Destruye la base de datos local.** Solo con confirmación
explícita y tras un `wp db export` de respaldo, aunque el dev diga que no hace falta:

```bash
{wp} db export "backups/pre-reset-$(date +%Y%m%d-%H%M).sql"
{wp} db reset --yes
```

Y después se repuebla — con `/eden:wp-import`, no a mano.

---

### Verificar un cambio en local

Cuando el dev quiere ver si algo funciona, el ciclo corto:

1. `tail -f wp-content/debug.log` en marcha.
2. Recarga forzada (el navegador cachea; el `filemtime()` del enqueue existe justo para esto).
3. Query Monitor: sin notices, sin queries duplicadas, y **la plantilla que se está usando es la que
   se cree**.
4. Si el cambio es visual, la medición 1:1 la hace `/eden:attention-detail` o `/eden:test-visual` — este skill no
   opina de píxeles.

---

### Reporte

```
🖥️ WP LOCAL — {modo}

Entorno   {local_env} · WP {x} · PHP {y} · {url}
Tema      {child} (padre {parent}) · Sabor {flavor}

Hecho
  {qué se ejecutó}

Estado del sitio
  Debug {on/off} · Query Monitor {sí/no} · Caché {desactivada/activa}
  Desactivado: {correos, pagos, cdn…}

⚠️ Hallazgos
  {lo que apareció en el log y qué significa}

❓ Sin resolver
  {qué y por qué}
```
