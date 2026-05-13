
#!/usr/bin/env python3
"""Filtro que convierte texto a mayúsculas."""

import sys

# Leer línea por línea desde stdin
for linea in sys.stdin:

    # Convertir a mayúsculas
    linea_mayuscula = linea.upper()

    # Escribir en stdout
    sys.stdout.write(linea_mayuscula)