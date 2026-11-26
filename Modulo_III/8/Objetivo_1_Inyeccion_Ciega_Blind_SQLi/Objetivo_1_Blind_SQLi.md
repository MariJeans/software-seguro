# Objetivo 1: El Arte de la Inyección Ciega (Blind SQLi)

**Consigna:** Explicar la diferencia técnica entre una inyección **Boolean-Based Blind** y una **Time-Based Blind**, y cómo un atacante extrae el nombre de una base de datos letra por letra cuando la aplicación solo responde con una pantalla genérica de "Cargando...".

---

## 1. Qué es una inyección SQL "a ciegas" (Blind SQLi)

En una inyección SQL **clásica**, la aplicación devuelve los datos o los errores directamente en pantalla: el atacante ve el resultado de su consulta (o un error de SQL que lo guía). En una inyección **ciega (blind)**, eso no pasa: la aplicación **sí es vulnerable** (la consulta se inyecta y se ejecuta en la base), pero **no muestra ni los datos ni los errores**. La pantalla responde siempre con algo genérico: un "Cargando...", un "OK", o la misma página sin cambios visibles.

El atacante entonces no puede *leer* la respuesta de la base directamente. Lo que hace es **hacerle preguntas de sí/no a la base de datos** y deducir la respuesta observando **cómo se comporta la aplicación**, no lo que muestra. De ahí el nombre: ataca "a ciegas", infiriendo los datos de forma **indirecta**.

## 2. Boolean-Based Blind (basada en verdadero/falso)

Aquí el atacante aprovecha que la aplicación **se comporta de forma distinta según si la condición inyectada es verdadera o falsa**, aunque no muestre datos.

La idea: se inyecta una condición booleana y se observa una **diferencia detectable** en la respuesta:

- Si la condición es **verdadera** → la página carga normal, aparece un contenido, o devuelve `200 OK` con cierto texto.
- Si la condición es **falsa** → la página cambia: no aparece el contenido, sale un mensaje distinto, o la respuesta es diferente en longitud.

Ejemplo conceptual. Partiendo de una consulta como:

```sql
SELECT * FROM productos WHERE id = '<input>';
```

El atacante inyecta:

```
' AND 1=1 --      → condición VERDADERA → la página responde "normal"
' AND 1=2 --      → condición FALSA     → la página responde "distinta"
```

Si nota la diferencia entre ambos, confirma que puede **preguntar cualquier cosa** a la base y leer la respuesta en ese "canal" de verdadero/falso. La clave: la **respuesta HTTP cambia** según el valor booleano.

## 3. Time-Based Blind (basada en tiempo)

A veces la aplicación responde **exactamente igual** sea verdadera o falsa la condición (misma página, mismo texto, misma longitud). No hay diferencia visible que observar. En ese caso, el atacante crea una diferencia **artificial** que sí puede medir: el **tiempo de respuesta**.

Se inyecta una condición que, **si es verdadera**, le ordena a la base **esperar** unos segundos antes de responder (con una función de retardo). Si la respuesta tarda, la condición era verdadera; si responde al instante, era falsa.

Funciones de retardo típicas según el motor:

- **MySQL:** `SLEEP(5)` — o `IF(condición, SLEEP(5), 0)`
- **PostgreSQL:** `pg_sleep(5)`
- **SQL Server:** `WAITFOR DELAY '0:0:5'`

Ejemplo (MySQL):

```
' AND IF(1=1, SLEEP(5), 0) --   → la respuesta TARDA 5 s  → condición verdadera
' AND IF(1=2, SLEEP(5), 0) --   → la respuesta es INSTANTÁNEA → condición falsa
```

El canal de información ya no es el *contenido* de la respuesta, sino **cuánto tarda**. Por eso la Time-Based sirve incluso cuando la página es idéntica en ambos casos — es la técnica a usar frente a esa pantalla genérica de "Cargando..." que nunca cambia.

### Diferencia técnica resumida

| | Boolean-Based | Time-Based |
|---|---|---|
| Canal que observa el atacante | El **contenido/forma** de la respuesta (cambia según V/F) | El **tiempo** de respuesta (retardo artificial con SLEEP) |
| Cuándo se usa | La página responde distinto según V/F | La página responde **igual** siempre (no hay diferencia visible) |
| Velocidad | Más rápida (respuesta inmediata) | Más lenta (hay que esperar el retardo en cada prueba) |
| Fiabilidad | Alta si la diferencia es estable | Sensible a la latencia de red / carga del servidor |

## 4. Cómo se extrae el nombre de la base letra por letra

Como el atacante solo puede hacer preguntas de **sí/no**, extrae cualquier dato **carácter por carácter**, y cada carácter lo averigua **bit a bit o por comparación**, usando funciones de SQL para aislar una letra y preguntar por su valor.

Las piezas de SQL que usa:

- `DATABASE()` (MySQL) → devuelve el nombre de la base actual.
- `SUBSTRING(texto, posición, 1)` → extrae **un solo carácter** de ese texto en una posición dada.
- `ASCII(carácter)` → convierte ese carácter en su número ASCII (ej. `a` = 97).
- Comparadores `>`, `<`, `=` → para hacer la pregunta de sí/no.

El proceso (ejemplo con Time-Based, misma lógica para Boolean):

1. **Averiguar el 1er carácter.** Se pregunta por su valor ASCII, acotando con comparaciones (**búsqueda binaria** para ir rápido):
   ```
   ' AND IF(ASCII(SUBSTRING(DATABASE(),1,1)) > 109, SLEEP(5), 0) --
   ```
   - ¿Tardó? → el 1er carácter tiene ASCII > 109. ¿No tardó? → es ≤ 109.
   - Se repite partiendo el rango a la mitad cada vez (¿> 115? ¿> 112?...) hasta clavar el número exacto, ej. ASCII 115 = **`s`**.
2. **Pasar al 2º carácter:** se cambia la posición en `SUBSTRING(DATABASE(), 2, 1)` y se repite la búsqueda.
3. **Continuar** posición por posición (3, 4, 5...) hasta reconstruir todo el nombre: `s` → `h` → `o` → `p` → ... = `shop`.
4. **Saber cuándo terminar:** cuando `SUBSTRING` en la siguiente posición devuelve vacío (o se pregunta primero por la longitud con `LENGTH(DATABASE())`), el atacante sabe cuántos caracteres tiene y cuándo parar.

El uso de **búsqueda binaria** (preguntar "¿es mayor que el valor del medio?") en lugar de probar carácter por carácter (¿es `a`? ¿es `b`?...) reduce drásticamente la cantidad de peticiones: ~7 preguntas por carácter en vez de hasta ~95.

Como esto son **miles de peticiones repetitivas**, en la práctica se automatiza con herramientas como **sqlmap**, o con scripts/Intruder de Burp — nadie lo hace a mano salvo para entender el mecanismo.

## 5. Conclusión

La inyección ciega demuestra que una aplicación puede ser **totalmente explotable sin mostrar jamás un dato ni un error**. Mientras el comportamiento del servidor dependa, aunque sea mínimamente, del resultado de una consulta inyectada —en su **contenido** (Boolean-Based) o en su **tiempo de respuesta** (Time-Based)—, el atacante tiene un canal de sí/no suficiente para extraer, carácter por carácter, cualquier información de la base: nombres de bases, tablas, columnas y hasta los datos. Una pantalla de "Cargando..." no es protección; la única defensa real es **consultas parametrizadas (prepared statements)** que impidan que el input se interprete como SQL.
