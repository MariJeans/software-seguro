# Lab: Notas Universitarias

**Plataforma:** Software Seguro (softwareseguro.com.ar)
**Stack identificado:** Django + Django REST Framework (djangorestframework-simplejwt)
**Objetivo del lab:** Modificar la nota del usuario `benjamin.sosa142` en la materia *Análisis Matemático I*, elevándola a 9.

---

## 1. Enunciado y materiales entregados

- Credenciales válidas de bajo privilegio: `benjamin.sosa142` / `nsdfjklewe..`
- Un JWT de tipo **refresh**, supuestamente filtrado por un infoStealer, perteneciente a un usuario desconocido:
  ```
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6NDg2NjEyODQwOCwiaWF0IjoxNzQ0MDY0NDA4LCJqdGkiOiJhOTNmMmMxYWI0OTY0NGJiODY1OWMwOTI3ZmQwYmM1NCIsInVzZXJfaWQiOjM2fQ.MienEEx2ZuN-xdFj7Qti8HYXILlqZmVfjMhC-Hun_tw
  ```
- Aviso de que ese refresh token ya está **blacklisteado** (no se puede usar en `/api/token/refresh/`).
- Dato de que el panel de administración de Django está habilitado en su URL por defecto, con credenciales de superusuario sin modificar desde la instalación.

## 2. Reconocimiento

### 2.1 Decodificación del JWT (sin atacar nada todavía)

Se decodificó el JWT (header.payload en base64url, sin necesidad de la firma) para extraer metadata:

- **Header:** `{"alg": "HS256", "typ": "JWT"}`
- **Payload:** `{"token_type": "refresh", "exp": 4866128408, "iat": 1744064408, "jti": "a93f2c1ab49644bb8659c0927fd0bc54", "user_id": 36}`

Dato clave: el token identifica al **`user_id: 36`**, con una expiración absurdamente lejana (año ~2124) — un detalle deliberado del lab para que el dato relevante no sea el token en sí, sino **a quién pertenece**.

### 2.2 Acceso al panel de administración de Django

Se probó `/admin/` con credenciales por defecto típicas de instalación. Resultado: **acceso concedido como superusuario (`admin`)**, confirmando el primer fallo de seguridad (credenciales de superusuario no modificadas desde la instalación — *Security Misconfiguration / Weak Credentials*).

Dentro del admin solo estaban registrados los módulos nativos de Django:
- **Authentication and Authorization** (Users, Groups)
- **Token Blacklist** (Blacklisted Tokens, Outstanding Tokens)

No había ningún modelo de "Notas" o "Materias" registrado en el admin, por lo que no se podía editar la nota directamente desde ahí.

### 2.3 Cruce del JWT con el panel de admin

En **Outstanding Tokens** apareció un único registro, correspondiente al **mismo `jti`** que el JWT entregado en el enunciado:

```
Token for graciela romero.romero799 (a93f2c1ab49644bb8659c0927fd0bc54)
User: graciela romero.romero799
Jti: a93f2c1ab49644bb8659c0927fd0bc54
```

Esto confirmó que **`user_id: 36` = graciela romero.romero799**, y que ella era la pieza clave del lab (el token en sí no era explotable por estar blacklisteado, pero señalaba a la usuaria correcta).

## 3. Explotación

### 3.1 Toma de cuenta de graciela sin necesitar su contraseña

Usando el acceso de superusuario al admin, se entró a `Users → graciela romero.romero799` y se usó la función nativa de Django **"Reset password"** para asignarle una contraseña nueva conocida, sin necesitar la original (*Broken Access Control* — un superusuario puede resetear la credencial de cualquier cuenta).

Con la nueva contraseña, se inició sesión como `graciela romero.romero799` en la aplicación normal (no el admin). Resultado: graciela es **profesora de Física II**, con una pantalla de gestión de notas:

```
Notas de alumnos de la materia Física II
Alumno | Legajo | Nota | [Guardar]
```

### 3.2 Identificación del IDOR

Se interceptó la petición que dispara el botón "Guardar" con Burp Suite:

```
POST /home/ HTTP/2
Content-Type: application/x-www-form-urlencoded

csrfmiddlewaretoken=<token>&materia_id=7&estudiante_id=14&nota=6.0
```

Observación clave: el formulario envía **`materia_id` y `estudiante_id` como parámetros controlados por el cliente**, sin que el backend valide (según lo observado) que esa `materia_id` pertenezca realmente al profesor autenticado. Esto es un **IDOR (Insecure Direct Object Reference)**: la autorización depende de que el usuario esté logueado como "algún" profesor, no de que sea el dueño del recurso que está modificando.

### 3.3 Explotación del IDOR

1. Se guardó la propia nota de Sosa, Benjamín en Física II con un valor distintivo (`3.0`) para confirmar que el guardado persiste de verdad en la base de datos (verificado luego desde la sesión de `benjamin.sosa142`).
2. Se identificó el `estudiante_id` de Benjamín (`estudiante_id=8`) repitiendo el guardado en su fila.
3. Se envió la misma petición cambiando únicamente `materia_id` (probando valores fuera de `7`, que correspondía a Física II), manteniendo `estudiante_id=8` y `nota=9.0`.
4. El servidor aceptó el cambio igual, aunque esa materia no era de graciela.

## 4. Evidencia / Resultado

Verificado desde la sesión de `benjamin.sosa142` → "Mis Materias y Notas":

| Materia | Nota |
|---|---|
| Álgebra y Geometría Analítica | 9.00 |
| **Análisis Matemático I** | **9.00** ✅ (objetivo cumplido) |
| Física I | 9.00 |
| Química | 9.00 |
| Sistemas de Representación | 1.00 |
| Análisis Matemático II | 4.00 |
| Física II | 3.00 |

Flag obtenida: **`660b416167e7fd839bc06c61bb5a184b`**

## 5. Cadena de vulnerabilidades (resumen)

| Paso | Vulnerabilidad | Categoría OWASP |
|---|---|---|
| 1 | Credenciales de superusuario de Django sin cambiar desde la instalación | A07 — Identification and Authentication Failures / A05 — Security Misconfiguration |
| 2 | Reset de contraseña de cualquier usuario desde el admin, sin controles adicionales | A01 — Broken Access Control |
| 3 | IDOR en el guardado de notas: no se valida que la materia pertenezca al profesor logueado | A01 — Broken Access Control (IDOR) |

El JWT entregado en el enunciado no se explotó de forma directa (estaba blacklisteado y no se encontró el `SECRET_KEY` para forjar uno nuevo); su función en el lab fue de **pista de reconocimiento** para identificar al usuario objetivo (`user_id: 36` → graciela), no un vector de ataque en sí mismo.

## 6. Lecciones / notas para el reporte final

- Importancia de no asumir que todos los datos entregados en un enunciado son "el" vector: a veces son pistas de reconocimiento (el JWT acá).
- Un superusuario de Django con el admin expuesto es un riesgo crítico aunque la app no registre modelos de negocio ahí: permite tomar control de cualquier cuenta vía reset de password.
- Validar SIEMPRE del lado del servidor que el recurso que se modifica (`materia_id`) pertenece al usuario autenticado — nunca confiar en un ID que viaja desde el cliente, sea en el body de un form o en una API JSON.
