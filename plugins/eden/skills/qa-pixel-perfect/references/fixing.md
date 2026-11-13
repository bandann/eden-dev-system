# Referencia — Cómo se corrige sin romper el sitio

Este es el único skill del kit que **mide y además arregla**. Esa capacidad es útil exactamente en la
medida en que no genere un problema mayor que el que resuelve.

> La pregunta que se hace antes de cada corrección: **¿este valor vive solo aquí, o lo consume alguien
> más?** De la respuesta depende si se corrige o se pregunta.

---

## La clasificación, con ejemplos reales

### 🟢 Corrección segura — se aplica

El valor está acotado a la sección que se está revisando y nadie más lo consume:

- Un `padding-top` de 24px que debía ser 32px, en el CSS de esa sección.
- Un `gap` propio del bloque.
- Un `font-size` declarado en la clase de esa sección — **si el valor correcto existe como token**.
- Una alineación (`align-items`, `text-align`) dentro del componente.
- Un `aspect-ratio` o un `object-fit` de una imagen de esa sección.

Se corrige, se registra el `archivo:línea`, y **se vuelve a medir**.

### 🟡 Requiere decisión — se para y se pregunta

Cualquiera de estas, sin excepción:

| Situación | Por qué se para |
|---|---|
| El valor correcto **es un token** y hay que cambiar el token | Repinta o remide todo lo que lo use |
| No existe token para el valor correcto | Crear uno afecta al design system del proyecto |
| El valor está en un **componente/snippet compartido** | Blast radius: otras secciones y páginas |
| Hay que cambiar el **default de un setting** | Cambia instancias ya publicadas |
| El Figma difiere entre breakpoints y **no hay control responsive** | Es un hueco de configuración, no un override CSS |
| Hay que tocar `theme.json`, `settings_schema.json` o un preset global | Es configuración del proyecto |
| La corrección exige **cambiar el marcado**, no solo el estilo | Puede afectar a la semántica, el SEO o el JS |

Antes de presentar la decisión, **se mide el blast radius**:

```bash
grep -rn "{clase|variable|snippet}" --include="*.liquid" --include="*.css" --include="*.js" --include="*.json" .
graphify affected "{lo que se tocaría}" --depth 2     # si el proyecto tiene cerebro
wp db search "{clase|bloque}" --stats                 # en WordPress, el contenido publicado
```

Y se presenta así, con el coste de cada opción:

```
🟡 {sección} · {propiedad}
   Figma: {valor} · actual: {valor}
   Para igualarlo hay que tocar: {token / componente / setting}
   Blast radius: {n} secciones · {n} páginas · {n} instancias publicadas

   A) Cambiar {lo compartido} → esta página queda 1:1, y cambian también {qué}
   B) Override acotado a esta sección → 1:1 aquí, pero el sistema queda inconsistente
   C) Dejarlo y reportar al diseñador → puede que el Figma esté desactualizado

   ¿Cuál?
```

**Nunca se elige la B por defecto** porque "es la que no rompe nada": un override que contradice el
token es deuda que reaparece en la siguiente tarea.

### 🔴 No se puede igualar — se declara

- La **fuente del Figma no está disponible** (no está en la librería de la plataforma, o no hay
  licencia).
- La plataforma **no permite** ese control (un espaciado que el builder no expone).
- El **Figma no define** el breakpoint o el estado que falta.
- El contenido es **dinámico** y su longitud real no coincide con el mockup.

**No se aproxima.** No se pone "la fuente más parecida" ni se fuerza una altura fija para que cuadre con
un texto que en producción será distinto. Se reporta qué es, por qué, y qué haría falta para cerrarlo.

---

## Lo que no se suspende al corregir

Las reglas del kit siguen valiendo dentro de este skill:

- **Colores y tipografía por token.** Si la corrección "correcta" es un hex crudo, no es 🟢: es 🟡.
- **Acotado al bloque**, con la convención de clases del proyecto.
- **Los patrones del proyecto mandan** sobre cualquier preferencia.
- **Nada de "ya que estoy"**: se corrige lo medido, no lo que parezca mejorable.
- **Sin `!important`** para ganar una especificidad. Si hay que escalar especificidad, algo está mal
  estructurado y eso es 🟡.

---

## Re-medir es parte de corregir

Una corrección no está hecha hasta que se volvió a medir. Y hay que medir **más que lo corregido**:

| Se corrigió | Hay que volver a medir |
|---|---|
| Un padding o margin | La sección **y la distancia con la de arriba y la de abajo** |
| Un tamaño de fuente | La altura de la caja y el reflujo del texto |
| Un ancho o un contenedor | La alineación con el resto de secciones de la página |
| Cualquier cosa | **Todos los breakpoints**, no solo en el que se detectó |

Corregir en desktop y no verificar en 375 es cómo se arregla una cosa y se rompen dos.

---

## Cuándo parar el loop

El ciclo termina cuando:

- No quedan 🟢 ni 🟡 aprobadas sin cerrar.
- Lo pendiente son 🟡 esperando decisión del dev, o 🔴 declaradas.

**No se para "porque ya está bastante bien".** Y si en la tercera vuelta una misma medida sigue sin
cerrar, se para y se reporta: es señal de que el problema no es el valor sino la estructura, y eso es
una decisión, no una corrección.

---

## Lo que nunca se hace

- Tocar un token, un componente compartido o un default **sin aprobación**.
- Aproximar lo que no se puede igualar y contarlo como resuelto.
- Corregir el Figma "mentalmente" — si el diseño parece equivocado, se reporta; no se decide por él.
- Dar por corregido lo que no se volvió a medir.
- Acumular correcciones y medir al final: se mide después de cada una, o no se sabe cuál rompió qué.
