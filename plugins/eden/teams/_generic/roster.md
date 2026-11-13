# Roster genérico — cualquier stack sin roster propio

Es el equipo por defecto. Lo usa cualquier stack que no tenga `teams/{stack}/roster.md`, y cualquier
rol que el roster de un stack no cubra. Ver `rules/eden-team-rules.md`.

| Rol | Agente | Notas |
|---|---|---|
| `explorer` | `eden:explorer` | |
| `architect` | `eden:explorer` | En modo auditoría: convenciones, deuda y riesgos |
| `design-extractor` | `eden:figma-extractor` | Compartido por todos los stacks |
| `design-system` | `eden:implementer` | Con el encargo de `create-fundaments` |
| `implementer` | `eden:implementer` | |
| `data` | `eden:implementer` | |
| `tester` | `eden:implementer` | Con el encargo de escribir solo los tests (test-first) |
| `devops` | — | Lo hace la sesión principal o el dev |
| `design-auditor` | `eden:design-auditor` | Compartido por todos los stacks |
| `reviewer` | `eden:qa-reviewer` | |
| `quality-auditor` | `eden:qa-reviewer` | Con el foco en performance, accesibilidad y SEO |
| `security-auditor` | `eden:security-auditor` | Un solo agente para todos los stacks; lee el módulo de seguridad del stack |
| `migrator` | — | Lo hace la sesión principal o el dev |

Líder: **no hay**. Sin líder de stack, los skills del núcleo (`ignition-task`, `section-mod`, …) hacen
de líder con este roster.
