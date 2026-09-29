# Objetivo 3: Profundización Técnica — El "Handshake" TLS

## Contexto: ¿por qué hace falta esto?

HTTP viaja en texto plano: cualquiera que intercepte el tráfico entre el navegador y el servidor puede leer (o modificar) lo que se envía. HTTPS es HTTP corriendo sobre una capa de seguridad llamada **TLS** (Transport Layer Security), que se ubica entre TCP y HTTP. Antes de que el navegador mande la primera petición HTTP, cliente y servidor tienen que negociar esa capa segura — a ese proceso de negociación se lo llama **TLS Handshake**.

## ¿Qué es y cómo funciona el TLS Handshake?

El handshake es el intercambio de mensajes previo a cualquier dato HTTP, donde cliente y servidor se ponen de acuerdo en tres cosas:

1. Qué versión de TLS y qué algoritmos de cifrado van a usar.
2. Confirmar que el servidor es quien dice ser (autenticación).
3. Generar una clave secreta compartida para cifrar todo lo que viaje después.

Estos son los pasos (versión clásica, TLS 1.2, la más fácil de seguir conceptualmente):

1. **Client Hello:** el navegador le manda al servidor las versiones de TLS que soporta, la lista de cifrados (cipher suites) que puede usar, y un número random generado en el momento (*client random*).
2. **Server Hello:** el servidor elige una versión de TLS y un cipher suite de los que le ofrecieron, genera su propio número random (*server random*), y le manda al cliente su **certificado digital** (que contiene su clave pública).
3. **Verificación del certificado:** el navegador valida ese certificado contra una Autoridad Certificadora (CA) de confianza — chequea que la cadena de confianza sea válida, que no esté vencido, que corresponda al dominio al que se está conectando, y que no esté revocado.
4. **Intercambio de claves:** el cliente genera un valor llamado *pre-master secret*, lo cifra con la clave pública del servidor (acá entra el cifrado asimétrico) y se lo manda. Solo el servidor puede descifrarlo, porque es el único que tiene la clave privada correspondiente. Con ese *pre-master secret* más los dos randoms anteriores, ambos lados calculan — cada uno por su cuenta, sin volver a transmitirla — la misma clave de sesión simétrica.
5. **Finished:** ambos lados mandan un mensaje avisando que a partir de ahí todo va cifrado con la clave simétrica recién acordada, y un mensaje "Finished" cifrado que sirve para confirmar que nadie alteró el handshake en el camino.

De ahí en adelante, toda la conversación HTTP real viaja cifrada con esa clave simétrica.


## ¿Qué rol juegan los certificados digitales?

El certificado es un documento firmado digitalmente por una Autoridad Certificadora (CA) que vincula una clave pública con una identidad — en la práctica, con un dominio. Contiene: el nombre de dominio, la clave pública del servidor, quién lo emitió, fechas de validez, y la firma digital de la CA.

El problema que resuelve es el de la identidad: sin certificado, cualquiera podría entregarme una clave pública diciendo "soy tubanco.com", y no tendría forma de comprobarlo. Sin esa verificación, el cifrado por sí solo no evita un ataque de tipo Man-in-the-Middle: alguien podría interceptar la conexión y hacerse pasar por el servidor real, cifrando todo con su propia clave. El certificado es la pieza que impide eso.

## ¿Por qué se usan dos tipos de cifrado distintos en la misma conexión?

Porque cada uno resuelve un problema diferente:

- **Cifrado asimétrico** (par de clave pública/privada): permite que dos partes que nunca se comunicaron antes puedan intercambiar información de forma segura por un canal que podría estar siendo espiado. Es la única forma de resolver el problema inicial ("¿cómo nos ponemos de acuerdo en un secreto sin haber compartido nada antes?"). El costo es que es computacionalmente pesado y lento si se usara para cifrar todo el tráfico.
- **Cifrado simétrico** (una sola clave compartida, ej. AES): es mucho más rápido y liviano, ideal para cifrar el volumen real de datos que viaja durante toda la sesión HTTP. El problema es que ambas partes ya necesitan tener la misma clave de antemano — y ese es exactamente el problema que el paso asimétrico acaba de resolver.

Por eso se combinan: el cifrado asimétrico se usa una sola vez, durante el handshake, para autenticar al servidor y acordar de forma segura una clave simétrica. Una vez que esa clave existe en ambos lados, toda la conversación real pasa a cifrado simétrico, que es mucho mejor para mover grandes volúmenes de tráfico. Es un esquema híbrido: seguridad en el intercambio inicial, performance en la comunicación real.