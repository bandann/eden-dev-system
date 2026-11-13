# Sabor: Node sin framework

Node con librerías pequeñas o solo con lo que trae: servicios, workers, CLIs, webhooks, APIs mínimas.
**Sin framework, lo que Express o Nest dan hecho (enrutado, errores, validación) lo escribe el proyecto**:
por eso este sabor es más estricto con lo básico.

## Estructura habitual

```
src/
├── app.ts · handler.ts   la lógica, exportada (testeable sin levantar nada)
├── server.ts · index.ts  el arranque: config, listen, apagado limpio
├── config.ts             variables de entorno validadas al arrancar
├── lib/ · services/      lógica
└── workers/ · jobs/      trabajo en segundo plano
test/
package.json ("type": "module") · tsconfig.json · .env.example
```

**Manda la estructura real del proyecto.**

## Lo que aquí no viene gratis

| Qué | Cómo |
|---|---|
| **Servidor HTTP** | `node:http` con un router pequeño, o el que ya use el proyecto. Si las rutas crecen, se propone Express o Nest (es una dependencia: decide el dev) |
| **Validación** | Un esquema (Zod) por entrada; nada se usa sin pasar por él |
| **Errores** | Un manejador único que traduce excepciones a respuestas sin detalles internos; `process.on('unhandledRejection')` registra y termina de forma controlada |
| **Límites** | Tamaño máximo del cuerpo, timeouts de petición y de conexiones salientes |
| **Configuración** | `--env-file` o la librería del proyecto en local; validada al arrancar |
| **Apagado** | `SIGTERM` → dejar de aceptar, terminar lo pendiente, cerrar conexiones |

## TypeScript sin build

`node src/server.ts` funciona con **type stripping** (estable): solo sintaxis borrable (sin `enum`,
`namespace` en tiempo de ejecución, decoradores ni parameter properties), imports con extensión `.ts` e
`import type`, y los `paths` de `tsconfig` no se aplican (se usan imports `#` de `package.json`). **No
comprueba tipos**: el `typecheck` (`tsc --noEmit`) sigue siendo la puerta. Si el proyecto necesita
sintaxis que no se borra, usa un paso de build o `tsx`.

## Workers y CLIs

- Un worker procesa con concurrencia acotada, reintentos con backoff y un estado que sobrevive a un
  reinicio; es idempotente.
- Un CLI valida sus argumentos, devuelve códigos de salida reales y no imprime secretos.

## Tests y validación propia de este sabor

`node:test` (estable) o el runner del proyecto; supertest si hay servidor HTTP.

```bash
{pm} run lint && {pm} run typecheck && {pm} test && {pm} run build   # build si existe
{pm} audit
```
