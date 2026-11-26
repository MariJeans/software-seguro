# Objetivo 3: Anatomía de una Condición de Carrera (Race Condition)

**Escenario:** Un código de descuento de **un solo uso** que, mediante el envío de ~50 peticiones simultáneas (con herramientas como el **Turbo Intruder** de Burp Suite), se logra canjear **múltiples veces** antes de que el servidor actualice la base de datos. Se analiza cómo y por qué funciona.

---

## 1. Qué es una Race Condition (TOCTOU)

Una **condición de carrera** ocurre cuando el resultado de una operación depende del **orden y el tiempo** en que se ejecutan varias tareas concurrentes. En seguridad, el caso crítico es el **TOCTOU** (*Time Of Check / Time Of Use*): hay una **ventana de tiempo** entre el momento en que el sistema **verifica** una condición (el *check*) y el momento en que **actúa** sobre ella (el *use*).

Si un atacante consigue colar varias operaciones dentro de esa ventana, todas ven el mismo estado "válido" y actúan sobre él antes de que ninguna lo haya modificado. El sistema termina haciendo algo que, en condiciones normales (una operación a la vez), jamás permitiría.

## 2. Por qué un cupón de un solo uso es vulnerable

El servidor, al canjear el código, suele ejecutar una lógica de **dos pasos no atómicos**:

```
1. CHECK:  SELECT usado FROM cupones WHERE codigo = 'DESC50';
           → ¿usado == false?  (sí → seguir)
2. USE:    aplicar el descuento al pedido
           UPDATE cupones SET usado = true WHERE codigo = 'DESC50';
```

El problema: entre el paso 1 (leer que el cupón **no** fue usado) y el paso 2 (marcarlo como usado y aplicar el descuento) pasa un instante. Si en ese instante llegan **muchas peticiones a la vez**, todas ejecutan el `CHECK` **antes** de que cualquiera haya ejecutado el `UPDATE`. Todas leen `usado == false`, todas pasan la validación y todas aplican el descuento. El cupón "de un solo uso" se canjea N veces.

```
Petición A:  CHECK (usado=false) ──┐
Petición B:  CHECK (usado=false) ──┤── todas leen "libre"
Petición C:  CHECK (usado=false) ──┘
                                    ↓
Petición A:  USE → descuento + UPDATE usado=true
Petición B:  USE → descuento   (ya había leído false)
Petición C:  USE → descuento   (ya había leído false)
```

La causa raíz es la **falta de atomicidad y de control de concurrencia**: la comprobación y la actualización no se ejecutan como una única operación indivisible, ni hay un bloqueo que impida que dos transacciones toquen el mismo cupón al mismo tiempo.

## 3. Cómo lo explota un atacante con Turbo Intruder

El desafío técnico del atacante es que las 50 peticiones lleguen **lo más juntas posible** — idealmente en el mismo milisegundo — para maximizar la cantidad que cae dentro de la ventana TOCTOU. Si las manda una tras otra (secuencial), la primera ya marcó el cupón como usado antes de que llegue la segunda, y no hay race.

**Turbo Intruder** es una extensión de Burp Suite diseñada para esto: permite enviar miles de peticiones con alta concurrencia y control fino del tiempo, programando el ataque en Python.

El flujo típico:

1. **Capturar la petición de canje** en Burp (ej. `POST /aplicar-cupon/` con `{"codigo": "DESC50"}`) y enviarla a Turbo Intruder.
2. **Configurar el motor de envío** para que abra muchas conexiones en paralelo y **retenga** las peticiones hasta disparar todas juntas. Ejemplo de script de Turbo Intruder:

   ```python
   def queueRequests(target, wordlists):
       # concurrentConnections alto para paralelizar
       engine = RequestEngine(endpoint=target.endpoint,
                              concurrentConnections=30,
                              requestsPerConnection=100,
                              pipeline=False)

       # Encolar 50 copias idénticas de la misma petición
       for i in range(50):
           engine.queue(target.req, gate='canje')

       # Soltar las 50 EN EL MISMO INSTANTE
       engine.openGate('canje')

   def handleResponse(req, interesting):
       table.add(req)
   ```

   La clave es el **"gate"** (`gate='canje'` + `openGate`): Turbo Intruder encola las 50 peticiones pero las **retiene** en la compuerta, y al abrirla las libera todas de golpe, sincronizadas.

3. **Técnica single-packet attack:** en HTTP/2, Burp puede ir un paso más allá y meter varias peticiones en un **único paquete TCP**, eliminando casi por completo la variabilidad de la red (el *jitter*). Así las peticiones llegan al servidor literalmente en el mismo instante, lo que dispara la tasa de éxito de la race.

4. **Leer los resultados:** en la tabla de respuestas, si el cupón se canjeó varias veces, se verán **múltiples respuestas 200/"descuento aplicado"** en lugar de una sola seguida de 49 errores "cupón ya usado".

## 4. Por qué funciona: la ventana de tiempo

El éxito del ataque depende de que la ventana entre `CHECK` y `USE` sea más larga que la diferencia de llegada entre las peticiones. Factores que la agrandan (y que el atacante aprovecha): consultas lentas, falta de índices, lógica de negocio pesada entre la lectura y la escritura, y ausencia de bloqueos. El single-packet attack ataca el otro lado de la ecuación: reduce casi a cero la separación temporal entre peticiones.

## 5. Cómo se defiende el desarrollador

La solución es garantizar **atomicidad** y **control de concurrencia**, para que "comprobar y usar" sea una sola operación indivisible:

1. **Operación atómica en la base de datos.** En lugar de leer y luego escribir, hacer el `UPDATE` condicional en un solo paso y comprobar cuántas filas afectó:
   ```sql
   UPDATE cupones SET usado = true
   WHERE codigo = 'DESC50' AND usado = false;
   ```
   Si devuelve **1 fila afectada**, el canje es válido; si devuelve **0**, otro ya lo usó. Solo la primera petición de la carrera afecta una fila; las demás obtienen 0 y se rechazan. La base de datos serializa este `UPDATE`, así que no hay ventana que explotar.

2. **Bloqueo de fila (pessimistic locking).** `SELECT ... FOR UPDATE` dentro de una transacción bloquea la fila del cupón: la segunda petición concurrente espera hasta que la primera termina y confirma, momento en el cual ya ve `usado = true`.

3. **Transacciones con nivel de aislamiento serializable.** Fuerzan que las transacciones concurrentes se comporten como si corrieran una tras otra; la base aborta las que entran en conflicto.

4. **Restricciones de unicidad.** Si cada canje genera un registro (ej. `redenciones(codigo, pedido_id)`), una constraint `UNIQUE` sobre el código impide físicamente insertar un segundo canje.

5. **Rate limiting / idempotencia.** Como defensa en profundidad: limitar la cantidad de intentos de canje por usuario/segundo, y usar claves de idempotencia para que peticiones duplicadas no se procesen dos veces. (No reemplazan la atomicidad, pero reducen la superficie.)

## 6. Conclusión

Una race condition no explota un dato malicioso ni un fallo de permisos, sino el **tiempo**: la ventana entre verificar un estado y actuar sobre él. Toda regla de "una sola vez" —cupón de un uso, un voto por persona, un retiro de saldo, una unidad de stock— es vulnerable si la comprobación y la actualización no son atómicas. Herramientas como Turbo Intruder (y el single-packet attack) existen justamente para demostrarlo, enviando decenas de peticiones sincronizadas que caen todas dentro de esa ventana. La defensa no pasa por validar "mejor" el input, sino por hacer la operación **indivisible** a nivel de base de datos.
