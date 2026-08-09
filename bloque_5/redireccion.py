#!/usr/bin/env python3

import os
import sys


print("Este mensaje va a la terminal")

# Guardar stdout original
stdout_original = os.dup(1)

# Abrir archivo destino
archivo = os.open(
    "/tmp/salida.txt",
    os.O_CREAT | os.O_WRONLY | os.O_TRUNC,
    0o644
)

# Redirigir stdout al archivo
os.dup2(archivo, 1)

# Ya no necesitamos este descriptor
os.close(archivo)

# Estos mensajes van al archivo
print("Este mensaje va al archivo")
print("Y este también")

sys.stdout.flush()

# Restaurar stdout original
os.dup2(stdout_original, 1)
os.close(stdout_original)

print("Volvimos a la terminal")
print("Revisá el contenido de /tmp/salida.txt")
