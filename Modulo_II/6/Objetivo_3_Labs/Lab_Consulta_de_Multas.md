# Lab: Consulta de Multas

**Plataforma:** Software Seguro (softwareseguro.com.ar)
**Objetivo del lab:** Ignacio pide ayuda porque no quiere pagar sus multas — el objetivo es escalar privilegios dentro de la aplicación hasta obtener acceso como administrador de multas, sin tener credenciales de ese rol.

---

## 1. Reconocimiento

Se exploró la aplicación con Burp activo, interceptando el tráfico generado por las distintas pantallas (consulta de multas por usuario, perfil, etc.).

Durante la revisión del historial de peticiones (Proxy → HTTP history) se identificó una llamada de tipo **JSONP** — un patrón de API antiguo donde el servidor responde con JavaScript ejecutable en lugar de JSON puro, pensado para evitar restricciones de CORS. En el cuerpo de esa respuesta estaba **expuesta la `SECRET_KEY` de la aplicación**, usada por el backend para firmar los JWT (*Sensitive Data Exposure / Cryptographic Failures — OWASP A02*).

Clave filtrada:
```
123456@pz*+2p(e10(n7891"
```

## 2. Análisis del JWT legítimo

Se decodificó un JWT propio (de Ignacio, usuario de bajo privilegio) para entender la estructura del payload que usa la aplicación:

- Algoritmo: **HS256** (firma simétrica — la misma clave sirve para firmar y verificar).
- Campos relevantes en el payload: `user_id`, `username`, `email`, `orig_iat` (issued-at), `exp` (expiración).

Al ser HS256, **cualquiera que conozca la `SECRET_KEY` puede firmar tokens arbitrarios** que el servidor va a aceptar como legítimos — no hay forma de distinguir un token forjado de uno real si la firma es válida.

## 3. Explotación: forja del JWT de administrador

Se infirió que el usuario administrador de multas podía tener `user_id: 2` (Ignacio, como usuario de prueba, era `user_id: 1`). Se generó un script en Python con la librería **PyJWT** para forjar un token firmado con la `SECRET_KEY` filtrada:

```python
import jwt
import time

SECRET_KEY = '123456@pz*+2p(e10(n7891"'

payload = {
    "user_id": 2,
    "username": "administrador_multas@yopmail.com",
    "email": "administrador_multas@yopmail.com",
    "orig_iat": int(time.time()),
    "exp": int(time.time()) + 3600 * 24  # vigencia amplia para la prueba
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print(token)
```

El token generado se probó en **Burp Repeater**, reemplazando el JWT de Ignacio por el forjado (en el header `Authorization` o en la cookie de sesión, según cómo lo esperaba la app) en una petición a un endpoint de administración de multas.

## 4. Resultado

El servidor aceptó el token forjado como válido (la firma verificaba correctamente contra la `SECRET_KEY` real), concediendo acceso con privilegios de administrador de multas sin haber tenido nunca esas credenciales.

**Flag obtenida:** `e470ca488c867e223fb`

## 5. Clasificación OWASP

| Vulnerabilidad | Categoría OWASP |
|---|---|
| Exposición de la `SECRET_KEY` en una respuesta JSONP | A02 — Cryptographic Failures / Sensitive Data Exposure |
| Forja de JWT válido por conocer la clave de firma | A07 — Identification and Authentication Failures |
| Falta de validación adicional de rol/privilegio más allá de la firma del token | A01 — Broken Access Control |

## 6. Lecciones / notas para el reporte final

- Un JWT firmado con **HS256** es tan seguro como lo sea el secreto de firma: si el secreto se filtra (por el motivo que sea — un endpoint JSONP mal pensado, en este caso), el atacante puede emitir tokens arbitrarios con cualquier rol o identidad.
- El uso de algoritmos **asimétricos (RS256)** para JWT mitiga este riesgo específico, ya que la clave para *verificar* (pública) no sirve para *firmar* (privada).
- Nunca exponer secretos de aplicación en respuestas HTTP, logs, código fuente del frontend, ni en endpoints "legacy" como JSONP que muchas veces quedan fuera del radar de revisiones de seguridad modernas.
