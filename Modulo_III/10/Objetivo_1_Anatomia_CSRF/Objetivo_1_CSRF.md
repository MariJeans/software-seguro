# Objetivo 1: Anatomía de un Ataque CSRF (Cross-Site Request Forgery)

**Consigna:** Explicar el flujo exacto de un ataque CSRF exitoso, por qué ocurre (énfasis en el comportamiento automático de los navegadores con las cookies) y cómo el atributo de cookie **SameSite** (valores `Lax` y `Strict`) lo mitiga radicalmente.

---

## 1. Qué es CSRF

**CSRF** (falsificación de petición entre sitios) es un ataque que **obliga al navegador de una víctima autenticada a ejecutar una acción no deseada** en un sitio en el que ya tiene sesión abierta. El atacante no roba la sesión ni la cookie: **abusa** de que el navegador la envía sola. La víctima, sin darse cuenta, "firma" la petición maliciosa con su propia sesión.

El objetivo típico son **acciones con efecto** (cambiar el email, transferir plata, cambiar la contraseña), no leer datos.

## 2. Por qué ocurre: el navegador envía las cookies automáticamente

Acá está la raíz del problema. Cuando te logueás en `banco.com`, el servidor te da una **cookie de sesión**. A partir de ahí, el navegador tiene una regla: **adjunta automáticamente las cookies de un dominio en TODA petición que vaya a ese dominio**, sin importar **desde qué página se originó** la petición.

Es decir: si estando logueada en `banco.com` abrís otra pestaña con `sitio-malicioso.com`, y esa página hace una petición a `banco.com`, **el navegador igual adjunta tu cookie de sesión de `banco.com`**. El navegador no distingue "esta petición la pedí yo desde el banco" de "esta petición la disparó una página de otro sitio": para él, una petición a `banco.com` lleva las cookies de `banco.com`, y punto.

El servidor del banco, al recibir la petición **con una cookie de sesión válida**, asume que es una acción legítima de la usuaria. **No puede distinguir** una petición genuina de una falsificada, porque ambas llegan con la misma cookie válida. Esa confianza ciega en la cookie es el fallo que CSRF explota.

## 3. Flujo exacto de un ataque CSRF

Escenario: el banco permite cambiar el email del titular con una petición `POST /cambiar-email`.

1. **La víctima se loguea** en `banco.com`. El navegador guarda su cookie de sesión. **No cierra sesión** (la cookie sigue viva).
2. **El atacante prepara una página maliciosa** en `sitio-malicioso.com` que contiene una petición dirigida al banco. Por ejemplo, un formulario que se auto-envía:
   ```html
   <form action="https://banco.com/cambiar-email" method="POST" id="f">
     <input type="hidden" name="email" value="atacante@evil.com">
   </form>
   <script>document.getElementById('f').submit();</script>
   ```
   (Para un `GET`, bastaría con una imagen: `<img src="https://banco.com/transferir?a=atacante&monto=1000">`.)
3. **El atacante hace que la víctima visite esa página** (un link en un email, un anuncio, un sitio cualquiera). Con que la víctima **abra la página**, alcanza.
4. **El navegador de la víctima envía la petición a `banco.com`** y —acá está la clave— **le adjunta automáticamente la cookie de sesión** de la víctima, porque la petición va dirigida a `banco.com`.
5. **El servidor del banco recibe la petición con una cookie válida**, cree que es la usuaria legítima, y **cambia el email** al del atacante. La víctima nunca se enteró; nunca vio ni hizo nada conscientemente.

Con el email cambiado, el atacante puede pedir un reset de contraseña y tomar la cuenta completa.

**Nota:** CSRF funciona para acciones de **escritura/efecto**. El atacante normalmente **no puede leer la respuesta** (la política del navegador —SOP/CORS— se lo impide); lo que logra es **disparar la acción**.

## 4. Mitigación con el atributo SameSite

La causa del problema es que el navegador envía la cookie en peticiones **que se originan desde otros sitios** (*cross-site*). El atributo **`SameSite`** de la cookie ataca exactamente eso: le dice al navegador **cuándo NO adjuntar la cookie en peticiones cross-site**. Lo setea el servidor al crear la cookie:

```
Set-Cookie: sessionid=abc123; SameSite=Lax; Secure; HttpOnly
```

### `SameSite=Strict`

El navegador **nunca** envía la cookie si la petición se origina desde **otro sitio**. Solo la adjunta cuando la navegación nace del **mismo sitio**. Esto **corta CSRF de raíz**: la petición del formulario malicioso de `sitio-malicioso.com` hacia `banco.com` **va sin la cookie de sesión**, así que el banco la ve como no autenticada y la rechaza.

- **Contra:** es tan estricto que rompe la experiencia legítima: si alguien te manda un link al banco por email o chat y lo clickeás, esa navegación es "cross-site" y **tampoco** llevará la cookie, por lo que vas a aparecer deslogueada aunque tengas sesión. Útil para acciones muy sensibles.

### `SameSite=Lax`

Un punto intermedio (y el **valor por defecto** en los navegadores modernos). La cookie:
- **SÍ** se envía en navegaciones *top-level* de tipo seguro (cuando el usuario **hace click en un link** y navega a la página → métodos `GET`), para no romper la usabilidad de los links entrantes.
- **NO** se envía en peticiones cross-site de tipo "peligroso": envíos de **formularios `POST`**, peticiones de `<img>`, `fetch`/AJAX en segundo plano, iframes, etc.

Como la mayoría de las acciones con efecto son `POST` (o deberían serlo), `Lax` **bloquea el vector CSRF clásico** (el formulario auto-enviado del paso 3) sin romper que los usuarios lleguen al sitio desde un link externo. Por eso es el equilibrio recomendado por defecto.

### Por qué SameSite mitiga "radicalmente"

Porque ataca la **causa raíz**: en lugar de intentar detectar peticiones falsificadas, simplemente **deja de adjuntar la cookie en los contextos cross-site** donde vive el ataque. Sin la cookie, la petición maliciosa llega sin autenticación y el servidor la rechaza.

## 5. Defensa en profundidad (complementos a SameSite)

SameSite es muy efectivo, pero se combina con:

- **Tokens anti-CSRF (synchronizer token):** el servidor incluye en cada formulario un token aleatorio e impredecible que el atacante no puede conocer; la petición sin ese token se rechaza. (Es la defensa clásica, independiente de SameSite.)
- **Verificar cabeceras `Origin` / `Referer`** para confirmar que la petición viene del propio sitio.
- **Usar métodos correctos:** que las acciones con efecto sean `POST`/`PUT`/`DELETE`, nunca `GET` (un `GET` se dispara con solo una `<img>`).
- **Re-autenticación** para acciones críticas (pedir la contraseña otra vez para cambiar el email o transferir).

## 6. Conclusión

CSRF existe por una decisión de diseño de los navegadores: **adjuntan las cookies de un dominio automáticamente en toda petición dirigida a ese dominio, sin importar desde qué sitio se originó**. Eso permite que una página maliciosa dispare acciones autenticadas en nombre de la víctima. El atributo **`SameSite`** mitiga el ataque de raíz al cortar el envío automático de la cookie en contextos *cross-site*: `Strict` no la manda nunca desde otro sitio (máxima protección, menos usabilidad), y `Lax` (el default) la bloquea en los `POST` y peticiones en segundo plano donde vive el CSRF, conservando los links entrantes. Combinado con tokens anti-CSRF, cierra el vector por completo.
