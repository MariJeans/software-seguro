# Objetivo 3: La Única Mitigación Definitiva (Prepared Statements)

**Consigna:** Muchos desarrolladores intentan parchear inyecciones SQL con "listas negras" (bloquear `SELECT`, `UNION`) o escapando comillas. Es ineficiente y evadible. Explicar técnicamente cómo funciona una **Consulta Parametrizada (Prepared Statement)** a nivel de arquitectura, y por qué neutraliza por completo cualquier intento de inyección, sin importar qué caracteres envíe el usuario.

---

## 1. Por qué fallan las listas negras y el escape de comillas

Antes de la solución, por qué los parches comunes no sirven:

- **Listas negras (bloquear palabras):** bloquear `SELECT`, `UNION`, `OR`, etc. es un juego del gato y el ratón imposible de ganar. Siempre hay una forma de evadir: mayúsculas/minúsculas (`SeLeCt`), comentarios intercalados (`UN/**/ION`), codificaciones (hex, URL-encoding), sinónimos o funciones equivalentes. Además, muchas de esas palabras son legítimas en datos normales (alguien se puede apellidar "O'Brien" o escribir "select" en un comentario). Es un enfoque **reactivo** que nunca cubre todos los casos.
- **Escapar comillas manualmente:** poner `\` antes de las comillas parece tapar el agujero, pero se evade (ej. con inyecciones que no necesitan comillas porque el parámetro es numérico o va en un `ORDER BY`, o con trucos de codificación de caracteres). Depende de que el programador escape **bien, siempre, en todos lados** — y basta un olvido para reabrir el hueco.

El problema de fondo de todas estas defensas: **siguen mezclando el código SQL con los datos del usuario en un mismo string**, e intentan "limpiar" los datos a mano. Mientras código y datos vivan juntos en la misma cadena de texto, la inyección es posible.

## 2. La causa raíz de la inyección SQL

Una SQLi ocurre porque el código construye la consulta **concatenando** el input del usuario como texto:

```python
# VULNERABLE
query = "SELECT * FROM usuarios WHERE nombre = '" + input_usuario + "'"
```

Si el usuario escribe `' OR '1'='1`, la cadena resultante es:

```sql
SELECT * FROM usuarios WHERE nombre = '' OR '1'='1'
```

El motor de base de datos recibe **todo junto como un solo texto** y lo interpreta completo. No tiene forma de saber que la parte `' OR '1'='1` era "un dato que escribió el usuario" y no "instrucciones que escribió el programador". **Datos e instrucciones se confundieron en el mismo canal.** Eso es la inyección: datos que el motor termina ejecutando como código.

## 3. Cómo funciona un Prepared Statement a nivel de arquitectura

La consulta parametrizada resuelve el problema **separando en dos canales distintos** la estructura de la consulta (el código) y los valores (los datos). El proceso tiene dos fases:

### Fase 1 — PREPARE (preparar la plantilla)

El programa le envía a la base de datos **primero la consulta con "huecos"** (marcadores de posición / *placeholders*), **sin los datos todavía**:

```python
# SEGURO (parametrizado)
query = "SELECT * FROM usuarios WHERE nombre = ?"
```

El `?` (o `%s`, o `:nombre`, según el lenguaje/driver) es un **parámetro vacío**. En esta fase, la base de datos recibe solo esta plantilla y la **compila/planifica**: analiza la sintaxis, decide la estructura de la consulta (qué tabla, qué condición, qué operación) y arma el **plan de ejecución**. Todo esto ocurre **antes de que exista ningún dato del usuario**. La estructura de la consulta queda **fijada e inmutable** en este momento.

### Fase 2 — EXECUTE (enviar los datos por separado)

Recién después, el programa envía los **valores** por un **canal separado**, asociados a cada marcador:

```python
cursor.execute(query, (input_usuario,))
```

La base de datos toma ese valor y lo **inserta en el hueco ya reservado, tratándolo como DATO PURO**, nunca como SQL a interpretar. La consulta ya estaba compilada; la estructura no se puede modificar a esta altura. El valor se "ata" (*bind*) al parámetro como un literal.

**Analogía:** es como un formulario impreso. Primero se imprime el formulario con sus campos en blanco (la estructura, fija). Después alguien rellena los campos a mano. Por más que en el campo "nombre" escriba una frase larga con instrucciones, **sigue siendo lo que hay escrito en el campo nombre** — no cambia el formulario ni crea campos nuevos.

## 4. Por qué neutraliza CUALQUIER input

Acá está la clave de por qué es definitiva, no importa qué caracteres mande el usuario:

Si el atacante envía `' OR '1'='1` como valor del parámetro, la base **no lo interpreta como SQL**, porque la estructura de la consulta **ya fue compilada y fijada en la Fase 1, antes de ver ese dato**. El valor malicioso se trata como un **string literal**: la base busca, literalmente, un usuario cuyo nombre sea el texto `' OR '1'='1`. Como ese usuario no existe, no devuelve nada. La inyección simplemente **no ocurre**, porque el dato nunca tuvo la oportunidad de cambiar la estructura de la consulta.

La diferencia esencial frente a las listas negras: no se trata de **detectar y bloquear** caracteres peligrosos (lo cual es evadible), sino de que el motor **nunca mira el dato como código**. Los metacaracteres (`'`, `--`, `;`, `UNION`...) pierden todo su poder, no porque se filtren, sino porque llegan por el canal de "datos", donde no tienen significado sintáctico. Da igual lo que el usuario escriba: no hay forma de que un dato salte al canal de las instrucciones.

## 5. Aclaraciones importantes

- **Parametrizar valores, no identificadores:** los prepared statements parametrizan **valores** (lo que va en un `WHERE`, `INSERT`, etc.). **No** se pueden parametrizar nombres de tabla/columna ni palabras clave estructurales (ej. la columna de un `ORDER BY`). Si eso debe ser dinámico, se valida contra una **lista blanca** de valores permitidos, nunca concatenando input.
- **No confiar en el ORM a ciegas:** los ORM (Django, SQLAlchemy, etc.) usan prepared statements por debajo y son seguros en su uso normal, pero si uno escribe SQL crudo concatenando input (`.raw()`, `.extra()` mal usados), vuelve a abrir el agujero.
- **Defensa en profundidad:** los prepared statements son la mitigación principal, pero se combinan con validación de input (tipo y rango), principio de menor privilegio en el usuario de la base, y manejo de errores que no filtre información.

## 6. Conclusión

Las listas negras y el escape de comillas atacan el **síntoma** (caracteres peligrosos) y por eso son evadibles: siguen mezclando código y datos en un mismo string. El prepared statement ataca la **causa raíz**: **separa físicamente la estructura de la consulta de los datos del usuario**, compilando la consulta *antes* de recibir ningún valor. Así, el input del usuario nunca puede reinterpretarse como SQL, sin importar qué caracteres contenga. No es un filtro que hay que mantener actualizado: es un cambio de arquitectura que vuelve la inyección **estructuralmente imposible**. Por eso es la mitigación definitiva.
