#!/usr/bin/env python3

import mmap
import os
import struct

NUM_HIJOS = 4
TAMAÑO_POR_HIJO = 16
TAMAÑO_TOTAL = NUM_HIJOS * TAMAÑO_POR_HIJO

mm = mmap.mmap(-1, TAMAÑO_TOTAL)

hijos = []

for i in range(NUM_HIJOS):

    pid = os.fork()

    if pid == 0:

        inicio = i * 25 + 1
        fin = (i + 1) * 25

        suma = sum(range(inicio, fin + 1))

        offset = i * TAMAÑO_POR_HIJO

        struct.pack_into(
            "i",
            mm,
            offset,
            suma
        )

        struct.pack_into(
            "i",
            mm,
            offset + 4,
            os.getpid()
        )

        os._exit(0)

    else:
        hijos.append(pid)

# Esperar a todos
for pid in hijos:
    os.waitpid(pid, 0)

print("=== Resultados parciales ===")

suma_total = 0

for i in range(NUM_HIJOS):

    offset = i * TAMAÑO_POR_HIJO

    suma = struct.unpack_from(
        "i",
        mm,
        offset
    )[0]

    pid = struct.unpack_from(
        "i",
        mm,
        offset + 4
    )[0]

    print(
        f"Hijo {i}: "
        f"PID={pid}, "
        f"suma={suma}"
    )

    suma_total += suma

print(f"\nSuma total: {suma_total}")

esperada = sum(range(1, 101))

print(f"Suma esperada: {esperada}")

if suma_total == esperada:
    print("VERIFICACION: CORRECTA")
else:
    print("VERIFICACION: ERROR")

mm.close()
