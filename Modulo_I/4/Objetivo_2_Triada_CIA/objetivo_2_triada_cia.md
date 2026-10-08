# Objetivo 2: Análisis de la Triada CIA

## Los tres pilares con mis palabras

**Confidencialidad**: que la información solo la pueda ver quien está autorizado a verla. No es solo "que no se filtre hacia afuera" — también incluye que un usuario con un rol no pueda ver datos de otro usuario o de un rol más alto al que no tiene acceso. Es el pilar del "quién puede leer esto".

**Integridad**: que los datos sean exactamente los que deberían ser, sin que nadie los haya modificado, borrado o corrompido sin autorización (ya sea de forma maliciosa o por un error del sistema). No importa tanto quién lo lee, sino que lo que se lee/procesa sea confiable y no haya sido alterado en el camino. Es el pilar del "esto es lo que realmente se guardó/envió".

**Disponibilidad**: que el sistema y los datos estén accesibles cuando quien está autorizado los necesita. De nada sirve tener la info perfectamente confidencial e íntegra si el sistema está caído y nadie puede usarlo. Es el pilar del "esto funciona cuando lo necesito".

## Un ejemplo de vulnerabilidad web por cada pilar

### Confidencialidad → IDOR (Insecure Direct Object Reference)

Un IDOR es cuando una aplicación expone un recurso (por ejemplo `/api/pedidos/1042`) usando un ID predecible o secuencial, y no valida del lado del servidor si el usuario autenticado realmente tiene permiso sobre ese recurso puntual. Si simplemente cambiando el ID en la URL (`1042` → `1043`) puedo ver el pedido de otra persona, estoy rompiendo la confidencialidad: estoy accediendo a datos que no me corresponden, sin necesidad de explotar nada más que cambiar un número.

### Integridad → Mass Assignment / manipulación de parámetros ocultos

Un caso típico es cuando un formulario o una API acepta más campos de los que debería y los aplica sobre el objeto sin validar cuáles están permitidos — por ejemplo, un endpoint de "editar perfil" que en el body también acepta (sin querer) un campo `rol` o `precio`, y si yo como atacante lo agrego a mano en la petición, el servidor lo guarda tal cual. Ahí estoy **modificando datos que no debería poder modificar** (mi propio rol, el precio de un producto, el saldo de una cuenta): es un ataque directo a la integridad de la información, porque el dato guardado ya no refleja lo que el sistema esperaba que fuera válido.

### Disponibilidad → Ataque de Fuerza Bruta / DoS por agotamiento de recursos

Esto lo vimos justo en el objetivo anterior del curso: un ataque de fuerza bruta masivo contra un login (miles de peticiones por Burp Intruder, por ejemplo) no solo busca adivinar una contraseña — si no hay ningún tipo de rate limiting, bloqueo por IP o CAPTCHA, ese volumen de requests puede llegar a saturar el servidor y afectar la disponibilidad para el resto de los usuarios legítimos. Un DoS (Denial of Service) apunta : tirar abajo o degradar el servicio a propósito, sin necesidad de robar ni modificar un solo dato.

