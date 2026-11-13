# Testing — Eden (test-first, y nada se entrega sin test)

Dos niveles, una disciplina: **el criterio de aceptación se escribe antes que el código**, y **ninguna
tarea se entrega sin haber pasado su test**.

## La puerta

`turnoff-task` no cierra una tarea sin esto:

| | Requisito |
|---|---|
| **Visual** | Test de fidelidad **verde**: todos los nodos 1:1 con Figma, en todos los breakpoints |
| **Código** | Tests del stack en verde + validación (Theme Check / linter / type-check) |
| **Actualidad** | Nada deprecado; las APIs y librerías usadas son las vigentes |

Si algo no se pudo testear, **se declara qué y por qué** — no se marca como pasado. Un test que nadie
corrió es peor que ninguno: da confianza falsa.

---

## Test-first: por qué el orden importa

El ciclo es **🔴 rojo → 🟢 verde → ♻️ refactor**:

1. **Del Figma sale el baseline antes de escribir código.** Los valores esperados —colores, tipografía,
   espaciados— se extraen y se congelan primero.
2. **Se corre el test y falla.** Eso confirma que el test mide algo real. Un test que pasa antes de
   implementar no está midiendo nada.
3. **Se implementa hasta que pasa.**
4. **Se refactoriza** con el test como red.

Escribir el test después convierte el test en una descripción de lo que hiciste, no en una verificación
de lo que debías hacer. Con el baseline primero, **el diseño es el que manda**, no la implementación.

---

## Nivel visual — 1:1 en todos los nodos

Se verifica **nodo por nodo**, en **todos los breakpoints**, y sin excepción en:

| Grupo | Qué se asevera |
|---|---|
| **Color** | Texto, fondo, bordes, iconos — y **que venga del token**, no hardcodeado |
| **Tipografía** | Familia, tamaño, peso, line-height, letter-spacing, transform |
| **Espaciado** | Padding (4 lados), margin (4 lados), gap |
| **Dimensiones** | Ancho, alto, ancho máximo del contenedor, aspect-ratio |
| **Animación** | Propiedad, duración, easing, delay — y `prefers-reduced-motion` respetado |
| **Responsive** | Todo lo anterior, en cada breakpoint del proyecto o del perfil |

**Un color correcto pero hardcodeado falla el test.** Coincide en pantalla y aun así está mal: rompe el
sistema de tokens y no se actualizará cuando cambie el esquema.

Lo ejecuta `test-visual`, que mide el render real con Playwright contra un baseline derivado de Figma.

Para el pase de **página completa** antes de entregar está `qa-pixel-perfect`: recorre todas las
secciones, añade lo que solo se ve a nivel página (orden, espaciado entre secciones, contenedor común,
scroll horizontal) y **corrige** — lo seguro por su cuenta, lo compartido preguntando, y lo que no se
puede igualar lo declara en vez de aproximarlo.

---

## Nivel código

Qué se testea depende del stack. **Se sigue lo que el proyecto ya usa**; si no tiene nada, se propone y
se confirma antes de montarlo.

- **Lógica JS / Web Components** → tests unitarios del comportamiento: estados, eventos, casos borde,
  limpieza en `disconnectedCallback`.
- **Plantillas (Liquid)** → no hay test unitario nativo: la red es **Theme Check** + la verificación de
  render (que el marcado salga correcto con datos reales, vacíos y extremos).
- **Cualquier stack** → el linter y el type-check del proyecto son parte del test, no un extra.

### Actualidad de librerías y APIs

Parte del test de código, no una revisión aparte: **lo que se usa tiene que ser lo vigente**.

- Antes de usar una API, un filtro o un método de librería que no sea trivial, **se verifica contra la
  documentación actual** — con **context7** (`resolve-library-id` → `query-docs`) o la doc oficial.
- **No se confía en la memoria del modelo**: las plataformas cambian etiquetas, filtros y firmas, y una
  API deprecada pasa el linter y falla en producción meses después.
- Si algo que el proyecto ya usa está deprecado, **se reporta** — no se arregla de paso salvo que la
  tarea lo pida.

---

## Qué NO se hace

- **No se escribe un test que no puede fallar.** Un aserto sobre algo que siempre es cierto es ruido.
- **No se ajusta el baseline para que pase el test.** Si el test falla, o el código está mal, o el
  diseño cambió — y si cambió, se re-deriva el baseline **desde Figma**, no a mano.
- **No se marca verde lo que no se corrió.**
- **No se testea lo trivial** por cumplir. Un test por cada línea es mantenimiento sin valor; los tests
  cubren el comportamiento y la fidelidad, no la existencia de código.
- **No se deja el baseline sin versionar**: es el contrato del diseño y tiene que poder revisarse en un
  PR igual que el código.
