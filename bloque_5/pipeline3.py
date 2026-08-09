#!/usr/bin/env python3

import os


# Pipe 1: cat -> cut
read1, write1 = os.pipe()

# Pipe 2: cut -> sort
read2, write2 = os.pipe()


# =================================
# PRIMER HIJO: cat /etc/passwd
# =================================

pid1 = os.fork()

if pid1 == 0:
    os.close(read1)
    os.close(read2)
    os.close(write2)

    # stdout de cat -> pipe 1
    os.dup2(write1, 1)
    os.close(write1)

    os.execvp("cat", ["cat", "/etc/passwd"])


# =================================
# SEGUNDO HIJO: cut -d: -f1
# =================================

pid2 = os.fork()

if pid2 == 0:
    os.close(write1)
    os.close(read2)

    # stdin de cut <- pipe 1
    os.dup2(read1, 0)
    os.close(read1)

    # stdout de cut -> pipe 2
    os.dup2(write2, 1)
    os.close(write2)

    os.execvp("cut", ["cut", "-d:", "-f1"])


# =================================
# TERCER HIJO: sort
# =================================

pid3 = os.fork()

if pid3 == 0:
    os.close(read1)
    os.close(write1)
    os.close(write2)

    # stdin de sort <- pipe 2
    os.dup2(read2, 0)
    os.close(read2)

    os.execvp("sort", ["sort"])


# =================================
# PADRE
# =================================

os.close(read1)
os.close(write1)
os.close(read2)
os.close(write2)

# Esperar a los tres hijos
os.waitpid(pid1, 0)
os.waitpid(pid2, 0)
os.waitpid(pid3, 0)
