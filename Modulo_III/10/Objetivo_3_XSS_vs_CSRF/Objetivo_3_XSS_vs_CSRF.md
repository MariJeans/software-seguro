# Objetivo 3: XSS vs CSRF

**Consigna:** Ambos ataques involucran al navegador de la víctima y buscan afectar su cuenta, pero sus mecánicas son opuestas. Redactar una comparación técnica directa explicando la diferencia fundamental entre **Cross-Site Scripting (XSS)** y **Cross-Site Request Forgery (CSRF)**.

---

## 1. La diferencia fundamental en una frase

- **XSS** es un problema de **ejecución de código**: el atacante logra que **su JavaScript se ejecute en el navegador de la víctima**, dentro del contexto del sitio confiable. Explota la **confianza del usuario en el sitio**.
- **CSRF** es un problema de **falsificación de peticiones**: el atacante logra que **el navegador de la víctima envíe una petición no deseada** al sitio confiable, usando la sesión que ya tiene. Explota la **confianza del sitio en el navegador de la víctima** (en su cookie).

En otras palabras: **XSS inyecta y ejecuta código; CSRF dispara una acción legítima de forma fraudulenta.** XSS corre código en el cliente; CSRF no corre ningún código propio del atacante en el sitio víctima, solo abusa del envío automático de la cookie.

## 2. Comparación técnica directa

| Aspecto | **XSS** | **CSRF** |
|---|---|---|
| **Qué hace el atacante** | Inyecta y ejecuta **su propio JavaScript** en el navegador de la víctima | Hace que el navegador **envíe una petición** a una acción existente del sitio |
| **Qué explota** | La confianza del **usuario en el sitio** (el código corre con el origen del sitio confiable) | La confianza del **sitio en el navegador** (la cookie válida que el navegador adjunta solo) |
| **¿Ejecuta código en el sitio víctima?** | **Sí** — ese es el núcleo del ataque | **No** — solo dispara una petición HTTP válida |
| **¿Puede leer datos / la respuesta?** | **Sí.** El JS inyectado puede leer el DOM, robar cookies (si no son HttpOnly), tokens, hacer peticiones y leer respuestas | **No** (en general). El atacante dispara la acción "a ciegas"; la política del navegador le impide leer la respuesta |
| **Alcance del daño** | Muy amplio: robo de sesión, keylogging, modificar la página, realizar cualquier acción como la víctima, e incluso **ejecutar un CSRF** desde adentro | Acotado a **acciones con efecto** que el sitio ya ofrece (cambiar email, transferir, cambiar contraseña) |
| **¿Necesita que la víctima esté logueada?** | No necesariamente (depende del objetivo) | **Sí** — depende de una sesión activa (una cookie válida) para que la acción funcione |
| **Vector típico** | Un input que se refleja/almacena sin codificar y se renderiza como HTML/JS | Una página maliciosa con un formulario auto-enviado o una `<img>` apuntando al sitio víctima |
| **Defensa principal** | **Output encoding** + **CSP** (que el input nunca se interprete como código) | **SameSite cookies** + **tokens anti-CSRF** (que la petición cross-site no lleve sesión válida) |

## 3. La relación entre ambos (y por qué XSS es "más grave")

Un detalle importante: **un XSS puede ejecutar un CSRF, pero un CSRF no puede ejecutar un XSS.**

- Como el XSS corre JavaScript **dentro del sitio confiable**, ese código puede leer el token anti-CSRF de la página y enviar la petición maliciosa con el token correcto. Es decir, **XSS rompe las defensas anti-CSRF**: los tokens no sirven de nada si el atacante ya está ejecutando código en tu página.
- Por eso se considera al **XSS más peligroso**: incluye la capacidad del CSRF **y además** puede leer datos, robar sesión y hacer mucho más. El CSRF, en cambio, está limitado a disparar acciones predefinidas sin leer nada.

## 4. Analogía para fijar la diferencia

- **XSS:** el atacante logra **meter un empleado infiltrado dentro del banco** (su código corre adentro, con los permisos del sitio). Ese infiltrado puede mirar todo y hacer casi cualquier cosa.
- **CSRF:** el atacante **falsifica una orden firmada con la firma de la víctima** y la manda al banco. El banco la ejecuta porque la firma (la cookie) es válida, pero el atacante no está adentro ni puede ver qué responde el banco.

## 5. Conclusión

XSS y CSRF comparten que ocurren en el navegador de la víctima y apuntan a su cuenta, pero son **mecánicas opuestas**: XSS **ejecuta código del atacante** dentro del sitio confiable (abusa de la confianza del usuario en el sitio) y por eso puede leer, robar y actuar sin límites; CSRF **no ejecuta código**, solo consigue que el navegador **envíe una petición autenticada** que la víctima no quiso (abusa de la confianza del sitio en la cookie del navegador) y queda limitado a disparar acciones a ciegas. Por eso también difieren sus defensas: el XSS se combate impidiendo que el input se interprete como código (encoding + CSP), y el CSRF impidiendo que una petición cross-site lleve una sesión válida (SameSite + tokens). Y como un XSS puede, además, montar un CSRF, el XSS es el de mayor impacto de los dos.
