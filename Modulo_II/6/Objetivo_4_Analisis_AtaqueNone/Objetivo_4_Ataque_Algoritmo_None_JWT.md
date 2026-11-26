# Objetivo 4: Análisis del Ataque de Algoritmo "None" en JWT

**Tema:** Por qué un backend que acepta el algoritmo `none` permite a un atacante falsificar cualquier identidad sin conocer la clave secreta del servidor.

---

## 1. Repaso: cómo se valida normalmente un JWT

Un JWT tiene tres partes separadas por puntos, cada una en Base64URL:

```
HEADER . PAYLOAD . SIGNATURE
```

- **Header:** incluye el algoritmo de firma, ej. `{"alg": "HS256", "typ": "JWT"}`.
- **Payload:** los datos/claims, ej. `{"user_id": 1, "role": "admin"}`.
- **Signature:** la firma criptográfica.

En un flujo seguro con **HS256** (simétrico), el servidor, al recibir el token, recalcula la firma así:

```
firma_esperada = HMAC_SHA256( base64url(header) + "." + base64url(payload), SECRET_KEY )
```

y la compara con la firma que viene en el token. Si no coinciden → token rechazado. **La integridad del payload (que nadie cambió el `role` o el `user_id`) depende enteramente de que el atacante no pueda producir una firma válida, porque no conoce la `SECRET_KEY`.**

Esto lo vimos en la práctica en el lab *Consulta de Multas*: cuando la `SECRET_KEY` se filtró, se pudo forjar un token válido. El ataque `none` logra lo mismo **pero sin siquiera necesitar la clave.**

## 2. Qué es el algoritmo "none"

El estándar JWT (RFC 7519 / JWA RFC 7518) define un algoritmo especial llamado **`none`**, pensado para casos donde el token viaja por un canal que ya garantiza integridad por otros medios (un "Unsecured JWS"). Un token con `alg: none` tiene esta forma:

```
HEADER . PAYLOAD .
```

- Header: `{"alg": "none", "typ": "JWT"}`
- Payload: los claims que el atacante quiera.
- **Signature: VACÍA** (no hay nada después del último punto).

Es decir, `none` significa literalmente "este token no está firmado".

## 3. La vulnerabilidad: por qué permite falsificar cualquier identidad

El problema aparece cuando el backend **decide qué algoritmo usar para verificar leyéndolo del propio header del token** (que es controlado por el atacante) en lugar de imponer el algoritmo esperado desde el código del servidor.

Un backend vulnerable hace algo conceptualmente así:

```python
# VULNERABLE: confía en el 'alg' que viene en el token
header = leer_header(token)
algoritmo = header["alg"]          # ← el atacante controla esto
payload = jwt.decode(token, SECRET_KEY, algorithms=[algoritmo])
```

o peor, una librería vieja/mal configurada que, al ver `alg: none`, **salta por completo el paso de verificación de firma** y acepta el payload como válido.

### El ataque, paso a paso

1. El atacante toma un JWT legítimo propio (ej. el de un usuario común, `user_id: 36`).
2. Modifica el **header** a `{"alg": "none", "typ": "JWT"}`.
3. Modifica el **payload** con la identidad/rol que quiera, ej. `{"user_id": 1, "role": "admin"}`.
4. Deja la **firma vacía** (el token termina en un punto, sin nada detrás).
5. Envía ese token al servidor.

Si el backend respeta el `alg: none` del header, **no ejecuta ninguna verificación de firma** — no hay nada que comprobar porque el token "declara" que no está firmado. El servidor decodifica el payload manipulado y lo toma como verdadero.

### La clave conceptual

**Cuando el verificador delega en el atacante la decisión de si hay que verificar la firma, la seguridad se derrumba por completo.** El atacante no rompe la criptografía ni necesita la `SECRET_KEY`: simplemente le *ordena* al servidor que no verifique nada. La firma deja de proteger la integridad porque el propio token dice "no me firmaron, aceptame tal cual".

## 4. Ejemplo concreto

**Token original (HS256, usuario común):**

```
Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"user_id": 36, "role": "student"}
Signature: <firma HMAC válida>
```

**Token forjado por el atacante (algoritmo none):**

```
Header:  {"alg": "none", "typ": "JWT"}
Payload: {"user_id": 1, "role": "admin"}
Signature: (vacía)
```

Codificado se ve así (fijarse que **termina en punto**, sin tercer segmento):

```
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4ifQ.
```

Contra un backend vulnerable, ese token entra como administrador.

## 5. Variantes del mismo problema

- **Case-sensitivity:** algunas defensas bloquean solo `"none"` en minúscula. Los atacantes prueban `None`, `NONE`, `nOnE`, etc., para evadir una validación mal hecha.
- **Confusión de algoritmo (algorithm confusion, ej. RS256 → HS256):** un primo hermano de este ataque, donde el servidor usa RS256 (asimétrico) y el atacante cambia el header a HS256 para que el servidor use la **clave pública** (que es conocida) como si fuera el secreto HMAC, y así poder firmar. Mismo origen del bug: confiar en el `alg` del header.

## 6. Mitigaciones

1. **Imponer el algoritmo esperado en el servidor, NO leerlo del token.** La verificación debe especificar explícitamente una allowlist:
   ```python
   # SEGURO: el servidor impone el algoritmo, ignora el 'alg' del atacante
   payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   ```
   Si llega un token con `alg: none` o `alg: RS256`, se rechaza porque no está en la lista.
2. **Nunca permitir `none` en producción.** Rechazar explícitamente ese algoritmo.
3. **Usar librerías actualizadas.** Las versiones modernas de la mayoría de las librerías JWT ya rechazan `none` por defecto y exigen que se pase el parámetro `algorithms`.
4. **Separar claves por algoritmo** para evitar la confusión RS256/HS256.
5. Defensa en profundidad: validar también claims críticos (`exp`, `iss`, `aud`) y, para operaciones sensibles, no confiar únicamente en el rol embebido en el token sino re-validarlo contra la base de datos.

## 7. Conclusión

El ataque de algoritmo `none` es un caso de manual de **"confiar en input controlado por el atacante para tomar una decisión de seguridad"**. El `alg` del header es parte del token, y el token lo arma quien lo envía; si el servidor obedece ese campo para decidir *si* verifica la firma, le está entregando al atacante la llave de su propia autenticación. La integridad de un JWT nunca debe depender de un valor que el cliente puede modificar: el algoritmo de verificación tiene que estar **fijado y restringido del lado del servidor**.
