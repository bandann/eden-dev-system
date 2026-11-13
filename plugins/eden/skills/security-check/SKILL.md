---
name: security-check
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:security-check` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable
  de seguridad, de tokens o de vulnerabilidades, ni porque el trabajo parezca terminado: si no lo pidió
  por su nombre, no se usa. — Qué hace cuando SÍ se invoca: audita la seguridad de una tarea (el diff de
  la rama contra su base), de una sección o del proyecto entero. Declara la superficie de amenazas,
  corre los escáneres que haya instalados (gitleaks, semgrep, osv-scanner, npm/composer audit), lee el
  código contra el checklist de 12 áreas y reporta por severidad con archivo:línea, cómo se explota y
  cómo se arregla. Tras presentar el reporte puede aplicar los arreglos seguros, solo con el sí del dev.
  No commitea ni pushea.
argument-hint: "[diff | section {nombre} | project | secrets | deps] [| ruta]"
disable-model-invocation: true
---

## Security Check — auditoría de seguridad bajo demanda

Argumento recibido: `$ARGUMENTS`

Una sola pregunta: **¿hay algo en esto que alguien pueda explotar, y qué hay que hacer al respecto?**

El contrato es `rules/eden-security-rules.md` (principios, checklist, severidades, herramientas) más la
sección **Seguridad** del módulo del stack. Este skill no los repite: los aplica.

> **Idioma:** al dev, en español. Los arreglos (código, comentarios) en inglés.

**Modelos:** la auditoría la hace un agente (nivel `fast`) (rol `security-auditor`); la sesión principal decide
el alcance, **verifica los hallazgos** y presenta el reporte. Ver `rules/eden-model-strategy-rules.md`.
El agente se resuelve por rol con el roster del stack del proyecto (`teams/{stack}/roster.md`, ver
`rules/eden-team-rules.md`); si el stack no tiene roster, `teams/_generic/roster.md`.

---

### Paso 1 — Modo y alcance

| Modo | Qué audita | Cuándo |
|---|---|---|
| `diff` (por defecto) | La rama actual contra su base | Antes de cerrar una tarea |
| `section {nombre}` | Los archivos de esa sección y sus consumidores directos | Una sección puntual |
| `project` | Auditoría completa: código, **historial de git** (secretos), dependencias, configuración | Onboarding, auditoría periódica, antes de publicar |
| `secrets` | Solo secretos, **incluido el historial** (`gitleaks detect`) | Sospecha de una fuga |
| `deps` | Solo dependencias (`osv-scanner`, `npm audit`, `composer audit`) | Revisión de librerías |

`| ruta` restringe el alcance a una carpeta.

- **Modo `diff` con base desconocida:** la rama base **siempre se pregunta**, nunca se asume. Si el
  checkpoint ya la registra, se confirma en una línea.
- Sin argumento, se asume `diff` y se dice.
- El stack se lee de `project-config.json` o del `CLAUDE.md` (`rules/eden-stack-rules.md`). Si es
  ambiguo, se pregunta.

---

### Paso 2 — Delegar la auditoría

Lanza el rol **`security-auditor`** con el encargo de cinco partes
(`rules/eden-model-strategy-rules.md`):

```
Qué:        Auditar la seguridad de {alcance} y reportar con severidad.
Dónde:      {rama vs base | archivos de la sección | proyecto} — solo lectura.
Con qué:    rules/eden-security-rules.md + módulo del stack. Superficie declarada en el plan, si la hay.
            Modo: {diff|section|project|secrets|deps}. Escáneres: los que haya instalados.
Acepta:     Reporte en el formato del agente; cada hallazgo con archivo:línea, cómo explotarlo y arreglo.
NO hacer:   Editar archivos, atacar nada en vivo ni de terceros, imprimir secretos completos,
            marcar verificado lo que no se corrió.
