# Referencia — Cierre: PR y comentario en el tracker

Lo que dejas escrito al cerrar es lo único que el reviewer y el PM van a leer. Si tienen que
preguntarte algo para entender el cambio, el cierre está incompleto.

## 1. Pull Request

**Título** — formato de commit, en inglés:

```
feat(header): add sticky navigation on scroll
```

**Cuerpo** — en inglés, con esta estructura:

```markdown
## What
Short description of the change and why it was needed.

## Ticket
{url-del-ticket}

## How to test
1. Go to {exact page}
2. {steps}
3. Expected: {result}

## QA
- [x] Mobile (375px) — checked
- [x] Desktop (1440px) — checked
- [ ] Tablet — not checked ({reason})
- [x] Console clean on affected pages
- [x] Theme Check / lint passing

## Design
1:1 with Figma on mobile and desktop.
{Or: list of intentional deviations and why.}

## Security
- Surface: {summary of the plan's Superficie: inputs, outputs, permissions, secrets, third parties | zero surface}
- Scanners run: {gitleaks / semgrep / osv-scanner: run | not installed (what could not be verified)}
- Findings: Critical {n} · High {n} · Medium {n} · Low {n}
  {list medium/low with file:line and status}

### Security exceptions
{Only if the dev accepted a blocking finding: finding, reason, who accepted it. Omit this subsection otherwise.}

## Anti-slop
- Design source: {Figma node | screenshot | none}
- Functional checks (F-1..F-10): {result: blocking {n} · warnings {n}; what was not tested}
- Aesthetic/voice layer: {applied with the dev's OK, notes | not applied (design source exists or declined)}

### Anti-slop exceptions
{Only if the dev accepted a blocking finding: finding, reason, who accepted it. Omit this subsection otherwise.}

## Out of scope
{What was deliberately left out, and why.}

## Screenshots
{mobile / desktop, before and after when relevant}
```

**Reglas duras:**

- El destino del PR se confirma con el dev. **Un PR contra `main` o `develop` requiere autorización
  explícita en el momento**, distinta de la autorización para pushear.
- Nunca se mergea el propio PR sin revisión.
- Si la rama tiene commits que no son de esta tarea, se resuelve antes de abrir el PR.

## 2. Comentario de cierre en el tracker

**Es el único comentario que el flujo publica en toda la tarea** (`task.comment`), y su trabajo es
**describir qué se hizo**. Nada más. En inglés, en lenguaje claro para el PM — no en jerga técnica.

**Siempre se enseña el borrador completo al dev y se espera su sí antes de publicar.** En Asana un
comentario es permanente (no se edita ni se borra); en SMG Hub se publica con `isInternal: true` salvo
que el dev pida lo contrario, porque `isInternal: false` lo ve el cliente.

```
✅ Ready for review

What was done
- {point by point, in plain language}

Out of scope
- {or "nothing"}

PR: {link}
Preview: {link to THE EXACT PAGE of the change — one per page touched}
```

**Lo que NO va aquí:** el checklist de QA, los pasos para probar, las capturas, el detalle de la
auditoría y el tiempo. Todo eso vive en el **PR** (para el reviewer) y en el reporte en consola (para
el dev). Meterlo en el ticket lo convierte en un muro que el PM no lee.

El reporte que le muestras al dev va en español; **este comentario es su versión en inglés y resumida**,
no una traducción literal pegada.

**El preview apunta a la página del cambio, no a la home.** El reviewer aterriza directo sobre lo que
tiene que mirar; no debe navegar buscándolo. Si se tocaron tres páginas, van tres links.

Si el proyecto usa Loom, el video va en el comentario y **muestra el cambio funcionando** — su duración
escala con el tamaño del cambio, pero existe.

## 3. Tiempo

- Si se arrancó `time.start` en la ignición → `time.stop`.
- Si no → calcula desde la hora registrada en el checkpoint, **confírmala con el dev** y registra con
  `time.add`.
- Si la celda del adaptador es "—" (Asana sin `time_provider`), declara en una línea que no se puede
  por MCP y repórtale la duración al dev para que la cargue.
- Con `time_provider: smg-hub` y un ticket de Asana, `create-time-entry` usa `externalLinkUrl` =
  permalink de Asana (pasos de `time.add` en `rules/eden-tracker-rules.md`).
- Nunca registres tiempo que el dev no confirmó.

## 4. Status y asignación

Pregunta al dev:

- A qué estado mueve la tarea (los estados varían por proyecto y por tracker — se piden en lógico, `review` normalmente, y salen
  de `tracker.statuses`; no se adivinan).
- A quién se la asigna para revisión.

Ejecuta con `task.move` **solo con su respuesta**. Mover un ticket es visible para todo el equipo, y
**nunca se completa ni se cierra**: `done` es del lead.

## 5. Cerrar el checkpoint

`.claude/checkpoint.md` se marca como finalizado o se borra. Un checkpoint viejo hace que la próxima
sesión reanude un trabajo que ya se cerró.
