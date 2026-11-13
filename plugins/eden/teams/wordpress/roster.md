# Roster WordPress

Mapea los especialistas WordPress que ya existen a los roles de `rules/eden-team-rules.md`. El líder de
stack (`/eden-wordpress`) todavía no existe: mientras tanto, los skills `wp-*` y los del núcleo hacen de
líder con este roster.

| Rol | Agente | Notas |
|---|---|---|
| `explorer` | `eden:wp-explorer` | Blast radius en código **y** base de datos |
| `architect` | `eden:wp-explorer` | En modo auditoría |
| `design-extractor` | `eden:figma-extractor` | Compartido |
| `design-system` | `eden:wp-implementer` | `theme.json` / globales del builder, según el sabor |
| `implementer` | `eden:wp-implementer` | En el sabor declarado |
| `data` | `eden:wp-implementer` | CPTs, campos, endpoints — en el mu-plugin |
| `devops` | `eden:wp-migrator` | Entorno local |
| `migrator` | `eden:wp-migrator` | Backup y `--dry-run` primero |
| `design-auditor` | `eden:design-auditor` | Compartido |
| `reviewer` | `eden:wp-qa-reviewer` | Escape, sanitize, nonce, capability, contenido publicado |
| `quality-auditor` | `eden:wp-qa-reviewer` | |
| `security-auditor` | `eden:security-auditor` | Auditoría independiente de seguridad; lee el módulo WordPress |

Prohibiciones y convenciones: `rules/wordpress/eden-wordpress-rules.md` y el sabor del proyecto.
