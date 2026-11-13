# Perfiles de operación — Eden

El kit tiene dos capas, y no se mezclan:

| Capa | Qué es | Ejemplo |
|---|---|---|
| **Núcleo** | Cómo trabajamos, sea cual sea el cliente. Agnóstico. Cuando no sabe algo, **pregunta**. | "La rama base siempre se pregunta", reuse-first, medir en vez de estimar |
| **Perfil** | Las verdades concretas de una operación: estados reales, ramas, roles, umbrales, reglas de negocio | `acme-retail`: estados del tracker, ramas, roles, reglas de negocio del cliente |

Un perfil **no cambia cómo piensa el kit**: le da los datos que hoy tendría que preguntar. Por eso un
proyecto sin perfil sigue funcionando igual que siempre.

## Activar un perfil

En el `CLAUDE.md` del proyecto:

```
<!-- eden-profile: acme-retail -->
```

o en `.claude/project-config.json`:

```json
{ "profile": "acme-retail" }
```

Sin marcador, **no hay perfil**: el núcleo actúa con sus defaults y pregunta lo que no sabe.

> **Compatibilidad con marcadores antiguos.** Los proyectos que ya existen pueden traer
> `<!-- fl-profile: x -->`. El kit lo lee como equivalente de `<!-- eden-profile: x -->`, y **propone**
> migrarlo al marcador nuevo — nunca lo reescribe en silencio.

## Precedencia — la regla que evita choques

Cuando dos fuentes dicen cosas distintas, gana la de arriba:

1. **Lo que el dev dice en el momento.** Siempre. Un perfil nunca pisa una instrucción directa.
2. **El `CLAUDE.md` / `project-config.json` del proyecto.** Un proyecto puede desviarse de su perfil;
   el proyecto manda sobre el perfil.
3. **El perfil activo.**
4. **La config global del dev** (`~/.claude/eden-config.json`: `company`, `tracker`).
5. **El default del núcleo.**

## Qué hacer cuando algo se sale del perfil

Esta es la parte importante. Un perfil describe la operación **habitual**, no todo lo que puede pasar.

- **El trabajo nunca se bloquea por no estar cubierto.** Si el perfil no dice nada sobre la situación,
  se aplica el default del núcleo y **se declara en una línea**:
  > `↪ Esto no lo cubre el perfil acme-retail; sigo el default del kit y te aviso.`
- **Si el perfil y la realidad se contradicen** (el perfil dice que las ramas son
  `development/staging/main` y el repo no las tiene), **gana la realidad**: se reporta la discrepancia y
  se pregunta. Un perfil desactualizado no es una orden.
- **Si el dev pide algo que el perfil prohíbe**, se le dice qué dice el perfil **en una línea**, y se
  hace lo que pidió. Él conoce su excepción; el kit no discute.
- Las excepciones repetidas son señal de que el perfil está desactualizado: se anota para revisarlo,
  no se convierte en costumbre silenciosa.

## Qué NO va en un perfil

- Reglas de calidad universales (accesibilidad, performance, semántica): esas son del núcleo.
- Decisiones que le corresponden al dev.
- Credenciales, tokens o secretos. **Nunca.**

## Datos sensibles

Un perfil puede contener ids de workspace, listas y personas — es lo que lo hace útil. Eso significa que
**el perfil es interno**: no se publica fuera de la organización a la que pertenece. Si un perfil se
comparte, se revisa antes qué contiene.

## Perfiles disponibles

El kit trae `profiles/_template/`; cada empresa crea su propio perfil a partir de esa plantilla (es
interno y nunca se publica).

Un perfil vive en `profiles/{nombre}/` con un `profile.json` (los datos) y los `.md` que documentan sus
reglas.
