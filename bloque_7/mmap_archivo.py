#!/usr/bin/env python3
"""Crear, mapear y modificar un archivo usando mmap."""

import mmap

ARCHIVO = "/tmp/mmap_test.txt"

# Crear archivo con 5 líneas
with open(ARCHIVO, "wb") as f:
    f.write(b"Linea 1: Hola mundo\n")
    f.write(b"Linea 2: Computacion II\n")
    f.write(b"Linea 3: mmap es genial\n")
    f.write(b"Linea 4: Memoria compartida\n")
    f.write(b"Linea 5: Sistemas Operativos\n")

# Mapear el archivo
with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)

    print("=== Contenido completo ===")
    print(mm[:].decode())

    print("=== Linea por linea ===")
    mm.seek(0)

    while True:
        linea = mm.readline()

        if not linea:
            break

        print(f"  {linea.decode().strip()}")

    # Buscar la palabra mmap
    pos = mm.find(b"mmap")

    print(f"\n'mmap' encontrado en posicion: {pos}")

    # Reemplazar mmap por MMAP
    if pos != -1:
        mm.seek(pos)
        mm.write(b"MMAP")

    # Mostrar resultado
    mm.seek(0)

    print("\n=== Despues de modificar ===")
    print(mm[:].decode())

    mm.close()
