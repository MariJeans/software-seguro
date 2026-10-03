import hashlib

ALGORITMO = "md5"  # cambiar a "sha1" o "sha256" si se necesita otro hash


def generar_hash(numero: int) -> str:
    h = hashlib.new(ALGORITMO)
    h.update(str(numero).encode())
    return h.hexdigest()


def main():
    desde = int(input("Ingrese el numero desde: "))
    hasta = int(input("Ingrese el numero hasta: "))

    if desde > hasta:
        desde, hasta = hasta, desde

    salida = "hashes.txt"
    with open(salida, "w") as archivo:
        for numero in range(desde, hasta + 1):
            linea = f"{generar_hash(numero)}"
            print(linea)
            archivo.write(linea + "\n")

    print(f"\nListado guardado en {salida}")


if __name__ == "__main__":
    main()
