# Objetivo 1: Puertos y Servicios Esenciales


## Puerto 20 — FTP (datos)
Es el canal por donde viaja el contenido real cuando se transfiere un archivo por FTP en modo activo. No lleva comandos, solo la data en sí. Va de la mano con el puerto 21.

## Puerto 21 — FTP (control)
Acá es donde el cliente FTP manda los comandos: login, listar carpetas, subir o bajar archivos, etc. El problema histórico de FTP es que por defecto viaja todo sin cifrar — usuario, contraseña y comandos en texto plano, así que es un clásico a la hora de buscar credenciales sniffeadas.

## Puerto 22 — SSH
Acceso remoto a una terminal, pero cifrado. Reemplazó a Telnet justamente por eso. También se usa para transferir archivos de forma segura (SCP, SFTP) y para túneles. Si está abierto, un vector típico es probar fuerza bruta de credenciales o claves débiles.

## Puerto 23 — Telnet
El abuelo de SSH: hace lo mismo (acceso remoto a una terminal) pero sin ningún tipo de cifrado. Ver este puerto abierto en un pentest casi siempre es una bandera roja, porque implica que las credenciales viajan en texto plano.

## Puerto 25 — SMTP
El protocolo que usan los servidores de correo para *enviar* mails (tanto de cliente a servidor como entre servidores). Un SMTP mal configurado puede terminar funcionando como relay abierto y ser usado para mandar spam o phishing en nombre de otro dominio.

## Puerto 53 — DNS
Es el que traduce nombres de dominio (como google.com) a direcciones IP. Corre tanto sobre UDP (consultas normales, más rápidas) como sobre TCP (para transferencias de zona o respuestas más pesadas). Un DNS mal asegurado puede filtrar información interna de la red vía transferencia de zona, o ser blanco de cache poisoning.

## Puerto 80 — HTTP
El tráfico web de toda la vida, sin cifrar. Todo lo que viaja por acá —cookies, formularios, sesiones— puede ser leído por cualquiera que esté interceptando el tráfico, que es justo lo que veníamos haciendo con Burp en los objetivos anteriores.

## Puerto 110 — POP3
Protocolo para que un cliente de correo *reciba* mensajes desde el servidor. La particularidad de POP3 es que en su uso clásico descarga los mails al dispositivo y los borra del servidor (a diferencia de IMAP, que los deja sincronizados ahí). Al igual que FTP y Telnet, en su versión sin cifrar manda todo en texto plano.

## Puerto 443 — HTTPS
Lo mismo que el puerto 80, pero envuelto en TLS. Es el que estuvimos analizando en el Objetivo 3 con el handshake: primero se negocia la parte cifrada y recién después viaja el tráfico HTTP real, protegido de que alguien en el medio pueda leerlo o modificarlo sin el certificado correspondiente.

## Puerto 3306 — MySQL
El puerto por defecto del motor de base de datos MySQL (y su fork MariaDB). No debería estar expuesto a internet en un entorno de producción bien configurado; si aparece abierto públicamente en un scan, es una señal de que vale la pena revisar si acepta conexiones remotas con credenciales débiles o por defecto.

