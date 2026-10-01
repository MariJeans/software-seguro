# Objetivo 3: Análisis de Automatización y Fuerza Bruta

## Fuerza bruta vs. Diccionario

Un ataque de **fuerza bruta** es el que prueba de forma sistemática y exhaustiva todas las combinaciones posibles dentro de un alfabeto definido (por ejemplo, minúsculas + números, o un largo de caracteres determinado). Se recorre el espacio de combinaciones entero, una por una, hasta agotarlas todas o hasta encontrar la correcta. En un formulario de login, tanto el `user_name` como la `password` se vuelven variables, y desde Burp Intruder esto se configura con el tipo de ataque **Cluster bomb**, que prueba cada valor de una lista combinado con cada valor de la otra (todas las combinaciones posibles entre ambas). 
El problema es la cantidad de pruebas crece multiplicadamente, y el consumo de recursos más el tiempo puede llegar a ser muy alto, dependemos de la arquitectura de la compu que lo ejecuta, igual puede pasar que no dé abasto.

Un ataque de **diccionario**, es el que se usa hoy en día. Se usan listas de valores reales y probables: contraseñas más comunes, credenciales filtradas, nombres de usuario típicos. Acá en Burp también se arma con listas para `user_name` y `password`, pero en vez de Cluster bomb tiene más sentido usar **Pitchfork**, que avanza las dos listas en paralelo, posición por posición (el user_name número 1 con el password número 1, el 2 con el 2, y así) Es mejor cuando ya tenés alguna de las credenciales conocidas. Esto reduce la cantidad de intentos necesarios, porque en vez de probar todo el universo de combinaciones posibles, apuntás directamente a lo que la gente realmente usa.

## Mecanismo de defensa

Un desarrollador puede mitigar este tipo de automatización implementando un **bloqueo por IP + cuenta**: después de cierta cantidad de intentos fallidos sobre una misma cuenta (o desde una misma IP), se bloquea temporal o permanentemente ese acceso. Otra opción complementaria es agregar un **CAPTCHA** en el formulario de login, que corta la automatización al requerir una verificación que la automatización no puede resolver sola.
