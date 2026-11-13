# Anti-slop — Eden (que nada parezca hecho por una IA en piloto automático)

Adaptación al flujo Eden de **anti-slop v3.2.21** (github.com/miqdadbadjuber/anti-slop, MIT, ©
Miqdad Badjuber). El reglamento original completo está en
`skills/antislop/references/upstream/` como **material de consulta**; esta regla decide **cuándo** aplica,
**qué bloquea** y **qué se ignora** del original.

**Esta regla es bajo demanda.** No se carga en cada sesión ni se sincroniza a `~/.claude/rules`: la leen
`ignition-task`, `create-new-section`, `section-mod`, `figma-expert`, `turnoff-task` y `/eden:antislop`
cuando la tarea toca UI, textos o comentarios. Nada de esto se activa solo.

"Slop" es lo que sale cuando el agente **decide por defecto**: el degradado azul-violeta, la *bento grid*,
el "Get Started", la cifra inventada, el botón que no hace nada, el testimonio de "Sarah, CEO".

---

## Dos capas, dos reglas de activación

| Capa | Qué cubre | Cuándo aplica |
|---|---|---|
| **Funcional** | Nada inventado, nada muerto, estados, teclado, contraste, móvil usable, tema(s) funcionando, probar antes de entregar | **Siempre**, en toda tarea que toque UI o textos que llegan al usuario final. Es calidad, no estilo |
| **Estética y voz** | Decisiones visuales por defecto (degradados, iconos, layouts de plantilla, glass, glow…), voz de los textos (CTAs genéricos, palabras vacías, em dash) y comentarios de código con olor a IA | **Solo sin diseño definido**, y **solo con el sí del dev** (o su excepción explícita en `antislop.mode`) |

### Figma manda — siempre

Si hay diseño, se implementa el diseño. Un degradado, una *bento grid*, una flecha "→" o un "Learn more"
que están en el Figma **no son slop**: son decisiones del diseñador. La capa estética **nunca** se aplica
sobre lo que el diseño define.

### Detectar la fuente de diseño

Antes de construir o modificar UI, el flujo busca una **fuente de diseño de la tarea**:

1. URL o nodo de Figma (argumento, ticket, `project-config.json → figma`, `docs/sitemap.md`).
2. Captura o imagen del diseño (adjunto del ticket, imagen pegada en la conversación, archivo en el repo
   referido por la tarea).
3. Un documento de dirección de diseño de la tarea (`DESIGN.md` o equivalente que el dev señale).

Los **fundamentos** (tokens, `docs/design-system.md`) **no** son por sí solos una fuente de diseño de la
sección: dicen con qué colores pintar, no cómo es la sección.

**Si no hay ninguna**, el flujo **pregunta** antes de diseñar nada:

```
🧹 No encuentro diseño para esta tarea (Figma, captura ni imagen).
   ¿Aplico anti-slop para las decisiones visuales y de texto que tenga que tomar yo?
   · Sí — evito los defaults de IA y cada decisión lleva su porqué
   · No — sigo los patrones del proyecto sin esa capa
   · Tengo diseño — te paso el Figma o una captura
```

Y respeta la respuesta. La capa funcional se aplica igual en los tres casos.

### Excepciones explícitas del dev

`antislop.mode` en `.claude/project-config.json` (o, como default de todos tus proyectos, en
`~/.claude/eden-config.json`). Precedencia normal del kit: el dev en el momento > proyecto > global.

| Valor | Sin fuente de diseño |
|---|---|
| `ask` (default) | Se pregunta, como arriba |
| `on` | Se aplica la capa estética sin preguntar (excepción dada por el dev) |
| `off` | No se aplica la capa estética ni se pregunta |

Ningún valor desactiva la capa funcional.

---

## Capa funcional — siempre, y bloquea

