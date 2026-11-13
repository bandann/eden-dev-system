---
name: wp-import
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:wp-import` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable de
  clonar, migrar o subir un sitio, ni porque aparezca un `.sql` o un `.wpress`: si no lo pidió por su
  nombre, no se usa. —
  Qué hace cuando SÍ se invoca: mueve un sitio de WordPress de un entorno a otro, entero y sin romperlo.
  Cubre las cuatro formas: bajar un sitio de producción a local, importar contenido demo o un WXR,
  migrar desde otra plataforma (Shopify, Wix, otro WP), y el camino de vuelta a staging. Verifica antes
  de tocar, hace backup antes de escribir, usa `wp search-replace` con serialización correcta, y
  comprueba el resultado en vez de darlo por bueno.
argument-hint: "[from-prod | content | migrate | to-staging] [| origen y destino]"
disable-model-invocation: true
---

## WP Import — mover un sitio sin romperlo

Argumento recibido: `$ARGUMENTS`

Importar un WordPress no es copiar archivos: la base de datos guarda **URLs absolutas dentro de datos
serializados**, y un `find & replace` de toda la vida las corrompe en silencio. Este skill existe para
que eso no pase, y para que cada paso quede verificado en vez de supuesto.

> **Idioma:** al dev, en español. Lo que quede escrito —scripts, docs, notas— en inglés.

**Lo que NO hace:** commitear, pushear, **ni escribir en producción** (salvo el modo `to-staging`, y
solo tras autorización explícita del dev en el momento). Tampoco decide a dónde va algo: eso se
confirma siempre.

**Modelos:** el trabajo pesado —dumps, search-replace, verificación— se delega a **`eden:wp-migrator`**.
La sesión principal decide, pregunta y verifica.

---

### Las cuatro rutas

| Modo | Qué hace | Referencia |
|---|---|---|
| **`from-prod`** | Baja un sitio en producción (archivos + DB) a local | `references/from-production.md` |
| **`content`** | Importa contenido demo de un tema, o un WXR (`.xml`) | `references/content-import.md` |
| **`migrate`** | Trae contenido desde Shopify, Wix, Squarespace u otro WP | `references/from-other-platform.md` |
| **`to-staging`** | El camino de vuelta: local → staging (y de ahí a producción) | `references/to-staging.md` |

Si el argumento no dice cuál, **se pregunta**. Son operaciones muy distintas y la equivocada destruye
datos.

> **Figma → WordPress no es una importación.** Convertir un diseño en bloques, patterns o plantillas es
> construir: se hace con `/eden:create-new-section` (que rutea al sabor de WP del proyecto) o con
> `/eden:download-figma-img` para los assets. Si el dev pide "importar el Figma", se le redirige ahí.

---

### Paso 0 — Antes de tocar nada

1. **`/eden:wp-setup` tiene que haber corrido.** Sin `wordpress.flavor`, `local_env` y las tres URLs en
   `project-config.json`, este skill no tiene con qué trabajar. Si falta, se dice y se ofrece correrlo.
2. **Confirmar origen y destino en voz alta**, con las URLs concretas:
   ```
   ⚠️ CONFIRMA ANTES DE SEGUIR
      Origen:  {url/archivo}  ({qué es})
      Destino: {url/entorno}  ({qué hay ahí ahora})
      Esto va a: {sobrescribir la DB local | añadir contenido | escribir en staging}
      ¿Procedo?
   ```
   **Un import escribe encima.** Nunca se ejecuta sin que el dev confirme esa frase.
3. **Backup de lo que se va a sobrescribir**, siempre, aunque "esté vacío":
   ```bash
   wp db export "backups/pre-import-$(date +%Y%m%d-%H%M).sql"
   ```
   Si el destino no tiene nada que respaldar, se dice — pero se comprueba, no se supone.

---

### Paso 1 — Inventariar el origen

Delega a **`eden:wp-migrator`**. Antes de mover, saber **qué** se mueve: tamaño de la DB, tamaño de
`uploads/`, versiones de PHP/WP/MySQL en origen y destino, plugins activos, si es multisite, si hay
WooCommerce (pedidos = datos personales), y si el tema o algún plugin es de pago con licencia atada al
dominio.

Tres cosas que si se descubren a mitad cuestan el doble:

- **`uploads/` enorme** (varios GB). Se decide antes: ¿se baja entero, o se usa un proxy de imágenes
  hacia producción para trabajar en local?
- **Multisite.** Es otra operación: tablas por sitio, `wp site list`, y el search-replace va con
  `--network --url=`.
- **Datos personales reales** (pedidos, clientes, usuarios). Ver el bloque de datos sensibles abajo.

---

### Paso 2 — Ejecutar la ruta

Cada modo tiene su procedimiento en su referencia. Lo que es **común a todos** y no se salta nunca:

**El search-replace se hace con WP-CLI, y solo con WP-CLI:**

```bash
wp search-replace 'https://origen.com' 'https://destino.local' --all-tables-with-prefix --precise --recurse-objects --report-changed-only --dry-run
# revisar el reporte, y solo entonces repetir SIN --dry-run
```

- **`--dry-run` primero, siempre.** El reporte dice cuántos reemplazos en qué tablas: si el número es
  absurdo (0, o el triple de lo esperado), hay algo mal y se para.
- `--precise --recurse-objects` es lo que respeta la **serialización**. Sin eso, los datos serializados
  quedan con longitudes incorrectas y los widgets, los campos ACF y los diseños del builder
  desaparecen sin ningún error visible.
- **Cuatro variantes de la URL**, no una: `https://x.com`, `http://x.com`, `//x.com` y `x.com`. Se
  ejecuta el reemplazo para cada una que exista.
