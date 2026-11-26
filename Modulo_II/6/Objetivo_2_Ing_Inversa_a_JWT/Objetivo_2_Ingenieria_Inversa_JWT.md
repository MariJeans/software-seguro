# Objetivo 2: Ingeniería Inversa a JSON Web Tokens (JWT)

**Plataforma de origen del token:** Software Seguro (softwareseguro.com.ar) — lab "Notas Universitarias", entorno de práctica del curso de Ciberseguridad Web / Ethical Hacking.

---

## 1. JWT interceptado

Token obtenido durante la resolución del lab "Notas Universitarias" (entregado como parte del enunciado, simulando un token filtrado por un infoStealer):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6NDg2NjEyODQwOCwiaWF0IjoxNzQ0MDY0NDA4LCJqdGkiOiJhOTNmMmMxYWI0OTY0NGJiODY1OWMwOTI3ZmQwYmM1NCIsInVzZXJfaWQiOjM2fQ.MienEEx2ZuN-xdFj7Qti8HYXILlqZmVfjMhC-Hun_tw
```

## 2. Estructura técnica de un JWT

Un JWT se compone de **tres segmentos separados por puntos (`.`)**, cada uno codificado en **Base64URL** (no cifrado):

```
HEADER.PAYLOAD.SIGNATURE
```

- **Header:** metadata sobre el algoritmo de firma y el tipo de token.
- **Payload:** los datos ("claims") que transporta el token.
- **Signature:** firma criptográfica que permite verificar integridad y autenticidad, calculada sobre `base64url(header) + "." + base64url(payload)` con una clave o par de claves.

**Punto clave:** Base64URL **no es cifrado**, es solo una codificación reversible. Cualquiera que intercepte un JWT puede decodificar el header y el payload sin necesitar ninguna clave — lo único que protege la firma es la integridad (que nadie lo modifique sin ser detectado), no la confidencialidad del contenido.

## 3. Proceso de decodificación

Se decodificó manualmente con Python, sin herramientas externas, separando el token por sus puntos y aplicando `base64.urlsafe_b64decode` a cada segmento (agregando el padding `=` que Base64URL omite):

```python
import base64, json

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6NDg2NjEyODQwOCwiaWF0IjoxNzQ0MDY0NDA4LCJqdGkiOiJhOTNmMmMxYWI0OTY0NGJiODY1OWMwOTI3ZmQwYmM1NCIsInVzZXJfaWQiOjM2fQ.MienEEx2ZuN-xdFj7Qti8HYXILlqZmVfjMhC-Hun_tw"

header_b64, payload_b64, signature_b64 = jwt.split(".")

def decode(segment):
    # Base64URL omite el padding '='; hay que reponerlo antes de decodificar
    return json.loads(base64.urlsafe_b64decode(segment + "==" * (-len(segment) % 4)))

print("HEADER :", decode(header_b64))
print("PAYLOAD:", decode(payload_b64))
```

(También se puede hacer lo mismo pegando el token en **jwt.io**, que hace exactamente este proceso del lado del cliente, en el navegador — sin enviar el token a ningún servidor. Es seguro para practicar siempre que el token sea de un entorno de pruebas propio, nunca con tokens de sesiones reales de producción.)

## 4. Resultado de la decodificación

### Header

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Algoritmo de firma: `HS256`** (HMAC con SHA-256) — un algoritmo **simétrico**: la misma clave secreta (`SECRET_KEY` del backend) se usa tanto para firmar como para verificar el token. Esto implica que si esa clave se filtra (por ejemplo, por una mala configuración o un endpoint que la expone), cualquiera puede **forjar tokens nuevos y válidos** — fue justamente lo que ocurrió en otro lab de este mismo curso (*Consulta de Multas*), donde una `SECRET_KEY` expuesta en una respuesta JSONP permitió firmar un JWT falso con rol de administrador.

### Payload

```json
{
  "token_type": "refresh",
  "exp": 4866128408,
  "iat": 1744064408,
  "jti": "a93f2c1ab49644bb8659c0927fd0bc54",
  "user_id": 36
}
```

Campos identificados:

| Campo | Significado | ¿Es un dato sensible expuesto en texto plano? |
|---|---|---|
| `token_type` | Indica que es un **refresh token**, no un access token | Informativo — revela el propósito del token |
| `exp` | Timestamp Unix de expiración | No sensible en sí, pero en este caso es un valor anómalo (~año 2124), indicando un token pensado para no expirar nunca |
| `iat` | Timestamp Unix de emisión (*issued at*) | Revela cuándo se generó el token |
| `jti` | JWT ID — identificador único del token, usado por el backend para listas de revocación/blacklist | Identificador interno expuesto |
| `user_id` | **Identificador interno del usuario dueño del token** | **Sí — dato sensible**: permite saber a qué usuario pertenece el token sin autenticarse, y en combinación con otros vectores (como un panel de administración mal protegido) permite dirigir un ataque hacia una cuenta específica |

No incluye en este caso campos como `username`, `email` o `role`/`is_staff` directamente, pero es importante señalar que **muchas implementaciones de JWT sí incluyen ese tipo de datos en el payload** (nombre de usuario, email, rol o permisos), confiando en que "nadie los va a leer" porque el token "parece" un string opaco. Como se demostró en el punto 2, esa confianza es incorrecta: el payload es público para cualquiera que intercepte el token.

## 5. Riesgos identificados

1. **Exposición de identificadores internos** (`user_id`, `jti`) sin necesidad de descifrar nada — solo decodificar Base64URL.
2. **Uso de algoritmo simétrico (HS256):** la seguridad depende enteramente de que el `SECRET_KEY` del servidor nunca se filtre; si se filtra, se puede forjar cualquier token.
3. **Anti-patrón de diseño:** incluir datos sensibles (roles, emails, nombres) en el payload de un JWT sin cifrado adicional, asumiendo que el formato "parece" ilegible.
4. **Tokens con expiración excesivamente larga** (como el `exp` de este caso) amplían la ventana de explotación si el token se filtra, ya que no caduca por sí solo.

## 6. Conclusión

Un JWT **no es un mecanismo de confidencialidad**, es un mecanismo de **integridad y autenticidad** sobre datos que viajan en texto plano (codificados, no cifrados). Cualquier información incluida en el payload debe tratarse como pública desde el momento en que el token sale del servidor. Los datos verdaderamente sensibles (contraseñas, roles críticos, PII) no deberían viajar en el payload de un JWT salvo que exista una capa adicional de cifrado (JWE) sobre el token completo.
