# Objetivo 2: SSRF y el Peligro en la Nube (AWS/GCP)

**Consigna:** En infraestructuras Cloud, una vulnerabilidad de **SSRF** suele ser catastrófica. Explicar qué sucede si un atacante encuentra un SSRF en una app alojada en **AWS** y fuerza al servidor a hacer una petición GET a la dirección mágica **169.254.169.254**, y qué información sensible espera extraer.

---

## 1. Qué es SSRF

**SSRF** (Server-Side Request Forgery) es una vulnerabilidad donde el atacante logra que **el servidor haga peticiones HTTP a una URL que el atacante controla**. Ocurre en funcionalidades que toman una URL del usuario y la consultan del lado del servidor: un "diagnóstico remoto", un cargador de imágenes por URL, un generador de PDFs, un webhook, un validador de enlaces, etc.

La clave de por qué es tan grave: las peticiones **salen desde el servidor**, no desde el navegador del atacante. Y el servidor normalmente está **dentro de una red interna** (la nube, la VPC) con acceso a recursos que desde afuera son inalcanzables. El atacante usa al servidor como **trampolín** para llegar a esa red interna.

## 2. La dirección mágica: 169.254.169.254

`169.254.169.254` es una dirección especial (del rango *link-local*) que los proveedores cloud —**AWS**, GCP, Azure— usan para el **servicio de metadatos de la instancia** (*Instance Metadata Service*, IMDS). Cualquier máquina virtual (una EC2 en AWS) puede consultar esa IP **desde dentro de sí misma** para obtener información sobre su propia configuración: su rol, su región, sus datos de arranque... y, lo más crítico, **sus credenciales temporales**.

Puntos clave:
- Solo es accesible **desde la propia instancia** (no desde internet). Por eso el SSRF es el vehículo perfecto: le pide al servidor vulnerable —que SÍ está dentro de la instancia— que la consulte por el atacante.
- No requiere autenticación: históricamente, cualquier proceso dentro de la máquina podía leerla con un simple `GET`.

## 3. Qué extrae el atacante (el premio: las credenciales del rol IAM)

En AWS, a las instancias EC2 se les asigna un **rol IAM** para que las apps accedan a otros servicios (S3, bases de datos, etc.) sin credenciales hardcodeadas. Esas credenciales **viven en el servicio de metadatos** y se renuevan solas. El flujo del ataque:

1. El atacante fuerza (vía SSRF) al servidor a pedir la **lista de roles**:
   ```
   GET http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```
   Respuesta: el nombre del rol, ej. `mi-rol-ec2`.

2. Luego pide las **credenciales de ese rol**:
   ```
   GET http://169.254.169.254/latest/meta-data/iam/security-credentials/mi-rol-ec2
   ```
   Respuesta (JSON):
   ```json
   {
     "AccessKeyId": "ASIA...",
     "SecretAccessKey": "wJalr...",
     "Token": "FQoGZXIvYXdz...",
     "Expiration": "2026-11-26T22:00:00Z"
   }
   ```

Con ese **AccessKeyId + SecretAccessKey + Token**, el atacante tiene las **llaves de la cuenta de AWS con los permisos de ese rol**. Desde su propia máquina, configura esas credenciales en el AWS CLI y **actúa como el servidor**: según los permisos del rol, puede listar y descargar **buckets S3** (datos de clientes, backups), leer bases de datos, lanzar o borrar instancias, acceder a secretos, etc. De un SSRF "inofensivo" se pasa a un **compromiso potencial de toda la infraestructura cloud**. Por eso se dice que el SSRF en la nube es catastrófico.

### Otros datos del metadata (además de las credenciales)

- **User-data** (`/latest/user-data`): el script de arranque de la instancia, que a veces contiene **secretos, contraseñas o tokens** hardcodeados por error.
- Datos de red, región, ID de la instancia, security groups → útiles para mapear la red interna y seguir pivotando.

## 4. Cómo se evade el filtro (contexto de los labs del curso)

Muchas apps intentan frenar el SSRF con una **lista negra** de IPs internas. Esos filtros suelen ser débiles y se evaden:
- IP en **decimal**: `169.254.169.254` = `2852039166`.
- IP en **hexadecimal/octal**, con ceros a la izquierda, o IPv6.
- Usando un **nombre de host** que resuelve a la IP interna (muchos filtros bloquean literales de IP pero no hostnames — esto fue justo lo que resolvió el lab de Helios Energy en este curso).
- Redirecciones: una URL del atacante que responde con un `302` hacia `169.254.169.254`.

## 5. Mitigaciones

- **IMDSv2 (en AWS):** la versión 2 del servicio de metadatos exige obtener primero un **token con una petición `PUT`** (con una cabecera especial) antes de poder leer nada con `GET`. Como un SSRF típico solo puede hacer `GET` simples, IMDSv2 lo frena. **Es la mitigación principal: forzar IMDSv2.**
- **Validación estricta de la URL del lado servidor:** lista blanca de destinos permitidos (no lista negra), resolver el hostname y verificar que **no** apunte a rangos internos/privados (incluida `169.254.169.254`), y bloquear redirecciones.
- **Segmentación de red / egress:** impedir que el servidor de la app alcance el endpoint de metadatos o la red interna salvo lo estrictamente necesario.
- **Principio de menor privilegio en el rol IAM:** si el rol tiene permisos mínimos, el robo de sus credenciales hace mucho menos daño.

## 6. Conclusión

Un SSRF en la nube es catastrófico porque convierte al servidor vulnerable en un **proxy hacia la red interna de AWS**, y ahí vive el endpoint de metadatos **169.254.169.254**. Forzando una simple petición `GET` a esa dirección, el atacante extrae las **credenciales temporales del rol IAM de la instancia** (AccessKey, SecretKey y Token), con las que pasa a operar como la propia aplicación en la cuenta de AWS — accediendo a S3, bases de datos y más, según los permisos del rol. Lo que empieza como "el servidor consulta una URL que yo le doy" termina, sin mitigaciones como IMDSv2, en el **compromiso de la infraestructura cloud completa**.
