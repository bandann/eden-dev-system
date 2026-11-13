# Referencia — Checklist de auditoría de cierre

Se corre sobre **todo el diff de la rama** (`git diff <base>...HEAD`), no sobre el último commit. Cada
punto se responde con evidencia: archivo, línea, salida de comando o captura. "Se ve bien" no es una
respuesta.

> **Si el proyecto tiene perfil activo**, su checklist de QA manda sobre el orden de abajo — trae los
> anchos, umbrales y prioridades reales de esa operación. Si declara `qa.bug_frequency`,
> la revisión se ordena por **frecuencia real de bugs**: lo que más encuentra QA se revisa primero.

## 1. Funcional

- [ ] Hace lo que el ticket pide, requerimiento por requerimiento.
- [ ] Casos borde: sin datos, un solo ítem, muchos ítems, textos larguísimos, imágenes faltantes.
- [ ] Estados: carga, vacío, error, deshabilitado.
- [ ] Nada quedó a medias detrás de un flag o un comentario.

## 2. Regresiones y blast radius

- [ ] Se listaron **todos** los consumidores de lo que se tocó:
      ```bash
      grep -rn "{snippet-o-funcion}" --include="*.liquid" --include="*.js" --include="*.css" .
      ```
- [ ] Ningún componente compartido cambió de comportamiento para quien ya lo usaba.
- [ ] Toda opción/setting nueva tiene **default que reproduce el comportamiento actual** — las
      instancias existentes se ven exactamente igual que antes del cambio.
- [ ] Los estilos no se escapan: selectores acotados al bloque, nada global sin que el ticket lo pida.
- [ ] Nada se rompió en las otras páginas que usan lo tocado (se verificó, no se supuso).

## 3. Reglas del equipo

- [ ] **CSS**: BEM, mobile-first, sin `!important`, sin IDs, sin selectores de etiqueta, sin estilos
      inline, sin anidar más de 3 niveles, colores y tipografía por tokens.
- [ ] **Markup/plantillas**: semántica correcta, jerarquía de headings sin saltos, textos por sistema de
      traducciones (nunca hardcodeados), contenido de usuario escapado.
- [ ] **JS**: sin jQuery, sin `var`, sin handlers inline, sin Shadow DOM, listeners limpiados al
      desmontar, `defer`/`type="module"`.
- [ ] **Performance**: imágenes con dimensiones, `loading="lazy"` bajo el fold, `srcset`, scripts
      diferidos, sin trabajo pesado en el render.
- [ ] **Accesibilidad (WCAG AA)**: contraste, foco visible, todo operable por teclado, labels en
      inputs, alt descriptivo, `prefers-reduced-motion` respetado.
- [ ] **SEO**: headings correctos, texto real (no texto en imagen), links rastreables `<a href>`, datos
      estructurados intactos.

## 4. Limpieza

- [ ] Sin `console.log`, `console.warn` de debug, ni `debugger`.
- [ ] Sin código comentado, muerto o "por si acaso".
- [ ] Sin archivos de playground, pruebas sueltas, `.bak`, capturas temporales.
- [ ] Sin secretos, `.env`, credenciales ni tokens en el diff.
- [ ] Sin dependencias agregadas que nadie pidió.

## 5. Validación automática del stack

- [ ] **Shopify**: Theme Check sobre lo tocado — errores en cero; warnings explicados al dev en
      español.
- [ ] **WordPress**: `php -l` sobre cada PHP tocado + PHPCS con el estándar `WordPress` sobre nuestras
      rutas (nunca sobre el core ni sobre plugins de terceros); `wp-scripts lint-js` si hay bloques.
      Errores en cero. Y las cuatro comprobaciones que solo existen en WP:
      · salida escapada, entrada sanitizada, **nonce Y capability** en toda acción, `permission_callback`
        real en cada ruta REST;
      · nada de CPTs, campos ni lógica registrados desde el tema (van al mu-plugin: sobreviven al tema);
      · `wp db search` sobre lo renombrado — un bloque, shortcode o clase que ya está en contenido
        publicado **rompe páginas que nadie va a revisar**;
      · `core verify-checksums` / `plugin verify-checksums` si se sospecha del sitio heredado.
- [ ] **Otros stacks**: linter, type-check y tests del proyecto. Si fallan, se reporta la salida real,
      no un resumen optimista.

## 6. Navegador

- [ ] Cero errores en consola en cada página tocada.
- [ ] Sin requests fallidos (404 de assets, imágenes rotas).
- [ ] Sin saltos de layout al cargar (CLS).

## 7. Diseño (si aplica)

- [ ] Mobile 1:1 con Figma — medido, no estimado.
- [ ] Desktop 1:1 con Figma.
- [ ] Tablet, si el diseño lo especifica.
- [ ] Transición entre breakpoints correcta (nada se rompe entre medias).
- [ ] Estados visuales conformes al diseño.

## 8. Documentación

- [ ] Componente/sección nueva con schema o lógica no obvia → doc en `docs/`.
- [ ] `CLAUDE.md` del proyecto actualizado si cambiaron convenciones o arquitectura.

## 9. Seguridad (puerta bloqueante)

Las 12 áreas, la severidad y las herramientas están en `rules/eden-security-rules.md`; aquí no se
copian.

- [ ] `security-auditor` corrió sobre el diff y contrastó la **superficie** declarada en el plan.
- [ ] Cero hallazgos **Críticos o Altos** (o excepción explícita del dev, escrita en el PR).
- [ ] Medios y Bajos listados en el PR. Herramientas que faltaron, declaradas.
- [ ] El commit pasó el hook de secretos (`eden_guard.py`).

## 10. Anti-slop (puerta bloqueante en lo funcional)

Las comprobaciones F-1 a F-10 y su severidad están en `rules/on-demand/eden-antislop-rules.md`; aquí no
se copian.

- [ ] Corrieron sobre el diff (`reviewer` / `design-auditor`) si la tarea toca UI o textos al usuario.
- [ ] Cero F bloqueantes (o excepción explícita del dev, escrita en el PR en `Anti-slop exceptions`).
- [ ] Choques Figma vs capa funcional presentados al dev. Capa estética solo reportada.

---

## Cómo se reporta

Cada hallazgo con: **qué**, **dónde** (`archivo:línea`), **por qué importa**, **cómo se arregla**.
Ordenados por severidad. Si no hay hallazgos, se dice claramente que no los hay — pero solo después de
haber corrido el checklist de verdad.
