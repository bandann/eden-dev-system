# Referencia — Ramas, commits y trazabilidad

La rama es el vínculo entre el código y la tarea. Cualquiera del equipo debe poder mirar una rama y
llegar al ticket en un clic.

## 1. La base SIEMPRE se pregunta

No hay rama base por defecto en Eden. Antes de crear nada:

```bash
git fetch origin
git branch -a
```

Muéstrale al dev las candidatas (marcando la actual) y pregunta explícitamente de dónde sale la rama.
Recién con su respuesta:

```bash
git switch <base>
git pull --ff-only
git switch -c <tipo>/<ticket-id>-<slug>
git config branch.<rama>.ticket-url "<url-del-ticket>"
```

Si la base elegida tiene cambios locales sin commitear, resuélvelo con el dev antes de ramificar.

## 2. Nombre de la rama

```
{tipo}/{ticket-id}-{slug}
```

- **tipo**: `feature`, `fix`, `hotfix`, `chore`, `refactor`, `style`, `docs`.
- **ticket-id**: el id del ticket tal cual (`86ca177cj`, o un custom id como `prj-231`, en minúsculas; si el
  proyecto define `project.prefix`, va delante del id).
  Sin ticket → `no-ticket`.
- **slug**: 2–4 palabras en inglés, minúsculas, con guiones.

```
feature/86ca177cj-mega-menu
fix/prj-231-cart-total-rounding
hotfix/86cb01xyz-checkout-crash
chore/no-ticket-update-locales
```

Todo en minúsculas y en inglés. Una rama por tarea; nunca se mezclan trabajos distintos.

## 3. Commits

Conventional Commits, en inglés, con trailer al ticket:

```
feat(header): add sticky navigation on scroll

Ticket: <url-del-ticket>
```

- Tipos: `feat`, `fix`, `refactor`, `chore`, `style`, `docs`, `test`.
- Scope: la sección/componente afectado (`header`, `cart`, `product`, `footer`, `global`).
- Descripción: imperativo, minúsculas, sin punto final.
- Un commit por cambio lógico. Nunca se empaquetan cambios no relacionados.

## 4. Ramas protegidas

`main`, `master` y `develop` están **siempre** protegidas. Un proyecto puede proteger más — se declaran
en el `CLAUDE.md` del proyecto:

```
<!-- protected-branches: main, develop, staging -->
```

Sobre una rama protegida:

- **Nunca** push directo.
- **Nunca** force-push.
- Un PR hacia ella requiere **autorización explícita del dev** en el momento (`turnoff-task` la pide).

Las ramas de trabajo (feature/fix/…) sí se pushean directo.

## 5. Recuperar el contexto de una rama

```bash
git config branch.$(git branch --show-current).ticket-url
git log --format='%s%n%b' -1 | grep '^Ticket:'
```

Si una rama no tiene `ticket-url`, agrégala en cuanto lo detectes — es la forma de volver al ticket
desde el código meses después.

## 6. Nunca se commitea

`.env` y cualquier secreto, `node_modules/`, archivos generados/compilados, archivos de playground o
debug, `.claude/checkpoint.md`.
