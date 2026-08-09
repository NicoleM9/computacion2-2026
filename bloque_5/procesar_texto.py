#!/usr/bin/env python3

import subprocess


texto = """
primera linea
segunda linea con error
tercera linea
otra linea con error
ultima linea
"""


# echo texto
echo = subprocess.Popen(
    ["echo", texto],
    stdout=subprocess.PIPE
)


# echo -> grep error
grep = subprocess.Popen(
    ["grep", "error"],
    stdin=echo.stdout,
    stdout=subprocess.PIPE
)


# grep -> wc -l
wc = subprocess.Popen(
    ["wc", "-l"],
    stdin=grep.stdout,
    stdout=subprocess.PIPE,
    text=True
)


# Cerrar los pipes del padre
echo.stdout.close()
grep.stdout.close()


# Esperar resultado
resultado, _ = wc.communicate()


print(f"Líneas con 'error': {resultado.strip()}")
