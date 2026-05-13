
#!/usr/bin/env python3
"""Lee mensajes desde un named pipe."""

FIFO = "/tmp/mi_canal"

print(f"Leyendo desde {FIFO}...\n")

with open(FIFO, "r") as f:

    for linea in f:

        print(f"Recibido: {linea.strip()}")

print("\nLectura completada")