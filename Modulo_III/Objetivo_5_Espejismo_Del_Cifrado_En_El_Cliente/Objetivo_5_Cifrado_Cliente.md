# Objetivo 5: El Espejismo del Cifrado en el Cliente (Frontend Encryption)

**Escenario:** Una aplicación financiera cifra con JavaScript, en el navegador, todo el body de las peticiones POST y los parámetros sensibles antes de enviarlos al backend. Los arquitectos afirman que así es imposible interceptar y manipular los valores con un proxy como Burp, porque "todo viaja encriptado". Se analiza por qué es una falsa sensación de seguridad, dónde está el fallo de diseño y qué pasos daría un atacante para evadirlo.

---

## 1. El fallo fundamental de diseño

La afirmación es falsa por un principio básico: **el cliente es territorio enemigo.** Todo lo que corre en el navegador —el código JavaScript, la clave de cifrado, el algoritmo, el flujo completo— está **bajo el control total del usuario/atacante**, no del servidor.

Si el navegador es capaz de **cifrar** el dato antes de mandarlo, entonces el navegador necesariamente tiene en su poder:

- **El algoritmo de cifrado** (está en el código JS, que se descarga y se puede leer).
- **La clave** (o la forma de derivarla/obtenerla, también en el JS).
- **El dato en claro**, *antes* de cifrarlo (lo escribe el propio usuario).

El atacante **es** el dueño de ese entorno. No tiene que "romper" el cifrado: simplemente usa el mismo mecanismo que la aplicación le entregó. Puede leer el valor en claro antes de que se cifre, o cifrar él mismo un valor manipulado usando exactamente la misma función de la app.

El error conceptual es confundir **cifrado en tránsito** con **integridad/confidencialidad frente al usuario**. El cifrado en el cliente no agrega seguridad real porque las dos puntas del cifrado (el que cifra y el que tiene la clave) están del mismo lado: el del atacante.

### 1.1 Además, es redundante con HTTPS

Si la aplicación ya usa **HTTPS** (obligatorio en una app financiera), los datos **ya viajan cifrados en tránsito** por TLS. El cifrado extra en JavaScript no protege de un "hombre en el medio" en la red —de eso ya se encarga TLS—; solo pretende protegerse del **propio usuario**, que es justamente quien tiene todas las llaves. Es ponerle un candado a una caja y dejar la llave pegada al candado.

### 1.2 Burp no es el único punto de intercepción

Los arquitectos piensan que el problema es Burp interceptando el tráfico de red. Pero el atacante no está obligado a atacar en la red: puede actuar **dentro del navegador**, *antes* de que el dato se cifre y se envíe. Ahí el cifrado todavía no ocurrió (o ya se puede revertir con las herramientas que la app provee).

## 2. Pasos tácticos que realizaría un atacante

### Paso 1 — Leer y entender el código de cifrado

Abrir las **DevTools del navegador** (pestaña *Sources/Depurador*) y buscar la función de JavaScript que cifra el body. Como el JS se ejecuta en el cliente, está disponible para leer, incluso si está minificado u ofuscado (se puede "embellecer"/pretty-print y analizar). Ahí se identifica el algoritmo (ej. AES), la clave y cómo se arma el payload.

### Paso 2 — Interceptar el valor *antes* del cifrado

En lugar de interceptar la petición ya cifrada en Burp, el atacante actúa en el momento previo:

- **Breakpoint en el depurador:** poner un *breakpoint* en la línea donde se llama a la función de cifrado. Cuando la ejecución se detiene ahí, el dato sensible todavía está **en claro** en una variable; se puede leer y **modificar en vivo** (ej. cambiar el monto de la transferencia) y luego dejar que el código continúe y lo cifre ya manipulado.
- **Consola del navegador:** como la función de cifrado es global/accesible, el atacante la invoca a mano desde la consola: `cifrar({"monto": 999999, "cuenta_destino": "..."})`, obtiene el blob cifrado válido, y lo usa.

### Paso 3 — Cifrar su propio payload manipulado

Con el algoritmo y la clave en mano (extraídos del JS), el atacante **reutiliza la misma función de la aplicación** para cifrar cualquier valor que quiera. Arma el JSON malicioso, lo pasa por la función de cifrado de la propia app, y obtiene un payload cifrado que el servidor va a aceptar y descifrar como legítimo, porque está cifrado con la clave correcta.

### Paso 4 — Enviar el payload manipulado

Ahora sí, con el valor malicioso ya cifrado correctamente, lo envía al backend:

- Pegándolo en **Burp Repeater** (reemplazando el body cifrado original por el nuevo), o
- Modificando la variable en el breakpoint y dejando que la app lo mande sola, o
- Haciendo la petición directamente desde la consola (`fetch`) con el payload cifrado por él.

El servidor descifra, ve un payload bien formado y cifrado con su clave, y lo procesa. La "protección" fue completamente evadida.

### Paso 5 (variante) — Hooking de la función

Para manipular todo de forma más cómoda, el atacante puede **sobrescribir (hook)** la función de cifrado desde la consola para que, antes de cifrar, modifique el objeto (o lo loguee en claro). Así cada petición que haga la app se altera automáticamente.

## 3. Dónde reside realmente la seguridad

La conclusión de arquitectura: **toda validación de seguridad y de reglas de negocio debe ocurrir en el servidor**, que es el único entorno que el atacante no controla. El cifrado en el cliente:

- **No reemplaza** a HTTPS (que ya cifra en tránsito).
- **No impide** la manipulación, porque el cliente tiene la clave y el dato en claro.
- A lo sumo, es **ofuscación**: eleva un poco la barrera de esfuerzo, pero no es un control de seguridad real. Confiar en él es *security through obscurity*.

Lo que sí protege de verdad:

- **HTTPS/TLS** para la confidencialidad e integridad en tránsito.
- **Validación estricta del lado del servidor** de todos los valores, asumiendo que el cliente pudo haberlos manipulado.
- **Firma/integridad de extremo a extremo con claves que el cliente no posee** cuando hace falta (ej. el servidor firma, no el navegador).
- Para datos sensibles de verdad, controles como autenticación fuerte, autorización por recurso y límites de negocio, siempre verificados en el backend.

## 4. Conclusión

Cifrar en el navegador para "que Burp no pueda manipular los datos" es un **espejismo**: traslada la llave al mismo lado que el atacante. El fallo de diseño es creer que el cliente puede guardar un secreto o imponer una restricción cuando el usuario controla todo el entorno de ejecución. Un atacante no rompe el cifrado: lo **usa** —leyendo el dato antes de cifrarlo o cifrando su propio payload con la misma función— y manipula los valores igual que sin cifrado. La seguridad no se construye escondiendo la llave debajo del felpudo del cliente, sino validando y autorizando **siempre en el servidor**.
