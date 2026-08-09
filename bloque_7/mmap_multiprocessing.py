#!/usr/bin/env python3

import mmap
import struct
import os
from multiprocessing import Process

ARCHIVO = "/tmp/mmap_mp.bin"
TAMAÑO = 256
TAMAÑO_REGION = 64


def escribir_en_mmap(archivo, offset, mensaje):

    with open(archivo, "r+b") as f:

        mm = mmap.mmap(
            f.fileno(),
            TAMAÑO
        )

        datos = mensaje.encode()

        struct.pack_into(
            "i",
            mm,
            offset,
            len(datos)
        )

        mm[
            offset + 4:
            offset + 4 + len(datos)
        ] = datos

        mm.flush()
        mm.close()


# Crear archivo
with open(ARCHIVO, "wb") as f:
    f.write(b"\x00" * TAMAÑO)


mensajes = [
    "Hola desde proceso 0",
    "Saludos del proceso 1",
    "Proceso 2 presente",
    "Proceso 3 reportando"
]

procesos = []

for i, mensaje in enumerate(mensajes):

    p = Process(
        target=escribir_en_mmap,
        args=(
            ARCHIVO,
            i * TAMAÑO_REGION,
            mensaje
        )
    )

    p.start()
    procesos.append(p)


for p in procesos:
    p.join()


print("=== Mensajes de los procesos ===")

with open(ARCHIVO, "r+b") as f:

    mm = mmap.mmap(
        f.fileno(),
        TAMAÑO
    )

    for i in range(4):

        offset = i * TAMAÑO_REGION

        largo = struct.unpack_from(
            "i",
            mm,
            offset
        )[0]

        mensaje = bytes(
            mm[
                offset + 4:
                offset + 4 + largo
            ]
        ).decode()

        print(f"Proceso {i}: {mensaje}")

    mm.close()


os.unlink(ARCHIVO)
