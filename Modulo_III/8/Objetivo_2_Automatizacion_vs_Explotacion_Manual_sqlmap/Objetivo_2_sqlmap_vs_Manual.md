# Objetivo 2: Automatización vs Explotación Manual (sqlmap)

**Consigna:** sqlmap es la herramienta de explotación de inyecciones SQL más potente, pero depender exclusivamente de ella es un error. Enumerar y explicar al menos dos escenarios reales donde **sqlmap fallaría**, pero un atacante **manual** (manipulando la petición en Burp) sí lograría explotar la vulnerabilidad.

---

## 1. Por qué sqlmap no es infalible

sqlmap es excelente **automatizando** la detección y explotación de inyecciones en casos "estándar": toma un parámetro, le prueba cientos de payloads, identifica el motor, y extrae datos. Pero trabaja con **patrones y heurísticas genéricas**. Cuando la vulnerabilidad requiere **entender el contexto de la aplicación**, encadenar pasos propios del negocio, o construir un payload a medida que no encaja en sus plantillas, sqlmap se queda corto. Ahí es donde un humano con Burp gana: entiende *qué* hace la petición y puede improvisar.

A continuación, escenarios concretos donde sqlmap falla y el enfoque manual funciona.

## 2. Escenario 1 — La inyección depende de un flujo multi-paso o de un valor pre-procesado

**El caso:** El parámetro vulnerable no se envía "crudo" en una sola petición, sino que forma parte de un **flujo de varias peticiones** o depende de un valor que la propia aplicación genera y valida antes.

Ejemplos reales:
- El dato inyectable viaja en el **segundo paso** de un asistente (wizard) de varios pasos, y para llegar ahí hay que completar y enviar correctamente el paso anterior, manteniendo el estado de la sesión.
- El valor debe ir **firmado, cifrado o codificado** de una forma particular (ej. un ID que la app espera en base64, o un token CSRF que cambia en cada request y hay que extraer de la respuesta anterior).
- El parámetro se usa recién **en una segunda consulta diferida** (second-order SQLi): se guarda en la base en un paso, y se vuelve peligroso cuando otra funcionalidad lo lee y lo concatena en *otra* consulta más tarde.

**Por qué sqlmap falla:** sqlmap, por defecto, bombardea **un solo endpoint** con payloads esperando una respuesta inmediata. No sabe navegar un flujo de negocio de varios pasos, ni que tiene que inyectar en el paso A para que el efecto aparezca en el paso B (second-order), ni cómo re-generar un token dinámico para cada intento. Aunque tiene mecanismos avanzados (scripts `--eval`, manejo de CSRF con `--csrf-token`), configurarlos requiere **entender el flujo primero** — y muchas veces el caso es demasiado específico para encajarlo.

**Por qué el manual funciona:** el pentester **entiende la lógica de la aplicación**: completa el flujo a mano en Burp, identifica exactamente dónde y cómo se procesa el dato, extrae el token dinámico de cada respuesta, y coloca el payload en el punto correcto (o en la funcionalidad que lo *lee* después, en el caso second-order). Es un razonamiento contextual que la automatización ciega no hace.

## 3. Escenario 2 — Defensas/filtros no estándar o contexto de inyección inusual (WAF + sintaxis específica)

**El caso:** Hay un **WAF** o un filtro de entrada que bloquea los payloads "de catálogo", o el punto de inyección está en un **contexto sintáctico raro** que requiere un payload armado a mano.

Ejemplos reales:
- Un **WAF** bloquea las firmas típicas de sqlmap (su User-Agent, sus payloads conocidos, palabras como `UNION SELECT`), pero se evade con una ofuscación **muy específica de esa app** (comentarios intercalados, codificaciones mixtas, mayúsculas/minúsculas alternadas, funciones equivalentes) que hay que descubrir probando a mano qué pasa y qué no.
- La inyección está dentro de una **cláusula poco común** (`ORDER BY`, `LIMIT`, nombres de columna/tabla, un `INSERT`), donde las comillas no aplican y los payloads estándar de sqlmap no encajan; hay que construir la sintaxis exacta para ese contexto.
- El punto de inyección vive en un **formato que sqlmap no parsea bien** por defecto: dentro de un JSON anidado, de un XML, de una cabecera HTTP no convencional, o en un valor que la app descompone de una forma particular.

**Por qué sqlmap falla:** sus payloads son **plantillas**. Si el WAF conoce esas plantillas, las corta todas y sqlmap reporta "no es inyectable" (falso negativo). Y para contextos sintácticos raros, sqlmap asume estructuras comunes (`param=valor` con comillas) que no coinciden con, por ejemplo, un `ORDER BY` inyectable, así que ni detecta la vulnerabilidad.

**Por qué el manual funciona:** el atacante **observa el comportamiento** (qué devuelve el WAF, qué carácter rompe la query, qué error sutil aparece) y **diseña un payload a medida**: prueba la sintaxis exacta que necesita el contexto, encuentra la evasión puntual que ese WAF no filtra, y ajusta carácter por carácter en Burp Repeater hasta lograr la ejecución. Es creatividad y adaptación en tiempo real, no una lista fija de intentos.

## 4. (Mención) Otros casos donde el manual gana

- **Detección de la vulnerabilidad en primer lugar:** muchas veces sqlmap ni siquiera *encuentra* el punto porque está en un parámetro que no probó, o requiere un valor válido previo. El humano lo descubre explorando.
- **Rate limiting / bloqueo por volumen:** sqlmap hace miles de peticiones y dispara defensas (bloqueo de IP, captchas). Un ataque manual, quirúrgico, con pocas peticiones bien pensadas, pasa desapercibido.
- **Lógica de negocio combinada:** cuando la SQLi es solo un eslabón de una cadena (ej. extraer un dato que luego se usa en otro ataque), sqlmap no "razona" la cadena completa.

## 5. Conclusión

sqlmap es una herramienta potentísima para **escalar y acelerar** la explotación una vez que el caso es claro y estándar. Pero depende de patrones predefinidos y de un contexto "de manual". Cuando la vulnerabilidad vive en un **flujo multi-paso**, en una **inyección de segundo orden**, detrás de un **WAF con filtros específicos** o en un **contexto sintáctico inusual**, la automatización fracasa por falta de comprensión contextual. El atacante manual con Burp aporta lo que sqlmap no tiene: **entender la aplicación, observar su comportamiento y construir el payload exacto**. Lo profesional es usar ambos — sqlmap para lo repetitivo y masivo, y el criterio manual para lo que requiere cabeza.