```

La lectura grande va **siempre** al agente (`rules/eden-context-rules.md`): la sesión principal recibe el
reporte, no el volcado de archivos ni la salida cruda de los escáneres. Si el proyecto tiene grafo,
`graphify affected` puede ayudar a acotar consumidores; se suma al grep, no lo sustituye.

Modos de solo escaneo:

- `secrets` → `gitleaks detect --source . --redact --no-banner` (historial incluido).
- `deps` → `osv-scanner scan source -r .` + `npm audit --omit=dev` / `composer audit` según haya lockfile.

Si una herramienta no está instalada, **se dice** y la cubre la lectura del código; nunca se instala
nada sin preguntar al dev.

---

### Paso 3 — Verificar y presentar

**Un hallazgo es una afirmación, no una verificación.** Antes de presentarlo, la sesión principal:

- Abre el `archivo:línea` y confirma que existe y que el escenario de explotación se sostiene.
- Descarta falsos positivos y lo dice (`descartado: {motivo}`).
- Comprueba que la severidad corresponde a la tabla de `eden-security-rules.md`.

```
🛡️ SECURITY CHECK — {modo} · {alcance}

Stack: {stack} · Base: {rama base} · Fecha: {fecha}

| Sev | Área | archivo:línea | Qué pasa | Cómo explotarlo | Arreglo |
|---|---|---|---|---|---|
| 🔴 Crítica | … |
| 🟠 Alta | … |
| 🟡 Media | … |
| ⚪ Baja | … |

Escáneres
  ✅ Ejecutados: {cuáles, con resultado}
  ⚠️ No instalados: {cuáles} → {qué quedó sin verificar}

Descartados: {falsos positivos y por qué} | ninguno
No verificado: {qué y por qué} | nada

Veredicto: 🛡️ BLOQUEA ({n} críticos/altos) | 🛡️ PASA ({n} medios, {n} bajos)
```

**Semántica de la puerta** (la aplica `turnoff-task`):

- **Críticos y altos bloquean la entrega.**
- Medios y bajos se reportan y los medios quedan escritos en el PR.
- **Una excepción a un bloqueo la decide solo el dev**, de forma explícita y en el momento. Queda escrita
  en el PR, en una sección **Security exceptions**, con el hallazgo, el motivo y quién la aceptó. Este
  skill nunca la concede por su cuenta.

---

### Paso 4 — Arreglar, solo con el sí del dev

Tras el reporte, se ofrece corregir. Nada se toca sin un sí explícito.

1. **Arreglos locales y seguros** (escapar una salida, quitar un `innerHTML`, añadir `rel="noopener"`,
   mover un secreto a una variable de entorno): se proponen con el diff y, con el sí, los aplica el rol
   `implementer` con un encargo cerrado (archivos exactos, criterio de aceptación). Después se vuelve a
   auditar lo tocado: **medir → corregir → medir**.
2. **Código compartido** (un snippet, bloque o función con más consumidores): se mide el blast radius
   primero (`grep` + `graphify affected` si hay grafo; en WordPress, también `wp db search`) y se le
   presenta al dev antes de tocar nada.
3. **Secretos encontrados — incluido el historial:**
   - Un secreto que llegó a un commit **está comprometido aunque se borre**. Se explica que hay que
     **rotarlo** (revocar y emitir uno nuevo en el servicio de origen); quitarlo del código no basta.
     La rotación la hace el dev.
   - El arreglo del código: sacarlo a variable de entorno o al gestor de la plataforma.
   - **Nunca se reescribe el historial** (`git filter-repo`, `rebase`, force-push) sin autorización
     explícita del dev en el momento: afecta a todo el equipo y a las ramas compartidas.
4. **Dependencias:** actualizar o fijar una versión se propone y se confirma; nunca se añade una
   dependencia nueva sin preguntar.
5. **Lo que no se puede arreglar aquí** (una app de terceros, una decisión de negocio, una cabecera que la
   plataforma no deja configurar) se declara tal cual, con el riesgo residual.

**Este skill no commitea, no pushea y no abre PRs.** Los arreglos quedan en la rama sin commitear; los
cierra `turnoff-task`.

---

### Lo que NO hace

- No ataca nada: ninguna prueba de intrusión ni escaneo activo contra tiendas, sitios o servicios en vivo
  o de terceros. Solo código, entorno local o de pruebas.
- No instala herramientas, no sube secretos a ningún sitio y no los repite completos en el reporte.
- No presenta como verificado lo que no se corrió: si falta un escáner, el reporte lo dice.
- No suaviza una severidad para que el veredicto pase.
