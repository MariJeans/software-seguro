# Objetivo 2: Anatomía del DOM XSS

**Consigna:** A diferencia del XSS Almacenado y Reflejado, el **DOM-Based XSS** es indetectable para muchos IPS/WAF. Explicar por qué, analizando cómo manejan los navegadores el fragmento `#` de una URL y qué pasa cuando el JavaScript procesa entradas como `location.hash` de forma insegura.

---

## 1. Repaso: los tres tipos de XSS

- **XSS Almacenado (Stored):** el payload se **guarda en el servidor** (ej. en un comentario) y se sirve a otros usuarios. El servidor "ve" el payload cuando se envía y cuando se entrega.
- **XSS Reflejado (Reflected):** el payload viaja en la **petición al servidor** (ej. un parámetro de query), y el servidor lo **devuelve reflejado** en la respuesta HTML. El servidor "ve" el payload en la petición.
- **XSS Basado en DOM (DOM-Based):** la vulnerabilidad está **enteramente del lado del cliente**. El payload **nunca se procesa en el servidor**: lo lee y lo ejecuta el **JavaScript del navegador**, manipulando el DOM. El servidor nunca llega a ver el dato malicioso.

Esa última diferencia es la clave de por qué es invisible para las defensas de red.

## 2. El punto clave: el fragmento `#` nunca se envía al servidor

En una URL, todo lo que va **después del `#`** se llama **fragmento** (o *hash*). Y hay una regla fundamental del protocolo HTTP:

> **El navegador NO envía el fragmento (`#...`) al servidor.**

Cuando pedís `https://sitio.com/pagina?buscar=hola#seccion`, el navegador manda al servidor solo `https://sitio.com/pagina?buscar=hola`. **El `#seccion` se queda en el navegador** — originalmente servía para hacer scroll a un ancla dentro de la página. El servidor jamás lo recibe, no queda en sus logs, y ninguna defensa que mire el tráfico del lado del servidor lo ve.

Esto significa que un atacante puede poner su payload en el fragmento:

```
https://sitio.com/pagina#<img src=x onerror=alert(1)>
```

...y ese payload **nunca cruza por el servidor, el WAF ni el IPS**. Viaja directo del navegador de la víctima al JavaScript de la página.

## 3. Cómo ocurre el DOM XSS

El JavaScript de la página lee ese fragmento (u otra fuente controlable por el cliente) y lo **escribe en el DOM sin sanitizar**. Dos conceptos:

- **Source (fuente):** de dónde sale el dato controlable por el atacante. Ejemplos: `location.hash` (el `#...`), `location.search`, `document.URL`, `document.referrer`.
- **Sink (sumidero):** la función peligrosa que **convierte ese dato en código/HTML ejecutable**. Ejemplos: `innerHTML`, `document.write()`, `eval()`, `insertAdjacentHTML`, asignar a `location`.

El DOM XSS ocurre cuando un dato va de un **source** a un **sink** peligroso sin pasar por codificación.

### Ejemplo vulnerable

```javascript
// La página toma el fragmento de la URL (source)...
let seccion = location.hash.substring(1);   // lo que va después del #

// ...y lo escribe directo en la página (sink: innerHTML)
document.getElementById("contenido").innerHTML = "Estás en: " + seccion;
```

Si la víctima abre:

```
https://sitio.com/pagina#<img src=x onerror=alert(document.cookie)>
```

El JavaScript lee `location.hash`, lo mete en `innerHTML`, el navegador **renderiza ese HTML** y dispara el `onerror` → se ejecuta el código del atacante. Todo **dentro del navegador de la víctima**, sin que el servidor haya visto nada.

## 4. Por qué es indetectable para WAF / IPS

Los WAF e IPS trabajan **inspeccionando el tráfico que llega al servidor** (las peticiones HTTP). Buscan payloads de XSS en parámetros, cuerpos, cabeceras. Pero en el DOM XSS:

1. **El payload va en el fragmento `#`, que nunca se envía al servidor** → el WAF literalmente **no tiene nada que inspeccionar**. El dato malicioso nunca pasa por él.
2. **La ejecución ocurre 100% en el cliente** → la vulnerabilidad vive en el JavaScript del navegador, no en una respuesta que el servidor genere con el payload. El WAF no ve ni la entrada ni el resultado.
3. Incluso si el source fuera `location.search` (que sí viaja al servidor), el hecho de que el **procesamiento inseguro esté en el JS del cliente** hace que el análisis del lado servidor no alcance para detectarlo: habría que analizar el flujo *source → sink* dentro del código JavaScript, algo que un WAF de red no hace.

Por eso el DOM XSS es un **punto ciego**: las defensas perimetrales (WAF, IPS) asumen que el ataque pasa por el servidor, y este, por diseño, no lo hace.

## 5. Cómo se detecta y mitiga

- **Detección:** requiere **análisis del código del lado cliente** — revisar manualmente o con herramientas (análisis estático de JS, el escáner de DOM de Burp) el flujo desde cada *source* (`location.hash`, etc.) hasta cada *sink* peligroso (`innerHTML`, `eval`...).
- **Mitigación:**
  - **No usar sinks peligrosos con datos no confiables.** En vez de `innerHTML`, usar `textContent` / `innerText` (que insertan el dato como **texto**, no como HTML).
  - **Codificar/sanitizar** el dato antes de meterlo en el DOM (ej. librerías como DOMPurify si se necesita HTML).
  - **Evitar `eval()`, `document.write()`** y la asignación directa de datos no confiables a `location`.
  - **CSP** como red de contención (ver Objetivo 3).

## 6. Conclusión

El DOM XSS es especialmente peligroso porque rompe el supuesto en el que se apoyan los WAF e IPS: que el ataque atraviesa el servidor. Al vivir en el **fragmento `#` (que nunca se envía) y ejecutarse íntegramente en el JavaScript del cliente**, el payload es invisible para toda defensa que inspeccione el tráfico del lado del servidor. La vulnerabilidad nace de un flujo inseguro **source → sink** (`location.hash` → `innerHTML`) en el código del navegador, y por eso solo se detecta y se corrige **en el propio cliente**, no en el perímetro.
