# Sabor: Express

APIs y servidores con Express. Este sabor asume **Express 5**; un proyecto en Express 4 sigue en 4 (y su
migración es una tarea propia). Las diferencias importan, porque Express 5 cambió el enrutado y el
manejo de errores.

## Estructura habitual

```
src/
├── app.ts            crea y configura la app (exportada, sin listen: la usan los tests)
├── server.ts         listen + apagado limpio
├── config.ts         config validada al arrancar
├── routes/ · routers/   un router por recurso, montado en app.ts
├── controllers/ · handlers/
├── middleware/       auth, validación, errores, rate limit
├── services/ · repositories/
└── schemas/          esquemas de validación (Zod)
test/
```

## Express 5 — lo que cambió

- **Errores asíncronos:** una promesa rechazada en un handler o middleware llega sola al middleware de
  errores; no hace falta `try/catch` ni `.catch(next)` en código nuevo.
- **Rutas:** el comodín se nombra (`/*splat`; `/{*splat}` también incluye la raíz), lo opcional va entre
  llaves (`/:file{.:ext}`) y ya no hay expresiones regulares en la cadena de ruta (se usan arrays).
- `req.body` es `undefined` si no se parseó; `express.urlencoded` tiene `extended: false` por defecto; el
  parser de query es el simple; `req.params` no tiene prototipo.
- Eliminados: `app.del`, `req.param()`, `res.json(obj, status)`, `res.send(status)`, `res.sendfile`,
  `redirect('back')`. `res.status()` solo acepta 100–999.

## Cómo se arma una app segura

En `app.ts`, en este orden y una sola vez:

1. `app.disable('x-powered-by')` y **Helmet** (cabeceras de seguridad).
2. `app.set('trust proxy', …)` **solo** si hay un proxy delante y con el número de saltos real (si no,
   la IP del cliente —y el rate limit— se pueden falsear).
3. **CORS** con lista blanca de orígenes; nunca `*` con credenciales.
4. Parsers con **límite de tamaño** (`express.json({ limit })`).
5. **Rate limit** en login, registro y lo caro.
6. Routers por recurso, cada uno con su middleware de **validación** y de **auth**.
7. 404 y, al final, el **middleware de errores** (cuatro argumentos) con formato único y sin pila.

Cookies de sesión: nombre propio, `HttpOnly`, `Secure`, `SameSite`, y un almacén real (no el de memoria).

## Rutas

- Un router por recurso; el handler valida (middleware con el esquema), autoriza por recurso, delega en
  un servicio y responde con un DTO.
- Redirecciones solo a rutas propias o a una lista blanca (open redirect).
- Archivos estáticos con `express.static` y `dotfiles: 'ignore'` (el default en 5).

## Avisos recientes

`res.redirect` tuvo un XSS (CVE-2024-43796, corregido en 4.20.0) y `path-to-regexp` varios ReDoS
corregidos en 4.20.0 y 4.21.2. Un proyecto en Express 4 por debajo de esas versiones se reporta.

## Validación propia de este sabor

```bash
{pm} run lint && {pm} run typecheck && {pm} test && {pm} run build && {pm} audit
```

Y con la app corriendo en local: las rutas nuevas responden con sus códigos, y un error forzado devuelve
el formato único sin pila.
