---
name: test-code
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:test-code` o lo pide de forma explícita e inequívoca, o encadenado desde
  `create-new-section` / `section-mod` / `turnoff-task` como puerta de entrega. NO lo actives porque se
  mencionen tests o porque el código parezca listo: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: TDD a nivel código. Escribe primero los tests del comportamiento (estados,
  eventos, casos borde, limpieza), los corre en rojo, y tras implementar los deja en verde. Además
  verifica que las APIs y librerías usadas son las **vigentes** consultando la documentación actual con
  context7 — nunca de memoria — y reporta lo deprecado. Corre también el linter, el type-check y Theme
  Check según el stack.
argument-hint: "<qué se va a construir o revisar> [| spec | run | currency]"
disable-model-invocation: true
---

## Test Code — TDD y actualidad

Argumento recibido: `$ARGUMENTS`

Dos cosas que suelen ir por separado y aquí van juntas: **que el código haga lo que debe** (tests) y
**que lo haga con lo vigente** (APIs y librerías actuales, verificadas contra la documentación, no
contra la memoria del modelo).

Disciplina completa en `rules/eden-testing-rules.md`.

> **Idioma:** al dev, en español. Los tests y sus descripciones, en inglés.

**Regla cero: manda el proyecto.** Si ya tiene runner, convenciones y carpeta de tests, se usan esos.
Si no tiene nada, se **propone** uno y se confirma antes de montarlo — instalar un framework de tests es
una decisión del dev, no una consecuencia de esta tarea.

---

### Modo `spec` — los tests primero (🔴)

**Antes de escribir la lógica.** Del requerimiento y del comportamiento esperado salen los asertos.

**Qué se testea, según lo que hay** (`references/what-to-test.md`):

| Qué | Cómo |
|---|---|
| **Web Components / JS** | Comportamiento: estado inicial, respuesta a eventos, casos borde, y **limpieza en `disconnectedCallback`** |
| **Lógica pura** | Entradas → salidas, incluidos los extremos (vacío, uno, muchos, malformado) |
| **Plantillas (Liquid)** | No hay unitario nativo: Theme Check + verificación de render con datos reales, vacíos y extremos |
| **Integración** | El flujo completo que el ticket describe, de punta a punta |

Se escriben los tests, **se corren y deben fallar**. Un test que pasa antes de implementar no está
midiendo nada — revísalo antes de seguir.

```
🔴 SPEC ESCRITA — {qué}
   {n} tests · {archivo}
   Corriendo: {n} fallan, 0 pasan → correcto, todavía no hay implementación
```

---

### Modo `run` — la suite (🟢)

Corre **todo lo que el stack tenga**, y reporta la salida real:

```bash
# lo que el proyecto use — se detecta, no se asume
npm test        # o vitest / jest / …
npm run lint
npm run typecheck
shopify theme check    # en temas Shopify

# WordPress
php -l {archivos}
composer exec phpcs -- --standard=WordPress {nuestras-rutas}
npx wp-scripts lint-js {rutas}    # si hay bloques
```

```
🟢 TEST CODE — {qué}
   Tests       {n}/{n} ✅
   Linter      {resultado}
   Type-check  {resultado}
   Theme Check {n} errores · {n} warnings

❌ FALLA · {test}
   esperado {…} · actual {…}
   dónde    {archivo:línea}
```

**La salida real, siempre.** Si algo falla se pega lo que dijo la herramienta, explicado en español —
no un resumen optimista.

---

### Modo `currency` — que sea lo vigente

La parte que evita el error silencioso: **usar una API que ya no es la recomendada**. Pasa el linter,
funciona hoy, y rompe en la siguiente actualización de la plataforma.

**Nunca de memoria.** Antes de usar (o de dar por bueno) algo no trivial, se consulta la documentación
actual:

```
context7: resolve-library-id  → identificar la librería
context7: query-docs          → la sintaxis y las opciones VIGENTES
```

Procedimiento y qué verificar en cada stack: `references/library-currency.md`.

**Qué se revisa:**

- **APIs y filtros de la plataforma** — en Shopify cambian con frecuencia: tags de Liquid, opciones de
  schema, filtros, endpoints de la Admin API. En **WordPress**, funciones deprecadas del core, la firma
  de `block.json` y su `apiVersion`, y las APIs del editor (Interactivity, Block Bindings), que se
  mueven rápido. Se contrasta contra la doc del año en curso.
  ⚠️ En WordPress una función deprecada **pasa el linter y sigue funcionando durante meses**: es
  exactamente el caso que este modo existe para atrapar.
- **Métodos de librerías** — firmas, opciones renombradas, cosas movidas a otro paquete.
- **Deprecaciones** — lo que sigue funcionando pero ya está marcado como saliente.
- **Lo que el proyecto ya usa** — si algo existente está deprecado, **se reporta**; no se arregla de
  paso salvo que la tarea lo pida (eso es alcance nuevo, y lo decide el dev).

```
📚 ACTUALIDAD

✅ Vigente
   · {API/método} — confirmado en la doc actual de {fuente}

⚠️ Deprecado — en uso
   · {qué} en {archivo:línea}
     Reemplazo actual: {qué}
     ¿Está en el alcance de esta tarea? → decisión tuya

❓ No pude verificar
   · {qué} — {por qué: sin doc en context7, librería interna, sin conexión}
```

Lo que no se pudo verificar **se dice**. Afirmar que algo es vigente sin haberlo comprobado es
exactamente el error que este modo existe para evitar.

---

### El ciclo

```
spec (🔴 falla)  →  implementar  →  run (🟢 pasa)  →  currency  →  refactor  →  run
```

En `create-new-section` y `section-mod`, la spec se escribe con el plan y el `run` es parte de la
verificación. En `turnoff-task` es **puerta**: sin verde no se entrega, o se declara exactamente qué
quedó sin testear y por qué.

---

### Qué NO se hace

- **No se escriben tests que no puedan fallar.** Un aserto sobre algo siempre cierto es ruido que hay
  que mantener.
- **No se testea la existencia de código**, se testea el comportamiento.
- **No se instala un framework de tests sin aprobación.**
- **No se marca verde lo que no se corrió**, ni se resume una salida que no se leyó.
- **No se "arregla de paso"** lo deprecado que la tarea no pedía: se reporta y lo decide el dev.
