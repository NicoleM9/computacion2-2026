#!/usr/bin/env python3

import os
import sys


def parsear_linea(linea):
    """
    Parsea una línea de comando.

    Retorna:
        comando, argumentos, archivo_salida, archivo_entrada
    """

    partes = linea.split()

    if not partes:
        return None, [], None, None

    comando = partes[0]
    args = []
    archivo_salida = None
    archivo_entrada = None

    i = 1

    while i < len(partes):

        if partes[i] == ">":
            if i + 1 < len(partes):
                archivo_salida = partes[i + 1]
                i += 2
            else:
                print("Error: falta el archivo de salida", file=sys.stderr)
                return None, [], None, None

        elif partes[i] == "<":
            if i + 1 < len(partes):
                archivo_entrada = partes[i + 1]
                i += 2
            else:
                print("Error: falta el archivo de entrada", file=sys.stderr)
                return None, [], None, None

        else:
            args.append(partes[i])
            i += 1

    return comando, args, archivo_salida, archivo_entrada


def ejecutar(comando, args, archivo_salida=None, archivo_entrada=None):

    pid = os.fork()

    if pid == 0:

        # stdout -> archivo
        if archivo_salida:
            fd = os.open(
                archivo_salida,
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC,
                0o644
            )

            os.dup2(fd, 1)
            os.close(fd)

        # stdin <- archivo
        if archivo_entrada:
            fd = os.open(
                archivo_entrada,
                os.O_RDONLY
            )

            os.dup2(fd, 0)
            os.close(fd)

        try:
            os.execvp(comando, [comando] + args)

        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            os._exit(127)

    else:
        _, status = os.waitpid(pid, 0)

        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)

        return 1


def main():

    while True:

        try:
            linea = input("minish$ ")

        except EOFError:
            print("\nChau!")
            break

        linea = linea.strip()

        if not linea:
            continue

        if linea == "exit":
            print("Chau!")
            break

        comando, args, salida, entrada = parsear_linea(linea)

        if comando:
            ejecutar(comando, args, salida, entrada)


if __name__ == "__main__":
    main()
