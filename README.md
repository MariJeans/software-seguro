# Software Seguro — Ciberseguridad

Repositorio de documentación técnica del curso de **Ciberseguridad / Software Seguro**. Reúne mi trabajo práctico resolviendo objetivos y laboratorios: reconocimiento de red, análisis de tráfico, interceptación con proxy, manipulación de peticiones HTTP y ataques de fuerza bruta, cada uno documentado paso a paso con su resolución y evidencia (capturas y scripts).

## Temas y habilidades demostradas

- **Mapeo lógico de aplicaciones** y diagramación de arquitecturas (Mermaid).
- **Reconocimiento de red:** puertos y servicios, escaneo con **Nmap**, enumeración de subdominios.
- **TLS:** análisis del handshake y del cifrado en tránsito.
- **Proxy de interceptación:** instalación y configuración (**Burp Suite**).
- **Manipulación manual de peticiones** con Repeater.
- **Automatización y fuerza bruta** con Intruder, ataques por diccionario y generación de hashes (Python).

## Estructura

El curso se organiza en módulos; cada módulo agrupa sus clases (`1/`, `2/`, `3/` …) y cada clase contiene un subdirectorio por objetivo con su `.md` de desarrollo y la evidencia asociada.

```
software-seguro/
└── Modulo_I/
    ├── 1/                                        # Clase 1 — Fundamentos y proxy
    │   ├── Objetivo_1_Mapeo_Logico/              # Diagrama de arquitectura (Mermaid)
    │   ├── Objetivo_2_Laboratorios/              # Labs: Turnero, Ventas, Presupuesto, Gran Rifa
    │   ├── Objetivo_3_Handshake_TLS/             # El handshake TLS
    │   └── Objetivo_4_Instalacion_Proxy/         # Instalación del proxy
    │
    ├── 2/                                        # Clase 2 — Reconocimiento de red
    │   ├── Objetivo_1_Puertos_ServiciosEscenciales/
    │   ├── Objetivo_2_Escaneo_de_Red/            # Escaneo con Nmap
    │   └── Objetivo_3_Subdominios/               # Reconocimiento de subdominios
    │
    └── 3/                                        # Clase 3 — Ataques a aplicaciones web
        ├── Objetivo_2_Manipulacion_Manual_De_Peticiones/   # Repeater
        ├── Objetivo_3_Automatizacion_y_Fuerza_Bruta/       # Fuerza bruta vs. diccionario
        └── Objetivo_4_Labs/                      # Laboratorios prácticos
            ├── Lab_apagar-ia/                    # Informe + script de hashes + capturas
            └── Lab-votacion/                     # Capturas del laboratorio
```

## Cómo navegar el repositorio

Cada objetivo se lee de forma independiente: entrá a la carpeta del objetivo y abrí su archivo `.md`, que incluye el contexto, la resolución y las capturas. Los laboratorios del Objetivo 4 (Clase 3) incluyen además el informe completo y los artefactos usados (scripts en Python, archivos de hashes y evidencia en `capturas/`).

## Convención para nuevos módulos

Al sumar `Modulo_II`, `Modulo_III`, etc., se replica la misma lógica: una carpeta `Modulo_N/`, dentro una carpeta por clase (`1/`, `2/`, …) y, dentro de cada clase, un subdirectorio `Objetivo_X_<nombre_corto>/` por cada objetivo.

---

**Autora:** Maria Acuña · Repositorio de prácticas del curso de Ciberseguridad.
