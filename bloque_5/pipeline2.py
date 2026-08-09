#!/usr/bin/env python3

import os


# Crear el pipe
read_fd, write_fd = os.pipe()


# Crear el primer hijo: ls -l
pid1 = os.fork()

if pid1 == 0:
    # stdout de ls -> pipe
    os.close(read_fd)
    os.dup2(write_fd, 1)
    os.close(write_fd)

    os.execvp("ls", ["ls", "-l"])


# Crear el segundo hijo: grep .py
pid2 = os.fork()

if pid2 == 0:
    # stdin de grep <- pipe
    os.close(write_fd)
    os.dup2(read_fd, 0)
    os.close(read_fd)

    os.execvp("grep", ["grep", ".py"])


# Padre
os.close(read_fd)
os.close(write_fd)

os.waitpid(pid1, 0)
os.waitpid(pid2, 0)
