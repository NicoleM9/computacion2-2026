
#!/usr/bin/env python3
"""Comunicación básica por pipe."""

import os

# Crear pipe
read_fd, write_fd = os.pipe()

# Crear proceso hijo
pid = os.fork()

# =========================
# HIJO
# =========================
if pid == 0:

    # El hijo NO necesita leer
    os.close(read_fd)

    mensajes = [
        "Mensaje 1 del hijo",
        "Mensaje 2 del hijo",
        "Mensaje 3 del hijo",
        "FIN"
    ]

    for msg in mensajes:

        # Escribir mensaje en el pipe
        os.write(write_fd, (msg + "\n").encode())

        print(f"[HIJO] Envié: {msg}")

    # Cerrar escritura
    os.close(write_fd)

    # Terminar hijo
    os._exit(0)

# =========================
# PADRE
# =========================
else:

    # El padre NO necesita escribir
    os.close(write_fd)

    print("[PADRE] Esperando mensajes...\n")

    buffer = b""

    while True:

        datos = os.read(read_fd, 1024)

        # EOF
        if not datos:
            break

        buffer += datos

    # Convertir bytes a texto
    mensajes = buffer.decode().strip().split("\n")

    for msg in mensajes:
        print(f"[PADRE] Recibí: {msg}")

    # Cerrar lectura
    os.close(read_fd)

    # Esperar hijo
    os.wait()

    print("\n[PADRE] Hijo terminado")