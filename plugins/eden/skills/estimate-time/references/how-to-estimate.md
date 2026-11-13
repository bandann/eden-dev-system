# Referencia — El método de estimación

Estimar bien no es acertar el número: es **poder explicar de dónde sale** y equivocarse cada vez menos.

## 1. La jerarquía de las fuentes

Se usa la mejor disponible, y **se declara cuál se usó**:

| # | Fuente | Confianza |
|---|---|---|
| 1 | **Tiempo real de una tarea equivalente** en este mismo proyecto | ALTA |
| 2 | Tiempo real de algo equivalente **en otro proyecto** del mismo stack | ALTA/MEDIA |
| 3 | Tiempo real de algo **parecido pero no igual**, ajustado por diferencias | MEDIA |
| 4 | Descomposición en partes que sí tienen histórico | MEDIA |
| 5 | Nada comparable | **BAJA → se entrega como rango** |

```
time.list      → lo que de verdad se tardó
task.history   → cuánto en In Progress vs en Review
```

El **tiempo en Review** es el dato que casi nadie mira y el que más explica las desviaciones: si una
tarea parecida pasó 6 horas rebotando entre Review e In Progress, ese rework va a repetirse.

## 2. Los multiplicadores que mueven el número

Sobre la base histórica, lo que la sube o la baja:

| Factor | Efecto |
|---|---|
| **Escalón reuse-first** | Configurar ≪ extender schema < código acotado ≪ componente nuevo. Es el factor #1 |
| **Breakpoints** | Si el perfil activo declara `qa.breakpoints`, el QA cubre todos esos anchos, no solo dos |
| **Estados** | Hover, focus, disabled, vacío, error, carga — cada uno se implementa y se prueba |
| **Animación** | Suma desarrollo **y** el aserto de `prefers-reduced-motion` |
| **Blast radius** | Tocar algo de 20 páginas multiplica el QA de regresión, no el desarrollo |
| **Datos del cliente** | Metafields, contenido que sube el merchant, integraciones: suman coordinación, no solo código |
| **Huecos del diseño** | Cada hueco es una ida y vuelta con el diseñador. **Se estima el ciclo, no solo el código** |

## 3. Las reglas de negocio del perfil (si existen)

Si el perfil declara `business_rules`, léelas antes de estimar. Estas cosas se subestiman
sistemáticamente porque parecen pequeñas:

- **Una regla que debe cumplirse en varios lugares** — no es tocar un sitio: es verificar cada lugar
  donde el tema la pinta. Lo que parece media hora son dos.
- **Un dato que debe llegar hasta el pedido** — la parte cara no es el control de la interfaz, es que
  el valor llegue al carrito y al pedido, y probarlo end-to-end.
- **Un flujo con servicios externos** — incluido comprobar que el email o la notificación sale de verdad.

## 4. Reparto típico por fase

Como punto de partida cuando no hay histórico — **se ajusta con los datos reales, no se toma como ley**:

```
Análisis            10–15%
Desarrollo          40–50%
Tests del kit       15–20%   ← incluye el loop de corrección hasta verde
QA del dev          10–15%
Cierre               5–10%
Margen              15–25%   ← más alto cuanto menor la confianza
```

Lo que este reparto hace visible: **el desarrollo es menos de la mitad**. Una estimación que solo cuenta
"cuánto tardo en escribirlo" se queda corta por diseño.

## 5. Bugs: se estiman distinto

Un bug tiene una parte impredecible —encontrar la causa— y una predecible —arreglarlo y verificarlo—.
No se estiman juntas:

```
Investigación   {rango, siempre}   ← con un tope: "si en 2h no está la causa, replanteamos"
Arreglo         {estimación normal}
Verificación    {test + QA + comprobar que no reaparece}
```

El **timebox de investigación** es lo que evita que un bug se coma un día sin que nadie se entere.

## 6. Cómo se escribe una estimación defendible

```
{unidad}  {total}
   Base:      {qué tarea real y cuánto tardó}
   Ajustes:   {qué difiere y cuánto suma o resta}
   Confianza: {ALTA | MEDIA | BAJA}
   Riesgo:    {qué la haría saltar, y cuánto}
```

Si no puedes rellenar **Base**, la confianza es BAJA por definición — por bien que suene el número.

## 7. Errores que este método evita

- **Estimar solo el desarrollo.** Es menos de la mitad del trabajo.
- **Esconder el margen** repartido en las otras fases: hace la estimación imposible de revisar y de
  aprender de ella.
- **Dar un número único con confianza baja.** Fingir precisión cuesta más que admitir el rango.
- **Olvidar el QA del dev.** Es tiempo del proyecto aunque no lo ejecute el kit.
- **Ajustar la estimación al plazo deseado.** Si no cabe, eso es información para el PM — no un error
  que corregir bajando números.
- **No comparar después.** Sin el cierre del ciclo, la siguiente estimación es igual de mala.
