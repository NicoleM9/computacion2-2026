#!/usr/bin/env python3
"""Mapear un archivo usando mmap en modo solo lectura."""

import mmap

ARCHIVO = "/tmp/mmap_test.txt"

with open(ARCHIVO, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    print("=== Archivo en modo solo lectura ===")

    print(f"Contenido: {mm[:40]}")
    print(f"Tamaño: {mm.size()} bytes")

    # Intentar modificar el archivo
    try:
        mm[0:4] = b"TEST"
    except TypeError as e:
        print(f"Error al escribir: {e}")

    mm.close()
