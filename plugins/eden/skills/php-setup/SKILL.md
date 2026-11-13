---
name: php-setup
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Se usa únicamente cuando el dev escribe
  `/eden:php-setup`, lo pide de forma explícita e inequívoca, o encadenado desde `/eden:php` (que ya fue
  invocado por él y le pide confirmación antes). NO lo actives porque el proyecto sea PHP o falte una
  herramienta: si no lo pidió por su nombre, no se usa. — Qué hace cuando SÍ se invoca: levanta el
  entorno de desarrollo de un proyecto PHP o Laravel. En un proyecto nuevo pregunta el sabor (Laravel o
  PHP sin framework), la versión de PHP, el entorno local (Herd, Sail/Docker o PHP del sistema), la base
  de datos, el starter kit y las herramientas (Pest o PHPUnit, Pint, PHPStan), y lo monta con el
  instalador vigente. En uno existente completa solo lo que falta, sin tocar lo que funciona, y declara
  el bloque `php` en `project-config.json`. Nunca despliega, ni toca bases reales, ni instala paquetes
  sin el sí del dev.
argument-hint: "[ruta del proyecto] [| laravel | php] [| herd | sail | docker | local] [| nuevo | existente]"
disable-model-invocation: true
---

## PHP Setup — el entorno del proyecto

Argumento recibido: `$ARGUMENTS`

Deja el proyecto en el estado en el que cualquier skill del kit puede trabajar y verificar: PHP con
soporte, Composer, el framework instalado con su versión vigente, una base de datos local y otra de
tests desechable, y las herramientas que el kit usa para verificar (tests, Pint, PHPStan, `composer
audit`).

> **Idioma:** al dev, en español. Archivos, comentarios y config, en inglés.

**Modelos:** la sesión principal decide y pregunta; el trabajo lo hace `eden:php-devops`, con
`eden:php-architect` para el inventario si el proyecto ya existe.

### Lo que NO hace — nunca

- **Desplegar** ni conectarse a un servidor o a una base que no sea local.
- **Instalar herramientas globales** (PHP, Composer, Herd, Docker) ni paquetes sin el sí del dev, con la
  lista exacta delante.
- **Escribir secretos**: `.env.example` solo lleva nombres y comentarios; el `.env` real lo rellena el dev.
- Commitear o pushear. Crear la rama sí, local, con la base que diga el dev.

---

### Paso 1 — Qué hay

`python -I "${CLAUDE_PLUGIN_ROOT}/scripts/eden_stack.py" detect {ruta}` y, si hay código, un `inventory`
de `eden:php-architect`:

- ¿`composer.json`/`composer.lock`? ¿Qué PHP exige y qué Laravel (si hay)? `php -v`, `php -m`,
  `composer --version`.
- ¿Entorno local en uso (Herd, Sail, Docker Compose, PHP del sistema)?
- ¿Tests (Pest o PHPUnit) y contra qué base corren? ¿Pint, PHPStan/Larastan, Rector? ¿Scripts de Composer?
- ¿`.env.example`, `.gitignore` correcto, `.claude/project-config.json` con su bloque `php`?

Si el resultado es **WordPress**, se para: su setup es `/eden:wp-setup`.

### Paso 2 — Preguntar lo que falta, en una sola intervención

Antes, comprueba en la doc vigente (context7 o php.net / laravel.com) el comando de instalación, la
versión de PHP que exige el framework y las fechas de soporte: no se usan de memoria.

```
🐘 SETUP PHP — necesito:

Sabor:          [laravel] · [php — sin framework]        (recomiendo {x} porque {razón del proyecto})
PHP:            {instalado} — Laravel {v} exige {rango} {✅ | ❌}; recomiendo {8.4 o 8.5}
Entorno local:  Herd · Sail (Docker) · Docker Compose · PHP del sistema   (recomiendo {x})
Base de datos:  SQLite (por defecto en Laravel) · MySQL · PostgreSQL
Starter kit:    React · Vue · Svelte (Inertia) · Livewire · ninguno — solo Laravel
Tests:          Pest (recomendado) · PHPUnit
Calidad:        Pint ✅ · PHPStan/Larastan nivel {n} · Rector {sí | no}
Boost:          Laravel Boost (MCP para agentes) {sí | no}
Carpeta:        {ruta} {vacía ✅ | con archivos ⚠️}
Rama base:      {la que digas}
```

Para un proyecto **existente** se pregunta solo lo que falta, con lo que se va a añadir y por qué.

### Paso 3 — Montarlo (delegado a `eden:php-devops`)

Con el encargo de cinco partes y el sí del dev explícito en él (incluida la lista de paquetes):

- **Laravel nuevo:** el instalador vigente con el starter kit y la base elegidos; base de tests
  desechable en `phpunit.xml`; Pint; Larastan con el nivel acordado; scripts `test`, `lint`, `analyse`;
  `.env.example` sin valores; `.gitignore`.
- **PHP sin framework nuevo:** `composer init` con autoload PSR-4, `public/index.php` como único punto
  de entrada, `src/`, `tests/`, Pest o PHPUnit, Pint (preset `per`), PHPStan, `.env.example`.
- **Existente:** solo los huecos aprobados.

### Paso 4 — Verificar y declarar

1. `composer install`, `composer validate`, `composer audit`; en Laravel, `key:generate` y `migrate` **en
   la base local**; tests, `pint --test`, `phpstan analyse`: la salida real de cada uno.
2. El servidor local arranca y la página inicial responde (si hay navegador o Playwright, se mira; si no,
   se declara).
3. Escribe en `.claude/project-config.json`: `project.stack: "php"` y el bloque `php` (`flavor`,
   `php_version`). Si no existe el archivo, desde `team/project-config.example.json`.
4. En el `CLAUDE.md` del proyecto, el marcador `<!-- eden-stack: php -->` y una línea con el sabor.

### Paso 5 — Reporte

```
🐘 SETUP PHP — LISTO

Sabor: {laravel | php} · PHP {v} (soporte de seguridad hasta {fecha}) · Laravel {v} · entorno {x} · base {x}
Herramientas: tests {Pest | PHPUnit} ✅ · Pint ✅ · PHPStan nivel {n} ✅ · composer audit {limpio | n avisos}
Verificación: {salida resumida de cada comando}
Declarado: project-config.json (php.flavor = {x}) · CLAUDE.md
Pendiente del dev: {.env real, servicios (correo, colas), el deploy}

➜ Siguiente: /eden:php para la primera tarea, o /eden:laravel-feature para una funcionalidad.
```
