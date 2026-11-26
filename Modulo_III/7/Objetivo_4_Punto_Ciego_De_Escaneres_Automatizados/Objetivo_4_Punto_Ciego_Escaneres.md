# Objetivo 4: El Punto Ciego de los Escáneres Automatizados

**Consigna:** Explicar por qué la lógica de negocio es el mayor "punto ciego" de las herramientas automatizadas (Nessus, Acunetix, el escáner activo de Burp Suite) y por qué la auditoría manual es indispensable en esa etapa.

---

## 1. Para qué son buenos los escáneres automatizados

Herramientas como **Nessus**, **Acunetix** o el **escáner activo de Burp** son muy eficaces detectando fallas **técnicas y repetibles**, que tienen una "firma" reconocible:

- Inyecciones (SQLi, XSS, inyección de comandos) — se prueban con payloads conocidos y se detecta un patrón en la respuesta.
- Configuraciones inseguras (cabeceras faltantes, TLS débil, directory listing, cookies sin flags).
- Versiones de software con CVEs conocidos.
- Archivos o rutas expuestas por defecto.

Todo esto comparte una característica: **es un patrón genérico, independiente de lo que hace la aplicación**. Un `<script>alert(1)</script>` que se refleja es un XSS en un banco, en un blog o en un e-commerce por igual. El escáner no necesita entender el negocio para encontrarlo.

## 2. Por qué la lógica de negocio es el punto ciego

Una **falla de lógica de negocio** es un abuso de las **reglas propias de la aplicación**, no un defecto técnico del código. Y ahí es donde la automatización fracasa, por tres razones:

### 2.1 El escáner no entiende la *intención* del negocio

Para detectar que "un vendedor no debería poder tener 2 ventas asignadas" o que "una cantidad de -5 no tiene sentido" o que "este descuento solo debería usarse una vez", hay que **entender qué significa cada operación en el contexto del negocio**. El escáner solo ve peticiones HTTP y respuestas; no sabe qué es una "venta", un "vendedor" o un "cupón", ni cuáles son las reglas que los gobiernan. No hay un payload universal para "violar una regla de negocio" porque **cada regla es única de cada aplicación**.

### 2.2 No hay una "firma" ni una respuesta anómala que detectar

Las fallas técnicas se delatan: un error SQL en la respuesta, un script que se ejecuta, una cabecera ausente. En cambio, cuando se explota una falla lógica, **el servidor responde con un `200 OK` perfectamente normal** — porque, técnicamente, la petición es válida. Cambiar la cantidad a -5, reasignar un `id_usuario`, canjear un cupón en paralelo: todas son peticiones bien formadas que el servidor procesa sin error. No hay nada "roto" que un patrón pueda reconocer; lo roto es el **resultado de negocio**, y eso el escáner no lo evalúa.

### 2.3 Requiere encadenar pasos y razonar como un humano

Muchas fallas lógicas surgen de **secuencias de acciones legítimas** combinadas de forma inesperada: completar un flujo de compra salteando el paso de pago, usar una función "A" para evitar el control de la función "B" (como el IDOR por una ruta secundaria), o aprovechar una ventana de tiempo (race condition). El escáner prueba inputs aislados; no concibe hipótesis del tipo "¿qué pasa si hago esto *antes* de aquello?" ni improvisa caminos nuevos a partir de lo que observa. Eso requiere **creatividad, contexto e intuición** — razonar como un atacante que entiende el objetivo del sistema.

## 3. Por qué la auditoría manual es indispensable

El auditor humano aporta justamente lo que le falta a la máquina:

- **Comprende el modelo de negocio:** sabe qué reglas e invariantes deberían cumplirse (un saldo no puede ser negativo, un recurso tiene un dueño, un cupón se usa una vez) y, por lo tanto, sabe qué intentar romper.
- **Formula y prueba hipótesis:** "¿y si mando el `id` de otro usuario?", "¿y si lo hago 50 veces en paralelo?", "¿y si me salteo este paso?". Son preguntas que nacen de entender el flujo, no de una base de datos de payloads.
- **Encadena vulnerabilidades:** combina fallas menores (un dato filtrado + un IDOR + un cambio de email) en un ataque completo, algo que el escáner, que evalúa cada issue por separado, no hace.
- **Interpreta el contexto:** distingue un comportamiento esperado de uno que, aunque devuelva `200 OK`, viola una regla y tiene impacto real.

## 4. Conclusión

Los escáneres automatizados son indispensables para la **cobertura amplia y rápida** de fallas técnicas conocidas, pero operan sin entender **qué hace ni qué debería permitir** la aplicación. La lógica de negocio es su punto ciego porque sus fallas no tienen firma, se expresan con peticiones válidas y respuestas normales, y requieren razonamiento contextual y creatividad para descubrirse. Por eso la automatización y la auditoría manual son **complementarias, no sustitutas**: el escáner descarta lo técnico y repetitivo a escala, y el auditor humano se concentra en lo que ninguna herramienta puede ver — el abuso de las reglas del negocio. En seguridad, lo técnico se puede automatizar; el **criterio** todavía no.