Se verifica en el cierre (`turnoff-task`) junto a la puerta de seguridad. **Lo marcado como Bloquea
impide commit, push y PR** hasta arreglarlo o hasta que el dev conceda una excepción explícita, escrita en
el PR (sección **Anti-slop exceptions**).

| # | Comprobación | Origen | Severidad |
|---|---|---|---|
| F-1 | **Nada inventado**: ninguna cifra, estadística, delta, testimonio, nombre, avatar, logo de cliente, certificación ("SOC 2", "ISO 27001"), dato de rendimiento ("300% faster") ni característica que no venga de una fuente real. Sin dato real → no se muestra, o marcador honesto `[REAL DATA]`, `[LOGO]`, iniciales | R-17, R-18, R-23, R-36, R-38, UI-16/36/37/40, CP-18/19 | **Bloquea** |
| F-2 | **Nada muerto**: todo enlace, botón, menú, pestaña, modal, toggle y formulario hace algo real (destino que existe, `Escape` cierra, el formulario da respuesta). Lo no construido se omite o lleva "Coming soon" visible. Sin enlaces de navegación a páginas inexistentes | R-24, R-26, UI-32/33 | **Bloquea** |
| F-3 | **Estados**: toda vista con datos tiene vacío (por qué está vacío + una acción), carga (qué carga) y error (qué falló + siguiente paso) | R-27, UI-41, HU-10 | **Bloquea** |
| F-4 | **Teclado**: orden de Tab lógico, Enter/Espacio activan, Escape cierra diálogos, nada solo-ratón (hover/drag sin alternativa), foco visible con 3:1; nunca `outline: none` sin reemplazo `:focus-visible` | R-32, HU-05..08 | **Bloquea** |
| F-5 | **Contraste WCAG AA medido, no estimado**: 4.5:1 texto normal, 3:1 texto grande (**24 px, o 18,66 px en negrita** — umbral WCAG; el original dice 18 px+) y componentes. Texto sobre foto o degradado: se mide el peor punto, con velo o bloque si hace falta. Herramienta: `${CLAUDE_PLUGIN_ROOT}/scripts/contrast_check.py` | R-25, HU-01..03 | **Bloquea** |
| F-6 | **Móvil usable**: sin scroll horizontal, texto dentro de su contenedor, sin solapes, áreas táctiles de 44×44 px, navegación móvil funcional | R-03, LM-* | **Bloquea** el scroll horizontal, el solape y el área táctil; el resto se reporta |
| F-7 | **Temas**: si el proyecto ya tiene modo claro y oscuro, todo funciona en ambos (contraste, foco, componentes). **No** se exige crear un modo oscuro que el diseño no tiene | R-34 (R-21 descartado) | **Bloquea** si hay temas |
| F-8 | **Construido en el código fuente**: ninguna funcionalidad implementada por un script que reescribe CSS o plantillas con reemplazos de texto | R-33 | **Bloquea** |
| F-9 | **Probado antes de entregar**: se ejecuta, se mira la consola y se hace clic en cada elemento interactivo en cada breakpoint (y tema). Lo que no se probó se declara | R-35, C-5 | Lo cubren `test-visual` / `design-auditor`; si no se hizo, se declara y se reporta |
| F-10 | **Textos de relleno honestos**: nada de "John Doe", `johndoe@example.com` ni lorem ipsum disfrazado; placeholder de campo útil (`Your name`, `email@example.com`) | UI-40, R-38 | **Bloquea** en lo publicable |

**Si el Figma choca con la capa funcional** (testimonios o cifras de ejemplo en el diseño, un color que
no pasa contraste, un menú que apunta a páginas que no existen), **no se resuelve en silencio en ningún
sentido**: se implementa con marcador honesto o se mantiene como está, y **se le dice al dev** para que lo
hable con el diseñador o con el cliente. Es un hallazgo, no una decisión del agente.

---

## Capa estética y de voz — sin diseño definido, con el sí del dev

