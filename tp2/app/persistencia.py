"""Volcado del estado a JSON y reporte de volcados previos."""
import json
import logging
import time
from pathlib import Path

log = logging.getLogger("persistencia")


def volcar(tareas: list[dict], directorio: str) -> Path:
    Path(directorio).mkdir(parents=True, exist_ok=True)
    ruta = Path(directorio) / f"estado_{time.strftime('%Y%m%d_%H%M%S')}.json"
    ruta.write_text(json.dumps({"tareas": tareas}, indent=2, ensure_ascii=False))
    log.info("Estado volcado en %s (%d tareas)", ruta, len(tareas))
    return ruta


def reportar_previo(directorio: str) -> None:
    previos = sorted(Path(directorio).glob("estado_*.json"))
    if not previos:
        log.info("No hay volcados previos en %s", directorio)
        return
    ultimo = previos[-1]
    try:
        n = len(json.loads(ultimo.read_text()).get("tareas", []))
        log.info("Volcado previo encontrado: %s (%d tareas)", ultimo, n)
    except (OSError, ValueError):
        log.warning("Volcado previo ilegible: %s", ultimo)
