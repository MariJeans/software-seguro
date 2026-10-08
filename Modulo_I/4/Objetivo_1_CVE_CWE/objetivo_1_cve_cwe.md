# Objetivo 1: Estandarización de Vulnerabilidades (CVE y CWE)

## ¿Qué es un CVE?

**CVE** (Common Vulnerabilities and Exposures) es un identificador único que se le asigna a una vulnerabilidad **específica**, ya detectada en un producto o versión de software concreto. Básicamente es el "DNI" de esa falla puntual: cuando varias fuentes —un fabricante, un investigador, una herramienta de escaneo— hablan de la misma vulnerabilidad, el ID CVE es lo que permite confirmar que están hablando exactamente de lo mismo, sin ambigüedad.

El formato es siempre `CVE-AAAA-NNNNN` (el año de asignación y un número correlativo), por ejemplo `CVE-2021-44228` (el famoso Log4Shell). Cada entrada CVE trae, como mínimo, una descripción de la falla, el producto/versión afectado y referencias a parches o avisos oficiales.

## ¿Qué es el catálogo CWE?

**CWE** (Common Weakness Enumeration) es distinto: no cataloga vulnerabilidades puntuales encontradas en un software real, sino **tipos de debilidad genéricos** a nivel de diseño o código que pueden dar origen a una vulnerabilidad. Es más bien una taxonomía de "patrones de error" que cualquier desarrollador puede cometer, independientemente del producto.

Por ejemplo, `CWE-89` es "SQL Injection" como categoría general — el patrón de no sanitizar entradas antes de armar una query. Un CVE concreto (una inyección SQL real encontrada en, digamos, un plugin de WordPress específico) después se puede **mapear** a ese CWE, porque esa es la debilidad de código que la hizo posible.

## La diferencia en una frase

El CWE es la **causa raíz / categoría del error** (el "por qué" a nivel de patrón de diseño/código), y el CVE es la **instancia real** de esa debilidad explotada en un software concreto, con su propio ID. Un mismo CWE puede estar detrás de miles de CVEs distintos — es la relación de "clase" contra "objeto instanciado", para pensarlo con términos que uso todo el tiempo en testing.

## Quiénes asignan los CVE: las CNA

Los CVE no los asigna cualquiera: los otorgan las **CNA (CVE Numbering Authorities)**, que son organizaciones autorizadas por el programa CVE (actualmente coordinado por MITRE, bajo patrocinio de CISA/DHS en EE.UU.) para asignar IDs dentro de su propio alcance de productos. Entre las CNA hay:

- Grandes fabricantes de software/hardware (Microsoft, Google, Red Hat, Apple, Cisco, entre muchos otros), que asignan CVEs para vulnerabilidades en sus propios productos.
- MITRE como CNA de respaldo (CNA-LR), para los casos que no caen dentro del alcance de ninguna CNA específica.
- Equipos de respuesta a incidentes (CERTs) y empresas de investigación de seguridad que también tienen el rol habilitado.

## Dónde se consultan públicamente

- **NVD** (National Vulnerability Database, del NIST): la base de datos pública más usada, que además enriquece cada CVE con el score CVSS, el CWE asociado y referencias.
- **cve.org**: el sitio oficial del programa CVE (MITRE), donde se puede buscar directo por ID.
- **CWE catálogo de MITRE** (cwe.mitre.org): para consultar la taxonomía de debilidades en sí.

## Herramientas automatizadas de la industria que detectan CVEs

- **Nessus** (Tenable): scanner de vulnerabilidades que, al auditar una red o un host, identifica versiones de software desactualizadas y las cruza contra su base de CVEs conocidos.
- **Nmap** con el script engine NSE (en particular el script `vulners` o `vuln`), que a partir del fingerprinting de versión de servicios puede listar los CVEs asociados a esa versión detectada.

Otras que también se usan mucho en la industria para esto son OpenVAS/Greenbone y Qualys, pero con Nessus y Nmap+NSE ya queda cubierto el punto de "herramienta automatizada que detecta CVEs asignados" que pide la consigna.
