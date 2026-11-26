# Objetivo 3: Defensa en Profundidad (Encoding y CSP)

**Consigna:** Explicar cómo un arquitecto de seguridad mitiga definitivamente el riesgo de XSS con dos capas de defensa: 1) **Output Encoding** (codificación de salida) a nivel de código, y 2) una política de **Content Security Policy (CSP)** a nivel de cabeceras HTTP.

---

## 1. La idea de "defensa en profundidad"

Ninguna capa por sí sola es perfecta, así que se apilan varias: si una falla (un olvido del programador, un vector nuevo), la siguiente contiene el daño. Contra XSS, las dos capas más efectivas son **codificar la salida** (prevenir que el input se interprete como código) y **CSP** (limitar qué código puede ejecutarse aunque la primera capa falle).

## 2. Capa 1 — Output Encoding (Codificación de Salida)

### Qué es

El XSS ocurre porque un dato del usuario se **renderiza como código** (HTML/JS) en lugar de como texto. El **output encoding** consiste en, **al momento de insertar el dato en la página**, convertir los caracteres que tienen significado especial en HTML a sus **entidades inofensivas**, de modo que el navegador los muestre como texto literal y **no los interprete como marcado**.

Conversión básica para contexto HTML:

| Carácter | Se codifica como |
|---|---|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |

### Cómo neutraliza el XSS

Si un atacante envía como comentario:

```html
<img src=x onerror=alert(1)>
```

Con output encoding, al renderizarse en la página se transforma en:

```
&lt;img src=x onerror=alert(1)&gt;
```

El navegador muestra en pantalla el **texto literal** `<img src=x onerror=alert(1)>` — los `&lt;` y `&gt;` se ven como `<` y `>` pero **no abren una etiqueta**. El navegador nunca crea un elemento `<img>`, así que **no hay evento `onerror` que disparar**. El payload quedó inerte, convertido en un simple string visible. A diferencia de las listas negras (Objetivo 1 del módulo anterior), esto no intenta "adivinar" qué es malicioso: **trata todo el input como dato**, sin excepciones.

### El punto crítico: codificar según el CONTEXTO

La codificación correcta **depende de dónde se inserta** el dato. El mismo valor necesita codificación distinta si va:

- **En el cuerpo HTML** (entre etiquetas) → codificación de entidades HTML (la de la tabla).
- **Dentro de un atributo** (`value="..."`) → codificación de atributo (incluye comillas).
- **Dentro de JavaScript** (en un `<script>`) → codificación/escape de JS (Unicode `\u...`).
- **En una URL** (un `href`) → URL encoding (`%xx`), y validar el esquema.
- **En CSS** → escape de CSS.

Insertar un dato "HTML-codificado" dentro de un contexto JavaScript, por ejemplo, **no protege**. Por eso lo correcto es **codificar en el momento de la salida y según el contexto exacto** (lo que hacen por defecto los motores de plantillas modernos como los de Django, React, etc., que auto-escapan).

### Dónde encaja con el DOM XSS

Para el DOM XSS (Objetivo 2), la "codificación de salida" se traduce en **usar sinks seguros**: `textContent` en vez de `innerHTML` inserta el dato como texto automáticamente, que es la versión del lado cliente del mismo principio.

## 3. Capa 2 — Content Security Policy (CSP)

### Qué es

CSP es una **cabecera HTTP** (`Content-Security-Policy`) que el servidor envía y que le dice al navegador, de forma explícita, **de qué orígenes puede cargar y ejecutar recursos** (scripts, estilos, imágenes...). Es una **lista blanca** que el navegador hace cumplir. Si algo no está permitido por la política, el navegador **lo bloquea**, aunque ya esté inyectado en la página.

### Cómo mitiga el XSS

CSP actúa como **segunda línea**: aunque un payload logre inyectarse (porque la codificación falló en algún punto), CSP puede **impedir que el código malicioso se ejecute**. Ejemplos de lo que una buena política bloquea:

- **Scripts inline** (`<script>...</script>` o `onerror=...`): una política sin `'unsafe-inline'` hace que el navegador **se niegue a ejecutar** cualquier JavaScript embebido en el HTML. Esto mata de raíz la mayoría de los payloads de XSS, que son justamente código inline.
- **Scripts de dominios no autorizados:** si el atacante inyecta `<script src="https://sitio-malicioso.com/robar.js">`, CSP solo deja cargar scripts de los orígenes de la lista blanca, así que lo bloquea.

Ejemplo de cabecera:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'
```

- `default-src 'self'` → por defecto, solo recursos del propio dominio.
- `script-src 'self'` → JavaScript **solo** desde el propio dominio; **nada de inline** (porque no está `'unsafe-inline'`) y nada de dominios externos.
- `object-src 'none'` → sin plugins (Flash, etc.).

Con esa política, un `<img onerror=alert(1)>` inyectado **no ejecuta nada**, porque el `onerror` inline está prohibido.

### Buenas prácticas de CSP

- **Evitar `'unsafe-inline'` y `'unsafe-eval'`**, que anulan gran parte del beneficio.
- Para scripts legítimos que deben ir inline, usar **nonces** (`'nonce-xxxx'`, un valor aleatorio por request) o **hashes**, de modo que solo esos scripts específicos corran.
- **Es una red de contención, no un reemplazo del encoding:** CSP reduce el impacto si algo se escapa, pero la prevención primaria sigue siendo codificar la salida.

## 4. Por qué las dos capas juntas

| Capa | Qué hace | Si falla sola... |
|---|---|---|
| **Output Encoding** | Impide que el input se interprete como código (prevención en origen) | ...un olvido en un solo punto reabre el XSS |
| **CSP** | Impide que el código inyectado se ejecute (contención) | ...no previene el XSS, solo limita su daño; mal configurada (con `unsafe-inline`) no sirve |

Combinadas, se cubren mutuamente: el encoding evita que el payload se forme, y si en algún punto el programador se olvidó de codificar, CSP evita que ese payload llegue a ejecutarse. Esa redundancia es la **defensa en profundidad**.

## 5. Conclusión

La mitigación definitiva del XSS no es un filtro que bloquea etiquetas (evadible), sino dos capas que atacan el problema desde ángulos distintos: **Output Encoding**, que al escribir el dato en la página lo convierte en texto inofensivo según el contexto, de modo que el input **nunca se interprete como código**; y **CSP**, una cabecera que ordena al navegador no ejecutar scripts inline ni de orígenes no autorizados, **conteniendo cualquier payload que haya logrado colarse**. La primera previene; la segunda contiene. Juntas hacen que un XSS necesite que fallen **ambas** para tener impacto — que es justamente el objetivo de la defensa en profundidad.
