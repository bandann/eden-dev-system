# Plantilla de perfil de operación

Un perfil le da al kit las verdades concretas de **una operación** (una empresa, un equipo o un
vertical): su tracker y sus estados reales, sus ramas, sus roles, sus anchos de QA, sus plazos y sus
reglas de negocio. Sin perfil, el kit usa sus defaults y pregunta lo que no sabe.

## Crear uno

1. Copia esta carpeta a `profiles/{nombre}/` (minúsculas con guiones, p. ej. `acme-retail`).
2. Rellena `profile.json` con lo que tu operación tenga. **Borra lo que no uses**: un campo vacío es
   "el kit usa su default y pregunta".
3. Si el vertical tiene reglas de negocio (campos obligatorios, lugares donde algo debe ocultarse…),
   escríbelas en un `.md` del perfil y apúntalo desde `business_rules`.
4. Actívalo en cada proyecto con `<!-- eden-profile: {nombre} -->` en su `CLAUDE.md`, o con
   `"profile": "{nombre}"` en `.claude/project-config.json`.

## Qué no va en un perfil

Credenciales, tokens o secretos — nunca. Reglas de calidad universales (son del núcleo). Decisiones que
le tocan al dev.

Un perfil contiene ids y personas: es **interno**. Si se comparte, se revisa antes qué contiene.
Precedencia y comportamiento fuera de perfil: `rules/eden-profiles-rules.md`.
