# Objetivo 3 — Directory Listing (Listado de Directorios)

> **Curso:** Ciberseguridad Web y Ethical Hacking (UTN / Software Seguro)
> **Módulo / Objetivo:** Security Misconfiguration — Directory Listing
> **Autora:** María de los Ángeles Acuña — QA Tester
> **Fecha:** Octubre 2026

---

## 1. ¿Qué es el Directory Listing?

El **Directory Listing** (también llamado *Directory Indexing* o *listado de directorios*)
es una funcionalidad del servidor web que, cuando está habilitada, muestra
automáticamente el **contenido de una carpeta** (la lista de archivos y subcarpetas
que hay dentro) cuando el usuario navega a esa ruta y **no existe un archivo de índice**
que mostrar en su lugar.

Un archivo de índice es el que el servidor sirve por defecto al entrar a un directorio,
típicamente:

- `index.html`
- `index.php`
- `index.htm`, `default.html`, etc.

Cuando el directorio **sí tiene** uno de estos archivos, el servidor lo muestra y el
usuario nunca ve la estructura interna de la carpeta. El problema aparece cuando el
directorio **no tiene** ningún archivo de índice y la directiva de listado está activa.

---

## 2. ¿Qué ocurre técnicamente cuando se navega a un directorio sin índice?

Cuando un atacante (o cualquier visitante) solicita una URL que apunta a un **directorio**
en lugar de a un archivo concreto, el servidor web sigue este razonamiento:

1. **El cliente pide el directorio.**
   Por ejemplo: `GET /uploads/ HTTP/1.1`

2. **El servidor busca un archivo de índice por defecto** dentro de esa carpeta
   (`index.html`, `index.php`, etc.), según la lista configurada en la directiva
   `DirectoryIndex` (Apache) o `index` (Nginx).

3. **Dos caminos posibles:**
   - **Si encuentra el archivo de índice** → lo sirve normalmente (ej. muestra la web).
   - **Si NO encuentra ningún archivo de índice**, entra en juego la configuración de
     listado:
     - Si el listado está **deshabilitado** (lo correcto) → el servidor responde con un
       **`403 Forbidden`** (acceso prohibido). No revela nada del contenido.
     - Si el listado está **habilitado** (la mala configuración) → el servidor
       **genera dinámicamente una página HTML** con la **lista completa de todos los
       archivos y subcarpetas** de ese directorio, con enlaces para descargar o abrir
       cada uno, y normalmente su fecha de modificación y su tamaño.

### ¿Quién genera ese listado? (la directiva concreta)

- **Apache:** lo produce el módulo **`mod_autoindex`**, activado con la opción
  **`Options +Indexes`** (en la configuración o en un archivo `.htaccess`).
- **Nginx:** lo produce la directiva **`autoindex on;`** dentro de un bloque `location`
  o `server`.

En ambos casos, el servidor arma al vuelo una página que es, literalmente, un
**índice navegable del sistema de archivos** de esa carpeta expuesto al público.

### Por qué es un problema de seguridad

El atacante obtiene, **sin autenticarse y sin explotar ninguna vulnerabilidad de código**,
un mapa directo de qué archivos existen en el servidor. Esto rompe el principio de
seguridad conocido como **“security by obscurity”** mal aplicado: el desarrollador
asumía que nadie iba a “adivinar” el nombre de un archivo, pero el listado se lo entrega
al visitante en bandeja. Es un caso típico de **fuga de información** que facilita
ataques posteriores.

> Conexión con lo visto en clase: en la etapa de **Reconocimiento / Content Discovery**
> usamos herramientas como **ffuf** y **feroxbuster** con diccionarios de **SecLists**
> justamente para descubrir directorios ocultos. Cuando uno de esos directorios tiene el
> listado habilitado, el trabajo del atacante se simplifica enormemente: en vez de
> adivinar nombres de archivo uno por uno, el servidor le muestra todos de una vez.

---

## 3. ¿Cómo se detecta en la práctica?

1. **Navegación manual / "fuzzing" de directorios:** probar rutas comunes en el navegador
   o con herramientas de content discovery.

   ```bash
   # Descubrir directorios (visto en clase)
   ffuf -u https://sitio-objetivo.com/FUZZ -w SecLists/Discovery/Web-Content/common.txt

   feroxbuster -u https://sitio-objetivo.com -w SecLists/Discovery/Web-Content/raft-small-words.txt
   ```

2. **Señal visual:** al entrar a la carpeta aparece un título tipo
   **"Index of /nombre-carpeta"** con una tabla de archivos, fechas y tamaños, y al pie
   suele verse la firma del servidor (ej. `Apache/2.4.56 (Debian) Server at ...`).

3. **Señal por código de estado:** un directorio sin índice devuelve `200 OK` con el
   listado (vulnerable), mientras que uno bien configurado devuelve `403 Forbidden`.

---

## 4. ¿Qué tipo de archivos sensibles podrían quedar expuestos?

Al exponer el contenido de las carpetas, suelen quedar visibles archivos que **nunca
deberían ser públicos**. Los más críticos:

| Tipo de archivo | Ejemplos | Por qué es peligroso |
|---|---|---|
| **Copias de seguridad / backups** | `index.php.bak`, `config.old`, `web.zip`, `backup.tar.gz` | Pueden contener **código fuente** o la base de datos entera. Un `.bak` de un `.php` a veces se descarga como texto plano y revela la lógica interna. |
| **Variables de entorno** | `.env` | Suelen guardar **credenciales de base de datos, claves de API, tokens, secretos de la app** en texto plano. |
| **Volcados de base de datos** | `database.sql`, `dump.sql`, `users.sql` | Exponen **datos sensibles de usuarios (PII)**, hashes de contraseñas, estructura de tablas. |
| **Archivos de configuración** | `config.php`, `wp-config.php`, `settings.ini`, `.htaccess` | Contienen cadenas de conexión, usuarios y contraseñas de servicios. |
| **Carpetas de control de versiones** | `.git/`, `.svn/` | Permiten **reconstruir todo el código fuente** y ver el historial de cambios (incluidos secretos borrados “a medias”). |
| **Logs** | `error.log`, `access.log`, `debug.log` | Revelan rutas internas, errores con *stack traces*, IPs, y a veces datos de sesión. |
| **Documentos internos / subidas** | PDFs, planillas, facturas, DNI, avatares, documentos de usuarios en `/uploads/` | Fuga directa de **información confidencial** de la organización o de sus clientes. |
| **Código fuente y scripts** | `.py`, `.sh`, `.js` internos, instaladores | Exponen lógica de negocio y posibles credenciales hardcodeadas. |

El patrón común: todos son archivos que el desarrollador **asumió que nadie vería**,
pero que el listado de directorios deja al descubierto.

---

## 5. Impacto y clasificación

- **Tipo de fuga:** Divulgación de información (Information Disclosure). Por sí mismo no
  da acceso al sistema, pero **habilita y acelera** ataques posteriores (robo de
  credenciales desde un `.env`, reconstrucción del código desde `.git/`, acceso a datos
  desde un `.sql`).
- **OWASP Top 10:** **A05:2021 — Security Misconfiguration** (Configuración de Seguridad
  Incorrecta).
- **CWE:** **CWE-548 — Exposure of Information Through Directory Listing**.
- **Severidad:** generalmente **Media**, pero puede escalar a **Alta/Crítica** según lo
  que haya expuesto (un `.env` con credenciales productivas o un dump de la base de datos
  elevan el impacto de inmediato).

---

## 6. ¿Cómo se mitiga?

La mitigación tiene dos frentes: **apagar el listado** y **no dejar archivos sensibles
accesibles** por la web.

### 6.1. Deshabilitar el listado de directorios

**Apache** — quitar la opción `Indexes` (nótese el signo menos):

```apache
# En httpd.conf, en el VirtualHost o en un .htaccess del directorio
<Directory /var/www/html>
    Options -Indexes
</Directory>
```

**Nginx** — apagar la directiva (o directamente no activarla, ya que viene apagada por
defecto):

```nginx
location / {
    autoindex off;
}
```

### 6.2. Garantizar un archivo de índice

Colocar un `index.html` (aunque sea vacío o con una redirección) en los directorios que
no deberían listarse, para que el servidor nunca caiga en el comportamiento de listado.

### 6.3. Sacar de la raíz web lo que no debe ser público

- **No alojar** backups, `.env`, dumps `.sql` ni configuraciones dentro del *document root*
  (la carpeta que sirve la web). Guardarlos fuera del alcance del servidor web.
- **Bloquear por extensión** el acceso a archivos sensibles:

  ```apache
  # Apache: denegar el acceso a extensiones peligrosas
  <FilesMatch "\.(env|bak|old|sql|config|ini|log|git)$">
      Require all denied
  </FilesMatch>
  ```

- **Aplicar el principio de mínimo privilegio** en permisos de archivos y carpetas.
- **No desplegar la carpeta `.git/`** en el servidor de producción.

### 6.4. Verificación (re-test)

Después de aplicar la corrección, confirmar que:

- Al entrar a un directorio sin índice el servidor responde **`403 Forbidden`** (o un
  `404`), **no** un listado `200 OK` con los archivos.
- Los archivos sensibles conocidos (`.env`, `.bak`, `.sql`, `.git/`) **no** son
  accesibles directamente por URL.

---

## 7. Conclusión

El Directory Listing es un error de **configuración del servidor** (no de código): basta
con que una directiva (`Options +Indexes` en Apache o `autoindex on;` en Nginx) quede
activada y que una carpeta no tenga archivo de índice para que todo su contenido quede
expuesto al público. Aunque no otorga acceso directo al sistema, es una **puerta de
entrada** que le entrega al atacante un mapa de archivos sensibles —backups, `.env`,
dumps de base de datos, `.git/`— que suelen ser el primer paso hacia un compromiso mayor.
La mitigación es simple y debería formar parte del *hardening* básico de cualquier
servidor antes del pase a producción: **deshabilitar el listado y sacar de la web todo
archivo que no deba ser público.**

---

## Referencias

- OWASP Top 10 — A05:2021 Security Misconfiguration.
- CWE-548 — Exposure of Information Through Directory Listing.
- Apache HTTP Server — documentación de `mod_autoindex` y de la directiva `Options`.
- Nginx — documentación del módulo `ngx_http_autoindex_module`.
- OWASP Web Security Testing Guide — *Review Old Backup and Unreferenced Files for Sensitive Information*.
