"""Configuración por variables de entorno (todo con valores por defecto)."""
import os

NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
TAMANO_COLA = int(os.getenv("TAMANO_COLA", "1000"))
TIMEOUT_DEFECTO = float(os.getenv("TIMEOUT_DEFECTO", "60"))
LIMITE_APAGADO = float(os.getenv("LIMITE_APAGADO", "10"))
DIR_VOLCADOS = os.getenv("DIR_VOLCADOS", ".")
MAX_PROCESOS = int(os.getenv("MAX_PROCESOS", str(os.cpu_count() or 2)))

# Para la medición 2: ejecuta el hash DENTRO del event loop (a propósito mal).
MODO_BLOQUEANTE = os.getenv("MODO_BLOQUEANTE", "0") == "1"

# Iteraciones de SHA-256 entre cada chequeo de cancelación en el proceso hijo.
HASH_LOTE = int(os.getenv("HASH_LOTE", "200000"))
