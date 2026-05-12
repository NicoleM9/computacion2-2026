
#!/usr/bin/env python3
"""
Ejecutor de comandos en paralelo.
Uso: python3 paralelo.py "cmd1" "cmd2" ...
"""

import os
import sys
import time


def main():

    # Verificar argumentos
    if len(sys.argv) < 2:

        print(f"Uso: {sys.argv[0]} comando1 [comando2 ...]")

        sys.exit(1)


    # Lista de comandos
    comandos = sys.argv[1:]


    # Guardar tiempo inicial
    inicio = time.time()


    # Diccionario PID -> comando
    procesos = {}


    # Crear todos los procesos
    for cmd in comandos:

        partes = cmd.split()

        pid = os.fork()


        if pid == 0:

            # HIJO
            try:

                os.execvp(partes[0], partes)

            except OSError as e:

                print(f"Error ejecutando '{cmd}': {e}")

                os._exit(127)


        else:

            # PADRE
            procesos[pid] = cmd

            print(f"[{pid}] Iniciado: {cmd}")


    # Contadores
    exitosos = 0
    fallidos = 0


    # Esperar hijos
    while procesos:

        pid, status = os.wait()

        codigo = os.WEXITSTATUS(status)

        cmd = procesos[pid]

        print(f"[{pid}] Terminado: {cmd} (código: {codigo})")


        if codigo == 0:

            exitosos += 1

        else:

            fallidos += 1


        del procesos[pid]


    # Tiempo final
    duracion = time.time() - inicio


    # Resumen
    print("\nResumen:")

    print(f"- Comandos ejecutados: {len(comandos)}")

    print(f"- Exitosos: {exitosos}")

    print(f"- Fallidos: {fallidos}")

    print(f"- Tiempo total: {duracion:.2f}s")


if __name__ == "__main__":

    main()