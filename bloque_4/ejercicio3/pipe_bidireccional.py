
#!/usr/bin/env python3
"""Comunicación bidireccional."""

import os

# Pipe padre -> hijo
p2h_read, p2h_write = os.pipe()

# Pipe hijo -> padre
h2p_read, h2p_write = os.pipe()

pid = os.fork()

# =========================
# HIJO
# =========================
if pid == 0:

    # Cerrar extremos no usados
    os.close(p2h_write)
    os.close(h2p_read)

    # Leer pregunta
    pregunta = os.read(p2h_read, 1024).decode().strip()

    print(f"[HIJO] Recibí: {pregunta}")

    # Procesar
    if pregunta.isdigit():
        respuesta = str(int(pregunta) ** 2)
    else:
        respuesta = "No es número"

    # Enviar respuesta
    os.write(h2p_write, respuesta.encode())

    print(f"[HIJO] Envié: {respuesta}")

    # Cerrar
    os.close(p2h_read)
    os.close(h2p_write)

    os._exit(0)

# =========================
# PADRE
# =========================
else:

    os.close(p2h_read)
    os.close(h2p_write)

    numero = "42"

    print(f"[PADRE] Enviando: {numero}")

    # Enviar al hijo
    os.write(p2h_write, numero.encode())

    # IMPORTANTE
    os.close(p2h_write)

    # Leer respuesta
    respuesta = os.read(h2p_read, 1024).decode()

    print(f"[PADRE] Resultado: {numero}² = {respuesta}")

    os.close(h2p_read)

    os.wait()