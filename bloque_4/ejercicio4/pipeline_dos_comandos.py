
#!/usr/bin/env python3
"""Pipeline de dos comandos."""

import os

def pipeline_dos_comandos(cmd1, args1, cmd2, args2):
    """Ejecuta: cmd1 | cmd2"""

    # =========================
    # Crear pipe
    # =========================
    read_fd, write_fd = os.pipe()

    # =========================
    # PRIMER PROCESO
    # =========================
    pid1 = os.fork()

    if pid1 == 0:

        # No necesita leer
        os.close(read_fd)

        # stdout -> pipe
        os.dup2(write_fd, 1)

        # Ya no necesitamos write_fd
        os.close(write_fd)

        # Ejecutar comando
        os.execvp(cmd1, [cmd1] + args1)

        os._exit(1)

    # =========================
    # SEGUNDO PROCESO
    # =========================
    pid2 = os.fork()

    if pid2 == 0:

        # No necesita escribir
        os.close(write_fd)

        # stdin <- pipe
        os.dup2(read_fd, 0)

        # Ya no necesitamos read_fd
        os.close(read_fd)

        # Ejecutar comando
        os.execvp(cmd2, [cmd2] + args2)

        os._exit(1)

    # =========================
    # PADRE
    # =========================

    os.close(read_fd)
    os.close(write_fd)

    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)

if __name__ == "__main__":

    print("=== ls -la | grep .py ===\n")

    pipeline_dos_comandos(
        "ls",
        ["-la"],
        "grep",
        [".py"]
    )