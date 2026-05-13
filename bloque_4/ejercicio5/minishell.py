
#!/usr/bin/env python3
"""Mini-shell con redirección."""

import os
import sys

# =====================================================
# PARSEAR COMANDO
# =====================================================

def parsear_linea(linea):
    """
    Convierte una línea en:
    comando, argumentos, salida, entrada
    """

    partes = linea.split()

    # Línea vacía
    if not partes:
        return None, [], None, None

    comando = partes[0]

    args = []

    archivo_salida = None
    archivo_entrada = None

    i = 1

    while i < len(partes):

        # =========================================
        # REDIRECCIÓN DE SALIDA >
        # =========================================
        if partes[i] == ">":

            # Validar archivo
            if i + 1 >= len(partes):
                print("Error: falta archivo de salida")
                return None, [], None, None

            archivo_salida = partes[i + 1]

            i += 2

        # =========================================
        # REDIRECCIÓN DE ENTRADA <
        # =========================================
        elif partes[i] == "<":

            # Validar archivo
            if i + 1 >= len(partes):
                print("Error: falta archivo de entrada")
                return None, [], None, None

            archivo_entrada = partes[i + 1]

            i += 2

        # =========================================
        # ARGUMENTO NORMAL
        # =========================================
        else:
            args.append(partes[i])
            i += 1

    return comando, args, archivo_salida, archivo_entrada

# =====================================================
# EJECUTAR COMANDO
# =====================================================

def ejecutar(comando,
              args,
              archivo_salida=None,
              archivo_entrada=None):

    pid = os.fork()

    # =================================================
    # HIJO
    # =================================================
    if pid == 0:

        # =============================================
        # REDIRECCIÓN DE SALIDA
        # =============================================
        if archivo_salida:

            fd_salida = os.open(
                archivo_salida,
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC,
                0o644
            )

            # stdout -> archivo
            os.dup2(fd_salida, 1)

            os.close(fd_salida)

        # =============================================
        # REDIRECCIÓN DE ENTRADA
        # =============================================
        if archivo_entrada:

            fd_entrada = os.open(
                archivo_entrada,
                os.O_RDONLY
            )

            # stdin <- archivo
            os.dup2(fd_entrada, 0)

            os.close(fd_entrada)

        # =============================================
        # EJECUTAR COMANDO
        # =============================================
        try:

            os.execvp(comando, [comando] + args)

        except OSError as e:

            print(f"Error ejecutando comando: {e}",
                  file=sys.stderr)

            os._exit(127)

    # =================================================
    # PADRE
    # =================================================
    else:

        _, status = os.wait()

        return os.WEXITSTATUS(status)

# =====================================================
# MAIN
# =====================================================

def main():

    while True:

        try:
            linea = input("minish$ ")

        except EOFError:
            print("\nChau!")
            break

        linea = linea.strip()

        # Ignorar línea vacía
        if not linea:
            continue

        # Salir
        if linea == "exit":
            print("Chau!")
            break

        comando, args, salida, entrada = parsear_linea(linea)

        if comando:
            ejecutar(comando, args, salida, entrada)

# =====================================================

if __name__ == "__main__":
    main()