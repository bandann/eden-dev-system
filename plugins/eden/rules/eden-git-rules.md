# Reglas de Git — Eden

## Ramas

Formato: `{tipo}/{ticket-id}-{slug}`

- **tipo**: `feature`, `fix`, `hotfix`, `chore`, `refactor`, `style`, `docs`.
- **ticket-id**: el id del ticket del tracker en minúsculas (`86ca177cj`, `prj-231`, el GID de Asana o el id de SMG Hub;
  ver `eden-tracker-rules.md`). Sin ticket → `no-ticket`.
- **slug**: 2–4 palabras en inglés, minúsculas, con guiones.

```
feature/86ca177cj-mega-menu
fix/prj-231-cart-total-rounding
chore/no-ticket-update-locales
```

Reglas:

- **La base siempre se pregunta.** No hay rama base por defecto.
- Una rama por tarea. No se mezclan cambios no relacionados.
- La URL del ticket se guarda en la rama:
  ```bash
  git config branch.<rama>.ticket-url "<url>"
  ```
- Al mergear, se borra la rama (y su preview, si el proyecto genera uno).

## Commits — Conventional Commits

```
feat(header): add sticky navigation on scroll

Ticket: https://app.asana.com/0/{project_gid}/{task_gid}
```

- Tipos: `feat`, `fix`, `refactor`, `chore`, `style`, `docs`, `test`.
- Scope: el componente o área afectada (`header`, `cart`, `product`, `footer`, `global`).
- Descripción: imperativo, minúsculas, sin punto final, en inglés.
- Un commit por cambio lógico.
- Trailer `Ticket:` con la URL, siempre que haya ticket.
- **Sin firma de la IA.** Ni `Co-Authored-By: Claude …` (ni de Codex, Gemini, Qwen, Kimi, Grok u otra IA)
  en el commit, ni "Generated with Claude Code" (o con otra herramienta) en el PR. El autor es el dev. Lo
  apaga `attribution` en `~/.claude/settings.json` y lo bloquea `hooks/eden_guard.py` antes de cada commit
  y push — como hook de la herramienta y, si el dev los instaló con `/eden:setup githooks`, como hook de
  git del repo, que protege con cualquier IA o sin ella.

## Ramas protegidas

`main`, `master` y `develop` están **siempre** protegidas. Un proyecto puede proteger más, declarándolas
en su `CLAUDE.md`:

```
<!-- protected-branches: main, develop, staging -->
```

Sobre una rama protegida:

- Nunca push directo.
- Nunca force-push.
- **Un PR hacia ella requiere autorización explícita del dev en el momento** — distinta de la
  autorización para pushear la rama de trabajo.

Las ramas de trabajo sí se pushean directo.

## Pull Requests

- Título en formato de commit.
- Cuerpo (en inglés) con: qué se hizo, link al ticket, cómo probarlo, checklist de QA por breakpoint,
  capturas si es visual, y qué quedó fuera.
- Nunca se mergea el PR propio sin revisión.
- Se revisa antes de mergear, por el lead o por Claude.

## Nunca

- Push directo a rama protegida.
- Force-push a rama compartida.
- Commitear `.env`, claves, tokens o credenciales.
- Commitear `node_modules/`, builds o archivos generados.
- Commitear archivos de playground, debug o `.claude/checkpoint.md`.
- Firmar commits o PRs como la IA (`Co-Authored-By: Claude`, `noreply@anthropic.com`, "Generated with
  Claude Code", o lo mismo de cualquier otro asistente). Un co-autor humano sí vale.
- Saltarse hooks (`--no-verify`) o firmas sin que el dev lo pida explícitamente. Si un hook falla, se
  investiga la causa.