Si no hay diseño, antes de esta capa se **ofrece** UI/UX Pro Max (`skills/uiux-pro/SKILL.md`, siempre con
el sí del dev). Si el dev aceptó su propuesta, esta capa se aplica **sobre** ella: lo que UI/UX Pro Max
sugiera y esté en la lista de abajo se evita igual, salvo que el dev lo elija con un motivo escrito.

Cuando aplica, cada decisión visual o de texto que el agente tome **lleva una línea de por qué** (R-31).
Un default sin razón es slop aunque quede bonito.

**Por defecto se evita (permitido con una razón escrita):**

- **Color**: degradados azul-violeta, neón, orbes radiales y *glow*; paleta de más de 2–3 colores + 1
  acento. Siempre con los tokens del proyecto.
- **Iconos**: ✨ sparkles, estrellas, varitas, rayos, diamantes, orbes, robots; un set "estilo Lucide"
  por defecto. Ningún emoji como icono.
- **Layouts de plantilla**: hero + 3 o 6 tarjetas, *bento grid*, terminal falsa, "How it works" de 3 pasos
  con iconos redondos, pricing de 3 columnas con la del medio resaltada, barra "Trusted by" bajo el hero,
  footer uniforme de 4 columnas, ilustraciones Undraw/Storyset. FAQ de plantilla.
- **Efectos**: *glassmorphism* y *glow* en más de 1–2 elementos, cuadrícula o puntos de fondo, sombras y
  radios uniformes en todo, animación decorativa (y siempre con `prefers-reduced-motion`).
- **Tipografía**: monoespaciada grande para "parecer terminal", etiquetas en mayúsculas con mucho
  *tracking* por defecto.
- **Clonar** la estética de Linear, Vercel, Stripe o Notion.

**Voz de los textos que escribe el agente** (no los que vienen del ticket, del cliente o del Figma):

- Sin **em dash (—)** en textos que llegan al usuario final: punto, coma, dos puntos o paréntesis.
- Sin CTAs genéricos (`Get Started`, `Learn More`, `Try Now`, `Explore`, `Discover`): el botón dice qué
  pasa al pulsarlo.
- Sin palabras vacías (`AI Powered`, `Revolutionary`, `Next Generation`, `Seamless`, `Cutting Edge`,
  `Intelligent`, `Ultimate`, `Powerful`, `Effortless`) ni insignias vacías (`New`, `Beta`, `Secure`,
  `Fast`) sin un hecho detrás.
- Frases concretas sobre el producto real; si no se conoce el dato, se pregunta o se deja marcador.

**Comentarios de código** (`/eden:antislop code`): fuera los comentarios que narran lo obvio, los
banners decorativos y las disculpas de IA; **solo se tocan comentarios**, nunca código, nombres, imports
ni formato.

Esta capa **se reporta** (en el PR, sección **Anti-slop**); no bloquea.

---

## Qué se descarta del original

- La instrucción de **cargarse siempre**, el **asistente de instalación**, la escritura de bloques en
  `CLAUDE.md`/`AGENTS.md`, la pregunta de **modo en cada sesión** y el archivo
  `~/.config/antislop/settings.json`. En Eden: bajo demanda y `antislop.mode`.
- Las auditorías escritas en `anti-slop/audit-*.md` dentro del proyecto. En Eden: el reporte va a la
  consola y al PR.
- Su "Delivery Gate no delegable": en Eden la verificación es independiente (roles `reviewer`,
  `design-auditor`, `security-auditor`), y el autor no se aprueba a sí mismo.
- El servidor MCP de contraste: se usa su verificador como script bajo demanda.
- R-21 (construir siempre un interruptor claro/oscuro).

## Cómo encaja con el resto

- `eden-design-rules.md` y "Figma manda" están **por encima** de esta regla.
- La capa funcional **refuerza** `eden-quality-rules.md` (accesibilidad, estados) y se audita en el mismo
  momento que `eden-security-rules.md`.
- El idioma no cambia: textos del producto y del PR en inglés; al dev, en español.
