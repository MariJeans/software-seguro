"""
Prueba cada candidato de candidatos_zip.txt contra secreto.zip (cifrado AES)
hasta encontrar la contraseña correcta.

Requiere: pip install pyzipper

Uso:
    python crackear_zip_aes.py secreto.zip candidatos_zip.txt
"""
import sys
import pyzipper

def main():
    if len(sys.argv) != 3:
        print("Uso: python crackear_zip_aes.py <secreto.zip> <candidatos_zip.txt>")
        sys.exit(1)

    ruta_zip = sys.argv[1]
    ruta_candidatos = sys.argv[2]

    with open(ruta_candidatos, "r") as f:
        candidatos = [linea.strip() for linea in f if linea.strip()]

    print(f"Probando {len(candidatos)} candidatos contra {ruta_zip}...")

    with pyzipper.AESZipFile(ruta_zip) as zf:
        for i, password in enumerate(candidatos, 1):
            try:
                zf.extractall(pwd=password.encode(), path="extraido")
                print(f"\n¡CONTRASEÑA ENCONTRADA! -> {password}")
                print(f"(intento {i} de {len(candidatos)})")
                return
            except RuntimeError:
                pass
            except Exception:
                pass

            if i % 2000 == 0:
                print(f"  ...probados {i} sin éxito todavía")

    print("No se encontró ninguna contraseña válida en la lista.")

if __name__ == "__main__":
    main()
