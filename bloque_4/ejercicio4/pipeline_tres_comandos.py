
#!/usr/bin/env python3
"""Pipeline de tres comandos."""

import os

def pipeline_tres_comandos(cmd1, args1,
                            cmd2, args2,
                            cmd3, args3):

    # =========================
    # Crear pipes
    # =========================
    pipe1_read, pipe1_write = os.pipe()
    pipe2_read, pipe2_write = os.pipe()

    # =========================
    # CMD1
    # =========================
    pid1 = os.fork()

    if pid1 == 0:

        os.close(pipe1_read)

        os.close(pipe2_read)
        os.close(pipe2_write)

        # stdout -> pipe1
        os.dup2(pipe1_write, 1)

        os.close(pipe1_write)

        os.execvp(cmd1, [cmd1] + args1)

        os._exit(1)

    # =========================
    # CMD2
    # =========================
    pid2 = os.fork()

    if pid2 == 0:

        os.close(pipe1_write)
        os.close(pipe2_read)

        # stdin <- pipe1
        os.dup2(pipe1_read, 0)

        # stdout -> pipe2
        os.dup2(pipe2_write, 1)

        os.close(pipe1_read)
        os.close(pipe2_write)

        os.execvp(cmd2, [cmd2] + args2)

        os._exit(1)

    # =========================
    # CMD3
    # =========================
    pid3 = os.fork()

    if pid3 == 0:

        os.close(pipe1_read)
        os.close(pipe1_write)

        os.close(pipe2_write)

        # stdin <- pipe2
        os.dup2(pipe2_read, 0)

        os.close(pipe2_read)

        os.execvp(cmd3, [cmd3] + args3)

        os._exit(1)

    # =========================
    # PADRE
    # =========================

    os.close(pipe1_read)
    os.close(pipe1_write)

    os.close(pipe2_read)
    os.close(pipe2_write)

    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)
    os.waitpid(pid3, 0)

if __name__ == "__main__":

    print("=== cat /etc/passwd | grep root | wc -l ===\n")

    pipeline_tres_comandos(
        "cat", ["/etc/passwd"],
        "grep", ["root"],
        "wc", ["-l"]
    )