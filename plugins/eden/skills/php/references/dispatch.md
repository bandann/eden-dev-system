# Dispatch — cómo reparte el líder PHP

## 1. Partir en unidades

| Tamaño | Ejemplo | Cómo se ejecuta |
|---|---|---|
| **S** | Una regla de validación, un campo en un Resource, un ajuste en una vista | Un especialista (+ su test) |
| **M** | Un CRUD de un recurso, un endpoint con su Policy, un job | tester → data-dev → php-dev |
| **L** | Una funcionalidad con varias tablas, colas y vistas | Varias unidades M con dependencias declaradas |
| **XL** | Un proyecto o un módulo entero | Lotes L por funcionalidad |

Una unidad que cruza dueños **se parte**: test (tester) → esquema y modelos (data-dev) → rutas,
controladores, Form Requests, Policies y vistas (php-dev).

## 2. Asignar

| Si la unidad es… | Especialista |
|---|---|
| Entender lo que existe, quién lo usa | `eden:php-architect` |
| Rutas, controladores, Form Requests, Policies, middleware, servicios, vistas Blade/Livewire | `eden:php-dev` |
| Front de Inertia con React | `eden:react-ui-dev` (roster React) |
| Modelos, migraciones, factories, seeders, jobs, eventos, API Resources, integraciones | `eden:php-data-dev` |
| Tests (primero) | `eden:php-tester` |
| Entorno, Composer, config, Pint, PHPStan, CI | `eden:php-devops` |
| Figma → Design Spec · medir Figma vs render | `eden:figma-extractor` · `eden:design-auditor` |
| Revisar el diff; calidad | `eden:php-qa-reviewer` |
| Seguridad independiente | `eden:security-auditor` |

`bootstrap/app.php` y `config/auth.php`: el líder decide el dueño y lo escribe en el plan.

## 3. Plantilla del plan (al dev, en español)

```
🐘 PLAN DEL EQUIPO PHP

Trabajo: {new | onboard | task} · {ticket / descripción} · sabor {php | laravel}
Rama: {nombre} desde {base — preguntada}

| # | Unidad | Tamaño | Especialista | Archivos | Escalón | Depende de |
|---|---|---|---|---|---|---|
| 1 | Tests de {x} | S | eden:php-tester | tests/Feature/XTest.php | — | — |
| 2 | Esquema y modelo | S | eden:php-data-dev | database/migrations/…, app/Models/X.php | 3 — {por qué} | 1 |
| 3 | Endpoint + Policy | M | eden:php-dev | routes/api.php, app/Http/…, app/Policies/XPolicy.php | 4 | 1, 2 |

Esquema: {tablas · columnas · índices · ¿datos que mover?} — migración reversible
🛡️ Superficie: entra {…} · validado en {Form Request} · quién {Policy} · sale {Resource} · secretos {…} · terceros {…}
Verificación: reviewer + security-auditor al final · design-auditor en {vistas}
Paro a preguntarte en: {paquetes, esquema con datos, bootstrap/app.php, .env}
Blast radius: {consumidores — de architect}
Queda fuera: {…}

¿Le doy?
```

## 4. Plantilla del encargo (al especialista, en inglés)

```
UNIT {n} — {title}
WHAT: {observable result in one sentence}
WHERE (closed list): {files}. Anything else → stop and report.
WITH: flavor {php | laravel} (rules/php/flavors/{x}.md) · PHP {v} · Laravel {v} · reuse step {n}: {why} ·
      sibling pattern: {file} · consumers: {from architect} · tests to make green: {files}
ACCEPT WHEN: {tests green; pint --test clean; phpstan no new errors; migration up+down on the test DB}
DO NOT: touch other files; add/remove/upgrade packages; migrate/seed outside the local/test DB; deploy;
        put secrets in code or .env.example; disable PHPStan rules, tests or CSRF; {unit-specific}
HANDOFF: teams/php/roster.md format. Ambiguity → stop, return DECISIÓN PENDIENTE.
```

## 5. Paralelismo

Solo unidades con **archivos disjuntos**, en un solo turno, como mucho 4 a la vez. Dos unidades que
crean migraciones pueden chocar en el orden: van en secuencia.
