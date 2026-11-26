# Objetivo 1: El Arte de la Evasión de Filtros (WAF Bypass)

**Consigna:** Un desarrollador intenta bloquear XSS eliminando las etiquetas `<script>` y `</script>` de los comentarios. Explicar por qué esa defensa es inútil y dar al menos dos payloads en HTML/JS que ejecuten código **sin** usar la etiqueta `<script>`.

---

## 1. Por qué la defensa es inútil

El filtro parte de una suposición equivocada: que **la única forma de ejecutar JavaScript en una página es con la etiqueta `<script>`**. Eso es falso. El HTML ofrece **decenas de formas** de ejecutar código, así que bloquear solo `<script>` deja la puerta abierta de par en par. Hay tres problemas de fondo:

### 1.1 `<script>` no es el único vector

JavaScript también se ejecuta a través de **atributos de evento** (`onload`, `onerror`, `onmouseover`, `onfocus`...), de **URIs con el esquema `javascript:`**, y de otras etiquetas que disparan código. Eliminar `<script>` no toca ninguno de esos caminos.

### 1.2 El filtro por "lista negra" es evadible aunque quisiera bloquear `<script>`

Incluso para su objetivo puntual, un filtro que busca el texto literal `<script>` se evade fácil, porque el navegador es **tolerante** y "repara" HTML roto:
- Mayúsculas/minúsculas: `<ScRiPt>`.
- Si el filtro borra `<script>` una sola vez (no recursivamente), se anida: `<scr<script>ipt>` → al quitar el `<script>` del medio, queda `<script>`.
- Espacios, saltos de línea o atributos raros dentro de la etiqueta.

Es el problema clásico de las **listas negras**: hay infinitas variantes y el filtro siempre va un paso atrás.

### 1.3 La causa raíz: no se codifica la salida

El verdadero error no es "qué etiqueta bloquear", sino que el comentario del usuario se **inserta en el HTML sin codificar**. Mientras el input del usuario pueda convertirse en **marcado HTML activo** (etiquetas, atributos), siempre habrá un vector. La solución no es filtrar etiquetas, es **codificar la salida** (ver Objetivo 3).

## 2. Payloads que ejecutan código sin `<script>`

### Payload 1 — `<img>` con `onerror`

```html
<img src=x onerror="alert(document.cookie)">
```

**Cómo funciona:** se inserta una imagen con un `src` que **no existe** (`x`). Cuando el navegador intenta cargarla y falla, dispara el evento **`onerror`**, y ejecuta el JavaScript que pusimos ahí. No hay ninguna etiqueta `<script>`, así que el filtro no lo toca. En este ejemplo, roba la cookie de sesión (`document.cookie`).

### Payload 2 — `<svg>` con `onload`

```html
<svg onload="alert(document.domain)">
```

**Cómo funciona:** la etiqueta `<svg>` admite el evento **`onload`**, que se dispara **apenas el elemento se carga** en la página — sin necesidad de interacción del usuario ni de un recurso que falle. Es uno de los vectores más usados porque es corto y automático.

### Payload 3 (extra) — enlace con esquema `javascript:`

```html
<a href="javascript:alert(1)">Hacé click</a>
```

**Cómo funciona:** el esquema `javascript:` en un `href` ejecuta el código cuando el usuario hace click en el enlace. Requiere interacción, pero tampoco usa `<script>`.

### Payload 4 (extra) — input con `onfocus` + autofocus

```html
<input autofocus onfocus="alert(1)">
```

**Cómo funciona:** `autofocus` hace que el campo reciba el foco automáticamente al cargar, lo que dispara `onfocus` sin que el usuario haga nada.

## 3. Conclusión

Bloquear `<script>` es una defensa **inútil** porque confunde un *vector* con la *vulnerabilidad*. El XSS no se produce por una etiqueta específica, sino porque **entrada del usuario se renderiza como HTML/JS activo**. Mientras eso pase, siempre hay otro vector (`onerror`, `onload`, `javascript:`, `onfocus`, y muchos más), y las listas negras siempre quedan atrás. La defensa correcta no es enumerar y bloquear lo malo, sino **codificar la salida** para que el input nunca se interprete como marcado, y reforzarlo con **CSP** (ambos en el Objetivo 3).
