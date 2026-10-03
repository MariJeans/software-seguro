# Lab: Apagar la IA

## Resolución

El desafío arranca con una lista de números y, pegado a la URL, un hash — eso fue lo primero que identifiqué: el dato que realmente importa en el enunciado no son los números sueltos, sino que la URL trae un hash (`/codes/0e1422ea79781ee046484893ce0010c4/`) que hay que revertir para avanzar.

![Lista de códigos y hash en la URL](./capturas/Lab_apagar-ia_1.png)

Para confirmar qué número representaba ese hash, lo probé en **CrackStation** (crackeador de hashes online, gratuito, con diccionarios precargados). Cargué el hash y lo identificó como MD5, devolviendo el número `9912`.

![Hash crackeado en CrackStation, resultado 9912](./capturas/Lab_apagar-ia_2.png)

Con ese primer resultado hice la prueba manual de ir subiendo y bajando el número directamente en la URL (`/codes/<hash>/`) para ver hasta dónde el servidor seguía devolviendo contenido válido y en qué punto dejaba de reconocer el código — así fui acotando un rango aproximado de números donde tenía sentido buscar, en vez de salir a probar al azar.

Para no tener que ir probando número por número a mano, armé un script en Python (`generar_hashes.py`) que genera el hash MD5 de cada número dentro de un rango definido y los vuelca a un archivo de texto. Lo corrí para el rango **9000 a 12000**, que es la base de datos de hashes que después usé como diccionario para el ataque.

![Script en Python generando el listado de hashes](./capturas/Lab_apagar-ia_3.png)

Con el diccionario de hashes ya armado, pasé a Burp Suite: prendí el proxy, intercepté la petición GET que pide el código, y la mandé a **Intruder**.

![Petición GET interceptada, enviada a Intruder](./capturas/Lab_apagar-ia_4.png)

Dentro de Intruder, en la pestaña Positions, marqué el hash dentro de la URL como la variable a reemplazar en cada intento (ataque tipo Sniper, una sola posición).

![Hash marcado como variable en Intruder](./capturas/Lab_apagar-ia_5.png)

El paso siguiente fue configurar en Settings un **Grep - Extract**, para que Burp no solo me diga qué status code devuelve cada intento, sino que además me muestre, extraído directamente en la tabla de resultados, el dato que me interesa: agregué una expresión regular (`(<li>\d{16}<li>)`) para capturar un código de 16 dígitos si aparecía en la respuesta — esa iba a ser la señal de que encontré el hash correcto.

![Configuración de Grep - Extract con la expresión regular](./capturas/Lab_apagar-ia_6.png)

En Payloads cargué el diccionario de hashes generado por el script como una lista simple (Simple list), apuntando a la posición marcada en la URL.

![Lista de hashes cargada como payload](./capturas/Lab_apagar-ia_7.png)

Ejecuté el ataque y revisé los resultados: la columna del Grep - Extract hizo el filtro solo, mostrando enseguida en qué intento apareció el código de 16 dígitos en la respuesta — eso significó haber encontrado el hash real entre los miles de intentos generados.

*(Pendiente: agregar la captura del ataque ejecutado en Burp Intruder con el resultado extraído.)*

Con el código de 16 dígitos ya obtenido (`5524663362514956`), el último paso era generar su hash MD5, que es lo que pedía el desafío como respuesta final.

![Generación del MD5 del código de 16 dígitos](./capturas/Lab_apagar-ia_9.png)

El MD5 resultante fue: **`a8e0e8ff02dde0f62fdf4de5142d7de0`**

## Resumen del proceso

En definitiva, todo el laboratorio fue un ejercicio de fuerza bruta guiado: primero reconocer que el dato clave era un hash, confirmar manualmente con una herramienta online que el hash correspondía a un número dentro de un rango razonable, automatizar la generación de ese rango completo de hashes con un script propio, y usar Burp Intruder para probar automáticamente cada uno contra el servidor hasta que la respuesta — filtrada con una expresión regular — reveló el código de 16 dígitos que llevaba a la solución final.
