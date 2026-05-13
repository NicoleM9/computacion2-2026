
#!/usr/bin/env python3
"""Pipeline usando subprocess."""

import subprocess

texto = """
primera linea
segunda linea con error
tercera linea
otra linea con error
ultima linea
"""

# ==========================================
# PROCESO 1
# ==========================================

echo = subprocess.Popen(
    ["echo", texto],
    stdout=subprocess.PIPE
)

# ==========================================
# PROCESO 2
# ==========================================

grep = subprocess.Popen(
    ["grep", "error"],
    stdin=echo.stdout,
    stdout=subprocess.PIPE
)

# ==========================================
# PROCESO 3
# ==========================================

wc = subprocess.Popen(
    ["wc", "-l"],
    stdin=grep.stdout,
    stdout=subprocess.PIPE,
    text=True
)

# ==========================================
# IMPORTANTE
# ==========================================

echo.stdout.close()
grep.stdout.close()

# ==========================================
# OBTENER RESULTADO
# ==========================================

resultado, _ = wc.communicate()

print(f"Líneas con 'error': {resultado.strip()}")