#!/usr/bin/env python3

FIFO = "/tmp/mi_canal"


print(f"Leyendo de {FIFO}...")


with open(FIFO, "r") as f:

    for linea in f:

        print(f"Recibido: {linea.strip()}")


print("Lectura completada (el escritor cerró el pipe)")
