# Objetivo 2: Análisis de Manipulación Transaccional (Cantidades Negativas)

**Escenario:** Un e-commerce permite agregar productos al carrito. Al interceptar la petición, se cambia la cantidad del producto de `1` a `-5`. El servidor lo procesa, el total del carrito se vuelve negativo y, en lugar de cobrar, **suma saldo** a la cuenta del atacante. Se analiza por qué ocurre y cómo validar correctamente del lado del servidor.

---

## 1. Por qué ocurre la falla

### 1.1 El total se calcula multiplicando cantidad × precio

El cálculo del carrito es, en esencia:

```
subtotal = precio_unitario * cantidad
```

Si `cantidad` puede ser negativa, el subtotal también lo es:

```
subtotal = 100 * (-5) = -500
```

Un ítem con subtotal negativo **resta** del total del carrito. Si el carrito queda en negativo y el sistema de pago/saldo interpreta ese total como un movimiento a favor del cliente (un reembolso, un crédito, un ajuste), termina **acreditando dinero** en vez de cobrarlo.

### 1.2 La causa raíz: confiar en un dato controlado por el cliente

La `cantidad` viaja en la petición HTTP, que el usuario controla por completo. El atacante la intercepta (con Burp, por ejemplo) y la cambia a `-5` **después** de que el frontend la haya "validado". El fallo central es que el **servidor confía en ese valor sin re-validarlo**: asume que la cantidad siempre es un entero positivo razonable porque "así lo manda el formulario", olvidando que el formulario y sus controles (un `<input type="number" min="1">`, un desplegable, JavaScript) **viven en el navegador y no obligan a nada en el servidor**.

### 1.3 Por qué los controles del frontend no alcanzan

- `min="1"`, `max="99"`, `type="number"` → son atributos HTML que el navegador respeta, pero que se saltan enviando la petición directamente (Burp, curl, DevTools).
- Validación en JavaScript → corre en el cliente; el atacante simplemente no la ejecuta.

Todo control que no se repita en el servidor es, a efectos de seguridad, inexistente. La regla es: **el frontend es para la experiencia de usuario; la seguridad se valida siempre del lado del servidor.**

### 1.4 El problema de diseño detrás del número

Esto es un caso de **Broken Business Logic / Insecure Design**: la lógica de negocio ("un cliente agrega N unidades de un producto") tiene un invariante implícito —la cantidad es un entero ≥ 1— que nunca se expresó como una validación explícita. El sistema modela una operación comercial pero no protege sus reglas, así que un valor sin sentido de negocio (una cantidad negativa) produce un resultado sin sentido de negocio (saldo regalado).

## 2. Cómo debería validar el desarrollador (del lado del servidor)

### 2.1 Validación estricta del campo `cantidad`

En el servidor, antes de calcular nada, la cantidad debe pasar **todas** estas comprobaciones:

1. **Tipo correcto:** que sea un entero. Rechazar strings, decimales, `null`, objetos, arrays. (`-5`, `1.5`, `"abc"`, `1e3` → rechazar lo que no sea entero.)
2. **Límite inferior:** `cantidad >= 1`. Esto elimina de raíz el cero y los negativos.
3. **Límite superior razonable:** `cantidad <= max_por_item` (ej. 99, o el stock disponible). Evita overflow y pedidos absurdos.
4. **Rechazo explícito, no "corrección silenciosa":** si el valor es inválido, devolver un error (HTTP 400) y **no procesar**. No conviene "arreglarlo" en silencio (ej. convertir -5 en 5), porque enmascara el ataque y puede introducir otros bugs.

Ejemplo conceptual (pseudocódigo/Python):

```python
cantidad = request.data.get("cantidad")

# 1. Tipo
if not isinstance(cantidad, int):
    return error(400, "La cantidad debe ser un número entero.")

# 2 y 3. Rango
if cantidad < 1 or cantidad > 99:
    return error(400, "La cantidad debe estar entre 1 y 99.")

# (opcional) 3b. No superar el stock
if cantidad > producto.stock:
    return error(400, "Cantidad mayor al stock disponible.")

# recién ahora se calcula
subtotal = producto.precio * cantidad
```

### 2.2 Defensa en profundidad (más allá del campo)

- **Validación por esquema:** usar un serializer/validador (DRF serializers, Pydantic, JSON Schema, Zod) que declare `cantidad` como entero con `min=1` y `max=N`, para que el rechazo sea automático y centralizado, no un `if` suelto que alguien puede olvidar.
- **Tipos sin signo en la base de datos:** definir la columna como entero sin signo / con un `CHECK (cantidad > 0)`, de modo que ni siquiera una ruta no validada pueda persistir un negativo.
- **Validar el total resultante:** como última red, verificar que el total del carrito y de cada ítem sea `>= 0` antes de confirmar la operación. Un total negativo nunca debería avanzar al paso de pago.
- **Recalcular precios en el servidor:** nunca confiar en el `precio` ni en el `subtotal` que mande el cliente — el servidor debe tomar el precio de su propia base de datos y hacer la cuenta él mismo. (El mismo principio del `cantidad` aplica al `precio`.)
- **No tratar un total negativo como crédito:** el flujo de "acreditar saldo" debe ser un proceso separado y autorizado (reembolsos), nunca una consecuencia automática de un total de carrito negativo.

## 3. Conclusión

La falla no está en que el usuario "pueda escribir -5", sino en que el **servidor acepta y opera sobre un valor que viola una regla de negocio obvia**. Cualquier dato que llegue desde el cliente —cantidad, precio, descuento, id— es **no confiable por definición** y debe validarse estrictamente en el backend: tipo, rango y coherencia con las reglas del negocio. Validar `cantidad >= 1` (y recalcular los montos del lado del servidor) convierte un agujero que regala dinero en un simple error 400.
