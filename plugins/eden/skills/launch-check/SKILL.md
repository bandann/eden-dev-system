---
name: launch-check
description: >
  SOLO POR INVOCACIÓN EXPLÍCITA — NO LO ACTIVES POR TU CUENTA. Este skill se usa únicamente cuando el
  dev escribe `/eden:launch-check` o lo pide de forma explícita e inequívoca. NO lo actives porque se hable
  de lanzar, desplegar o de que el cliente aprobó: si no lo pidió por su nombre, no se usa. — Qué hace
  cuando SÍ se invoca: recorre el checklist de lanzamiento (P9) antes y después del deploy a producción
  —verificación previa, spot-check post-deploy de las páginas críticas, analytics y tracking en
  producción, y el plan de monitoreo de 24–48h—, y deja preparado el seguimiento de la garantía de 30
  días (P10). Verifica y reporta; el deploy y la autorización son del dev.
argument-hint: "[url de producción] [| pre | post]"
disable-model-invocation: true
---

## Launch Check — lanzamiento (P9) y garantía (P10)

Argumento recibido: `$ARGUMENTS`

El lanzamiento es el único momento donde un error no se queda en staging. Este skill recorre lo que hay
que verificar **antes** y **después** del deploy.

> **Idioma:** al dev, en español. Lo que quede escrito (comentarios del tracker, tareas), en inglés.

**Antes que nada:** el manual exige **sign-off escrito del cliente** antes de lanzar. Si el dev no
confirma que existe, **no se sigue**: se dice y se espera. No es una formalidad — es lo que separa un
lanzamiento de un incidente.

---

### Paso 1 — Pre-deploy

Nada de esto se marca sin haberlo comprobado:

- [ ] **Sign-off escrito del cliente** — confirmado por el dev.
- [ ] El checklist de handoff completo sobre las páginas que salen (perfil → `qa.md`): siete anchos,
      links, botones, contenido, imágenes.
- [ ] **PageSpeed** en los umbrales del perfil (90+ móvil · 95+ escritorio).
- [ ] Cero errores de consola.
- [ ] Chrome y Safari verificados.
- [ ] Cero lorem ipsum o contenido placeholder en cualquier página que se publique.
- [ ] Las reglas de negocio que declare el perfil (`business_rules`) verificadas en **todos** los
      lugares donde aplican, no solo en la página principal.
- [ ] La rama que va a producción es la correcta y viene por PR revisado — **nunca push directo a
      `main`**, y el PR a producción requiere **autorización explícita del dev en el momento**.
- [ ] **Seguridad: `/eden:security-check project`** completo (`rules/eden-security-rules.md`): secretos en el
      historial de git, dependencias con vulnerabilidades, cabeceras/CSP donde la plataforma lo permita
      e inventario de scripts de terceros (origen, versión, SRI). **Críticos y altos bloquean la
      recomendación de lanzar**; solo el dev puede aceptar una excepción, y queda escrita. Lo que no se
      pudo verificar (herramienta ausente) se declara.

Si algo falla, se dice **antes** del deploy, no después.

---

### Paso 2 — El deploy lo hace el dev

El kit no despliega a producción. Prepara, verifica y reporta; **la acción de publicar es del dev**.

---

### Paso 3 — Spot-check post-deploy

Sobre **producción**, no sobre staging. Las páginas críticas, una por una:

- [ ] **Home**
- [ ] Una **página de colección**
- [ ] Un **PDP**
- [ ] **Checkout** — flujo completo hasta el punto de pago
- [ ] **Formulario de contacto** — enviado de verdad

Y en cada una: carga correcta, sin errores de consola, imágenes cargando, links vivos.

---

### Paso 4 — Analytics y tracking

Lo que más se descubre tarde, porque en staging no está:

- [ ] **Google Analytics** disparando en producción
- [ ] **Meta Pixel** y cualquier otro píxel del cliente
- [ ] Eventos de e-commerce (view_item, add_to_cart, purchase) si el proyecto los implementa
- [ ] Herramientas de terceros del cliente conectadas

**Verificado en producción**, no "debería funcionar porque está el script".

---

### Paso 5 — Monitoreo 24–48 h

Prepara el seguimiento y díselo al dev:

- Qué revisar: incidencias reportadas por el cliente, logs de error, caídas de conversión.
- Cuándo: a las 24 h y a las 48 h.
- Qué hacer si aparece algo: severidad del perfil — **Critical se arregla el mismo día**.

---

### Paso 6 — Garantía de 30 días (P10)

Desde el lanzamiento, los bugs reportados entran en garantía. Del perfil:

- Se registran con `task.create` como tarea **tipo `Ticket`** (si el tracker distingue tipos), estado
  lógico **`todo`** (`Open` en el perfil), y solo con el sí del dev.
- Aplican las mismas severidades y plazos: Critical mismo día · High 1 día · Medium 2 días · Low
  siguiente sprint.
- **Fecha de fin de garantía: {fecha de lanzamiento + 30 días}** — calcúlala y dísela al dev.

---

### Salida final

```
🚀 LAUNCH CHECK — {proyecto}

Pre-deploy
   Sign-off cliente   {✅ confirmado | ⛔ falta — no se lanza}
   QA handoff         {✅ | lo que falta}
   PageSpeed          móvil {n} · escritorio {n}   {✅ | ⚠️ bajo umbral}
   Consola · Chrome · Safari   {estado}
   Reglas del perfil  {estado}
   Seguridad          críticos {n} · altos {n} (bloquean) · medios {n} · bajos {n}

Post-deploy (producción)
   Home · Colección · PDP · Checkout · Contacto   {✅ cada uno | lo que falló}
   Analytics          GA {✅} · Pixel {✅} · eventos {✅}

Monitoreo   24 h: {fecha/hora} · 48 h: {fecha/hora}
Garantía    hasta {fecha} — bugs como tarea tipo Ticket, estado Open

⚠️ Pendiente: {lo que quedó, o "nada"}
```

**Un checklist marcado sin haberlo corrido es peor que no tenerlo**: aquí lo que no se verificó se
declara como no verificado.
