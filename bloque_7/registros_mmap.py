#!/usr/bin/env python3

import mmap
import struct
import os

ARCHIVO = "/tmp/registros.bin"

FORMATO = "if20s"
TAMAÑO_REGISTRO = struct.calcsize(FORMATO)
NUM_REGISTROS = 5

print(f"Tamaño de cada registro: {TAMAÑO_REGISTRO} bytes")

# Crear archivo con espacio para 5 registros
with open(ARCHIVO, "wb") as f:
    f.write(b"\x00" * (TAMAÑO_REGISTRO * NUM_REGISTROS))

# Abrir y mapear
with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)

    registros = [
        (1, 8.5, b"Ana"),
        (2, 9.2, b"Juan"),
        (3, 7.8, b"Maria"),
        (4, 6.5, b"Pedro"),
        (5, 10.0, b"Lucia")
    ]

    print("\n=== Escribiendo registros ===")

    for i, (identificador, nota, nombre) in enumerate(registros):

        nombre = nombre.ljust(20, b"\x00")

        offset = i * TAMAÑO_REGISTRO

        struct.pack_into(
            FORMATO,
            mm,
            offset,
            identificador,
            nota,
            nombre
        )

        print(
            f"Registro {i}: "
            f"id={identificador}, "
            f"nota={nota}, "
            f"nombre={nombre.rstrip(b'\\x00').decode()}"
        )

    print("\n=== Leyendo registros ===")

    for i in range(NUM_REGISTROS):

        offset = i * TAMAÑO_REGISTRO

        identificador, nota, nombre = struct.unpack_from(
            FORMATO,
            mm,
            offset
        )

        nombre = nombre.rstrip(b"\x00").decode()

        print(
            f"Registro {i}: "
            f"id={identificador}, "
            f"nota={nota}, "
            f"nombre={nombre}"
        )

    mm.close()

print("\nArchivo creado:", ARCHIVO)
print("Tamaño:", os.path.getsize(ARCHIVO), "bytes")
