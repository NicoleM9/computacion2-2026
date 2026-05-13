
#!/usr/bin/env python3
"""Redirección manual de stdout."""

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

# Redirigir stdout
os.dup2(archivo, 1)

# Ya no necesitamos el fd original del archivo
os.close(archivo)

# Ahora stdout apunta al archivo
print("Este mensaje va al archivo")
print("Y este también")

# Forzar escritura
sys.stdout.flush()

# Restaurar stdout original
os.dup2(stdout_original, 1)

# Cerrar copia guardada
os.close(stdout_original)

print("Volvimos a la terminal")
print("Revisá /tmp/salida.txt")