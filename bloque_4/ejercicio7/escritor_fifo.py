
#!/usr/bin/env python3
"""Escribe mensajes en un named pipe."""

import os
import time

FIFO = "/tmp/mi_canal"

# ==========================================
# CREAR FIFO SI NO EXISTE
# ==========================================

if not os.path.exists(FIFO):

    os.mkfifo(FIFO)

    print(f"FIFO creado: {FIFO}")

# ==========================================
# ESCRIBIR MENSAJES
# ==========================================

print(f"Escribiendo en {FIFO}...")
print("(Ejecutá lector_fifo.py en otra terminal)\n")

with open(FIFO, "w") as f:

    for i in range(10):

        mensaje = f"Mensaje {i}: {time.ctime()}"

        print(f"Enviando: {mensaje}")

        f.write(mensaje + "\n")

        # Forzar escritura inmediata
        f.flush()

        time.sleep(1)

print("\nEscritura completada")