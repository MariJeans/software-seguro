# Objetivo 4 — Manejo Inseguro de Errores (Stack Traces)

> **Curso:** Ciberseguridad Web y Ethical Hacking (UTN / Software Seguro)
> **Módulo / Objetivo:** Security Misconfiguration — Manejo Inseguro de Errores
> **Autora:** María de los Ángeles Acuña — QA Tester
> **Fecha:** Octubre 2026

---

## 1. Introducción: cómo reacciona una app ante un fallo define su seguridad

Toda aplicación falla en algún momento: una consulta a la base de datos que rompe, una
variable que llega nula, un archivo que no existe, una división por cero. Lo que marca la
diferencia **no es que falle**, sino **qué le muestra al usuario cuando falla**.

Hay dos formas opuestas de reaccionar:

- Un **mensaje de error genérico** → seguro.
- Un **Stack Trace detallado** expuesto en producción → inseguro.

Entender la diferencia entre ambos, y por qué el segundo es tan peligroso, es el objetivo
de esta investigación.

---

## 2. ¿Qué es un "mensaje de error genérico"?

Es una respuesta **neutra y controlada** que la aplicación le muestra al usuario cuando
algo sale mal, **sin revelar ningún detalle interno** de cómo está construida.

Ejemplos típicos:

- *"Ocurrió un error inesperado. Intentá nuevamente más tarde."*
- *"No se puede procesar la solicitud."*
- Una página `500` personalizada con un código de referencia (ej. *"Error ID: 8F3A2"*)
  que solo sirve para que el equipo técnico lo busque en sus logs internos.

Características clave:

- **No dice qué tecnología usa** la app ni su versión.
- **No muestra rutas de archivos**, nombres de funciones, ni líneas de código.
- **No revela consultas SQL** ni estructura de la base de datos.
- El detalle real del error **se guarda del lado del servidor** (en logs privados), donde
  solo lo ve el equipo de desarrollo.

En resumen: el usuario (y un posible atacante) se entera de que **algo falló**, pero no de
**qué** ni **dónde**.

---

## 3. ¿Qué es un "Stack Trace" (traza de la pila)?

Un **Stack Trace** es el **informe técnico detallado** que genera el lenguaje de
programación cuando ocurre una excepción no controlada. Es la "radiografía" exacta del
error: muestra la secuencia de llamadas (la *pila* de funciones) que se ejecutaron hasta
el punto donde reventó el programa.

Un Stack Trace típicamente incluye:

- El **tipo de excepción** (ej. `NullPointerException`, `SQLException`, `PDOException`).
- El **mensaje de error** exacto (que a veces incluye hasta la consulta SQL que falló).
- La **cadena de archivos y líneas** por donde pasó la ejecución
  (ej. `/var/www/app/controllers/UserController.php:92`).
- Los **nombres de funciones, clases y métodos** internos.
- A menudo, la **versión del framework, del lenguaje y del servidor**.

### Ejemplo ilustrativo (PHP)

```
Fatal error: Uncaught PDOException: SQLSTATE[42S02]:
Base table or view not found: 1146 Table 'tienda.usuario' doesn't exist
in /var/www/html/includes/db_connect.php:48
Stack trace:
#0 /var/www/html/includes/db_connect.php(48): PDO->query('SELECT * FROM us...')
#1 /var/www/html/login.php(15): getUser('admin')
#2 {main}
  thrown in /var/www/html/includes/db_connect.php on line 48
```

En esas pocas líneas, un atacante ya se enteró de:

- que la app usa **PHP con PDO** (tecnología),
- que la base de datos se llama **`tienda`** y tenía una tabla **`usuario`**,
- la **ruta absoluta** del código en el servidor (`/var/www/html/...`),
- los **nombres de archivos** internos (`db_connect.php`, `login.php`) y las líneas exactas,
- y hasta **parte de la consulta SQL** que se ejecuta.

Lo que para el desarrollador es una herramienta de *debugging* buenísima en su máquina
local, en **producción** se convierte en un **regalo de información** para el atacante.

---

## 4. Comparación directa

| Aspecto | Mensaje genérico (seguro) | Stack Trace expuesto (inseguro) |
|---|---|---|
| **Qué ve el usuario** | "Ocurrió un error" | Detalle técnico completo del fallo |
| **Tecnología / versión** | Oculta | Revelada (lenguaje, framework, servidor) |
| **Rutas del servidor** | Ocultas | Expuestas (ej. `/var/www/html/...`) |
| **Estructura de la BD** | Oculta | A veces visible (nombres de tablas/columnas, SQL) |
| **Dónde queda el detalle** | En logs privados del servidor | En la pantalla del atacante |
| **Utilidad para el atacante** | Nula | Enorme |

---

## 5. ¿Por qué un Stack Trace facilita ENORMEMENTE la explotación?

Esta es la parte central de la consigna. En un pentest, antes de **explotar** una
vulnerabilidad hay que **conocer el objetivo** (la fase de reconocimiento que vimos en
clase). Un Stack Trace expuesto **le ahorra al atacante gran parte de ese trabajo** y le
entrega información que normalmente tendría que deducir a ciegas:

1. **Fingerprinting gratis (identificar el stack técnico).**
   Saber que la app corre, por ejemplo, PHP 8.0 sobre Apache con MySQL le permite al
   atacante buscar **CVEs y exploits conocidos** para esas versiones exactas, en lugar de
   atacar a ciegas.

