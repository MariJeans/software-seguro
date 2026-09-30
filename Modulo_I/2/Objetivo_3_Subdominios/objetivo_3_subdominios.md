# Objetivo 3: Reconocimiento Cotidiano (Subdominios en uso)

La idea de este objetivo es darme cuenta de que esto que venimos viendo en el curso no es solo teoría de laboratorio: lo uso todos los días sin prestarle atención. Repasé las apps que abro habitualmente y encontré varias que corren bajo subdominios bien claros. Marco en **negrita** la parte que es el subdominio en cada URL.

## 1. Gmail
`https://`**`mail`**`.google.com`

El correo de Google vive en el subdominio `mail`, colgado del dominio raíz `google.com` (que a su vez tiene un montón de otros servicios en otros subdominios, como voy a mostrar abajo).

## 2. Google Drive
`https://`**`drive`**`.google.com`

Mismo dominio raíz que Gmail (`google.com`), pero un subdominio distinto (`drive`) porque es un servicio completamente diferente corriendo por separado.

## 3. Notion
`https://`**`app`**`.notion.com`

Acá el subdominio es `app` — es donde vivo trabajando el tracking del curso y organizando notas.

## 4. Plataforma del curso de ciberseguridad
`https://`**`app`**`.softwareseguro.com.ar`

Este es el que uso a diario ahora para entrar a los laboratorios. Interesante que el mismo dominio (`softwareseguro.com.ar`) tiene *otro* subdominio distinto para otra función:

`https://`**`courses`**`.softwareseguro.com.ar`

Ahí es donde entrego los objetivos y veo el contenido de las clases. Dos subdominios, mismo dominio raíz, cada uno con un propósito distinto — justo el patrón de arquitectura que pide identificar la consigna.

## 5. LinkedIn
`https://`**`www`**`.linkedin.com`

Este es un poco más sutil porque `www` es tan común que a veces ni lo pensamos como subdominio, pero técnicamente lo es: es el subdominio por convención que apunta a la versión pública del sitio.

---

**En resumen:** lo que tienen en común todos estos casos es que la empresa no mete todo bajo un solo dominio plano — separa cada función o producto (correo, almacenamiento, la app en sí, la parte de contenido/cursos) en su propio subdominio. Esto no es casualidad: permite manejar cada uno con su propia infraestructura, certificados y hasta equipos de desarrollo distintos, aunque todos cuelguen del mismo dominio raíz.
