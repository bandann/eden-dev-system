# Sabor: Headless — WordPress como backend

WordPress solo administra y expone contenido; el front lo sirve otro framework (Next, Astro, Nuxt…).
**Son dos proyectos con dos conjuntos de reglas**, y confundirlos es el error típico de este sabor.

| Lado | Reglas que aplican |
|---|---|
| **WP (backend)** | `../eden-wordpress-rules.md` — seguridad, hooks, CPTs, i18n, performance, dónde va el código |
| **Front (JS)** | El núcleo del kit + las convenciones del framework del proyecto. **No** las reglas de temas de WP: aquí no hay `theme.json`, ni template hierarchy, ni enqueues |

En `project-config.json`, `project.stack` declara el principal y `project.stacks[]` el otro con su
ruta. **Cada tarea declara en qué lado trabaja antes de planear**: el blast radius de uno no dice nada
del otro.

## Del lado de WordPress

- El tema del admin es mínimo. **No se invierte en la presentación del tema**; si acaso, en que el
  editor muestre previews útiles.
- Todo lo que el front necesite tiene que estar **expuesto a propósito**:
  - `show_in_rest => true` al registrar CPTs, taxonomías y metadatos. Un campo que no está en REST no
    existe para el front.
  - ACF: `show_in_graphql` / exposición REST según el proyecto (ACF to REST API, WPGraphQL for ACF).
- Endpoints propios con `register_rest_route`, en el mu-plugin del sitio:
  - `permission_callback` **siempre** — nunca `__return_true` en algo que escribe.
  - `args` con `sanitize_callback` y `validate_callback` declarados.
  - Respuesta con forma estable y versionada en el namespace (`{prefix}/v1`). Cambiar la forma de una
    respuesta rompe el front en producción: es un breaking change y se trata como tal.
- **Previews y borradores** son el problema clásico del headless: se resuelven a propósito (token de
  preview + ruta de preview en el front), no se dejan para el final.
- La caché: si hay CDN o ISR delante, **publicar en WP tiene que invalidarla**. Un hook en
  `save_post` / `transition_post_status` que dispara el revalidate. Sin eso, el cliente publica y "no
  se ve", y acaba siendo un ticket.
- Las URLs de las imágenes vienen del dominio de WP: hay que decidir y declarar si el front las sirve
  desde ahí, las proxya o las descarga.

## Del lado del front

- Manda el framework: su router, su sistema de estilos, su forma de componer. Las reglas de núcleo
  (BEM o lo que use el proyecto, tokens, mobile-first, accesibilidad, tests) aplican igual.
- Los datos que llegan de WP son **contenido de usuario**: el HTML del `content.rendered` se sanea antes
  de inyectarlo. `dangerouslySetInnerHTML` sin sanear es un XSS servido por nosotros.
- **Seguridad del front** (núcleo en `../../eden-security-rules.md`):
  - **Secretos solo en el servidor.** Variables de entorno **sin** prefijo público (`NEXT_PUBLIC_`,
    `PUBLIC_`, `VITE_`, `NUXT_PUBLIC_`): lo que lleva ese prefijo va al bundle. El token de preview y
    las credenciales de la API de WP nunca llegan al navegador: Crítica.
  - **CORS con allowlist estricta** en WP (`rest_allowed_cors_headers`, `rest_pre_serve_request`): el
    dominio del front y nada de `*` con credenciales. Alta si es abierto en una ruta autenticada.
  - **Sanear `content.rendered`** con DOMPurify (o equivalente) antes de `dangerouslySetInnerHTML`,
    `v-html` o `set:html`. Sin sanear: Alta.
  - **Cabeceras de seguridad y CSP** en la configuración del framework (`headers()` en Next,
    middleware en Astro/Nuxt): CSP, `frame-ancestors`, `Referrer-Policy`. Ausentes: Baja.
  - La ruta de preview valida el token en el servidor y no lo guarda en `localStorage` ni en la URL
    visible.
- La forma de la respuesta de WP se tipa en el front (TypeScript o el esquema que use el proyecto). Sin
  tipos, un cambio en el backend se descubre en producción.
- Los estados que WP puede devolver **existen y están diseñados**: vacío, error, contenido sin imagen,
  campo opcional ausente.

## Escalera reuse-first

Se aplica igual, en cada lado por separado:

- **En WP**: ¿lo resuelve el REST del core con los parámetros que ya tiene (`_fields`, `_embed`,
  filtros por taxonomía)? → ¿un `register_meta` con `show_in_rest`? → ¿un filtro sobre la respuesta
  existente? → **último recurso**, un endpoint propio.
- **En el front**: componente existente → variante configurada → componente nuevo.

Un endpoint propio para algo que `_fields` ya resolvía es código que alguien tendrá que mantener sin
motivo.

## Fidelidad al Figma

Se mide en el **front**, con el render real, igual que en cualquier otro proyecto del kit
(`/eden:attention-detail`, `/eden:test-visual`). WordPress no participa: lo que se ve es del framework.

## Validación

Las dos puertas, cada una en su lado:

```bash
# WP
composer exec phpcs -- --standard=WordPress {rutas}
php -l {archivo}

# Front
{el linter, type-check y tests del framework del proyecto}
```

Y una comprobación que solo existe en headless: **el contrato entre los dos**. Si se tocó la forma de
una respuesta, se verifica el front contra el WP real antes de cerrar — no contra un mock.