- **Nunca `sed` sobre el `.sql`, nunca el buscar/reemplazar de un plugin, nunca un editor de texto.**
  Es exactamente así como se corrompe un sitio en silencio.

---

### Paso 3 — Verificar (esto no es opcional)

Un import "que terminó sin errores" no está bien hasta que se comprueba. Lista mínima:

```bash
wp option get home && wp option get siteurl     # ¿apuntan al destino?
wp db search "{dominio-origen}" --stats         # ¿quedó algo del dominio viejo?
wp post list --post_type=any --format=count     # ¿el número cuadra con el origen?
wp plugin list --status=active
wp rewrite flush                                 # los permalinks casi siempre hay que refrescarlos
```

Y en el navegador, con `WP_DEBUG_LOG` encendido:

- La home, una entrada, una página y —si hay Woo— una ficha de producto.
- **El admin**: que se pueda entrar y que el editor cargue.
- **Que las imágenes se vean.** Si no, es `uploads/` o el search-replace.
- **Que los campos ACF y los diseños del builder sigan ahí.** Si desaparecieron, la serialización se
  rompió: se restaura el backup y se repite bien. No se "arregla a mano".
- Sin PHP notices nuevos en `debug.log`.

---

### Paso 4 — Dejar el entorno en condiciones de trabajo

Un sitio recién bajado **no está listo**: está apuntando al mundo real. Antes de tocarlo:

- Desactivar lo que puede **mandar correos o cobrar de verdad**: SMTP, pasarelas de pago en modo live,
  automatizaciones, sincronizaciones con CRM. Ver `references/from-production.md`.
- Desactivar plugins de **caché y CDN** en local (dan falsos "no se aplicó el cambio").
- Activar `WP_DEBUG`, `WP_DEBUG_LOG`, `SCRIPT_DEBUG` y Query Monitor.
- **Bloquear la indexación** si el destino es una staging pública (`blog_public = 0` + auth básica).
  Una staging indexada es un problema de SEO real para el cliente.
- Un usuario administrador local propio, sin tocar los del cliente.

---

### Datos sensibles — la línea que no se cruza

Un dump de producción trae **datos personales reales**: clientes, direcciones, pedidos, contraseñas
hasheadas. Eso obliga a tres cosas:

- **Nunca al repo.** `*.sql` y `*.wpress` están en el `.gitignore` por esto.
- **Nunca a un servicio externo** para "convertirlo" o compartirlo.
- Si el trabajo no necesita los datos reales —y casi nunca los necesita—, se **propone anonimizar**
  tras el import (`wp user update`, limpiar pedidos, vaciar logs). Se propone; lo decide el dev.
- El backup local se borra cuando el trabajo termina. Se anota en el cierre.

---

### Reporte

```
📦 WP IMPORT — {modo}

Origen   {qué}  →  Destino  {qué}
Backup   {ruta del dump previo}

Movido
  DB        {n} tablas · {tamaño}
  Uploads   {tamaño} · {completo | parcial | proxy}
  Código    {qué}

Search-replace
  {origen} → {destino} · {n} reemplazos en {n} tablas

Verificado
  ✅ {lo que se comprobó, una línea cada uno}
  ❌ {lo que falló y qué se hizo}

⚠️ Desactivado en este entorno
  {SMTP, pagos, caché, indexación…}

⚠️ Pendiente / riesgos
  {licencias atadas al dominio, uploads sin bajar, datos reales sin anonimizar}
```

Al terminar, propón guardar en memoria lo que costó descubrir: el tamaño real del sitio, qué plugin dio
guerra, qué licencia está atada al dominio. La próxima migración de este cliente empieza sabiéndolo.