2. **Revela la estructura interna de la base de datos.**
   Si el error muestra nombres de tablas y columnas (`usuario`, `password`, `tienda`), el
   atacante ya sabe **qué pedir** cuando intente una **inyección SQL**. En vez de adivinar,
   construye consultas dirigidas.

3. **Convierte las inyecciones a ciegas en inyecciones "con vista" (error-based).**
   En una SQL Injection, el Stack Trace funciona como un **oráculo**: cada vez que el
   atacante manda un payload malformado, el error le confirma si va por buen camino y le
   devuelve pedazos de la consulta. Esto transforma un ataque lento y "a ciegas" (*blind*)
   en uno rápido y guiado (*error-based*), acelerando muchísimo la explotación.

4. **Mapea el sistema de archivos del servidor.**
   Las rutas absolutas (`/var/www/html/includes/db_connect.php`) le dicen al atacante
   **dónde** está el código. Eso es oro para otros ataques como **Local File Inclusion
   (LFI)**, **Path Traversal** o para saber dónde intentar escribir un *webshell*.

5. **Expone la lógica del código.**
   Los nombres de funciones y archivos (`getUser()`, `login.php`) revelan **cómo piensa**
   la aplicación, qué hace cada parte y por dónde conviene seguir atacando.

6. **Reduce el "ruido" y el tiempo del ataque.**
   Sin Stack Trace, el atacante tiene que hacer mucho *fuzzing* y prueba y error, generando
   logs y alertas. Con Stack Trace, apunta directo al blanco: **menos intentos, menos
   detección, más efectividad.**

> **En una frase:** el Stack Trace transforma a la propia aplicación en el mejor aliado del
> atacante, porque le hace gratis el reconocimiento que debería costarle tiempo y esfuerzo,
> y lo guía paso a paso hacia la explotación.

---

## 6. Clasificación

- **Tipo:** Divulgación de información sensible (Information Disclosure / Information Leakage).
- **OWASP Top 10:** **A05:2021 — Security Misconfiguration** (y se relaciona con
  **A04:2021 — Insecure Design** cuando el manejo de errores no se diseñó pensando en
  seguridad).
- **CWE:**
  - **CWE-209 — Generation of Error Message Containing Sensitive Information.**
  - **CWE-200 — Exposure of Sensitive Information to an Unauthorized Actor.**
- **Severidad:** generalmente **Media** por sí sola (es una fuga, no un acceso directo),
  pero es un **multiplicador de riesgo**: combinada con otra vulnerabilidad (como una SQLi),
  acelera y agrava el compromiso.

---

## 7. ¿Cómo se mitiga?

La idea central: **el detalle del error va al log privado; al usuario, un mensaje genérico.**

1. **Apagar el modo debug / display_errors en producción.**
   El error de configuración más común es dejar activado el modo de desarrollo.
   - **PHP:** `display_errors = Off` en `php.ini`; registrar en `log_errors = On`.
   - **Django (Python):** `DEBUG = False` en `settings.py`.
   - **ASP.NET:** `<customErrors mode="On" />`.
   - **Express (Node):** no enviar `err.stack` en la respuesta; usar un *error handler*
     que devuelva un mensaje genérico.

2. **Páginas de error personalizadas (genéricas).**
   Configurar páginas `404` y `500` propias y neutras a nivel de aplicación y de servidor
   (Apache: `ErrorDocument`; Nginx: `error_page`), sin ningún detalle técnico.

3. **Logging del lado del servidor.**
   Guardar el Stack Trace completo en un **log interno** (no accesible por web), para que el
   equipo de desarrollo pueda diagnosticar sin exponer nada al público. Opcionalmente, darle
   al usuario un **ID de error** para referenciar el incidente en soporte.

4. **Manejo de excepciones (try/catch).**
   Capturar las excepciones y responder con un mensaje controlado, en lugar de dejar que la
   excepción "burbujee" hasta el navegador.

5. **No filtrar versiones.**
   Ocultar o modificar cabeceras como `Server` y `X-Powered-By` para no regalar la tecnología
   y versión del stack.

### Verificación (re-test)

- Forzar errores a propósito (una comilla en un input, una ruta inexistente, un tipo de dato
  inválido) y confirmar que la app responde con un **mensaje genérico**, sin rutas, sin SQL,
  sin versiones ni trazas.

---

## 8. Conclusión

La forma en que una aplicación reacciona ante un fallo revela su madurez en seguridad. Un
**mensaje genérico** le dice al usuario que algo salió mal y guarda el detalle donde
corresponde: en los logs internos. Un **Stack Trace expuesto en producción**, en cambio, le
entrega al atacante un informe técnico completo —tecnología, versiones, rutas, estructura de
la base de datos y hasta consultas SQL— que le hace gratis la fase de reconocimiento y lo
guía directo hacia la explotación. Es un error de **configuración** fácil de corregir
(apagar el modo debug y usar páginas de error genéricas) y que debe formar parte del
*hardening* básico antes de cualquier pase a producción. En seguridad, **un error debe
informar al usuario lo justo y necesario, y al atacante, nada.**

---

## Referencias

- OWASP Top 10 — A05:2021 Security Misconfiguration.
- CWE-209 — Generation of Error Message Containing Sensitive Information.
- CWE-200 — Exposure of Sensitive Information to an Unauthorized Actor.
- OWASP Web Security Testing Guide — *Testing for Improper Error Handling*.
- OWASP Cheat Sheet Series — *Error Handling Cheat Sheet*.
