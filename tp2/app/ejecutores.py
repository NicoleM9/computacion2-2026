"""Lógica de cada tipo de tarea. Nada de time.sleep() acá."""
from __future__ import annotations

import asyncio
import hashlib
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.managers import SyncManager

import httpx

from . import config


# ---------------------------------------------------------------- validación
def validar(tipo: str, p: dict) -> None:
    """Lanza ValueError si los parámetros no sirven (la API responde 422)."""
    if tipo == "descargar":
        urls = p.get("urls")
        if (not isinstance(urls, list) or not urls
                or not all(isinstance(u, str) and u.startswith(("http://", "https://"))
                           for u in urls)):
            raise ValueError("'urls' debe ser una lista no vacía de URLs http(s)")
    elif tipo == "hashear":
        it = p.get("iteraciones")
        if not isinstance(p.get("texto"), str):
            raise ValueError("'texto' debe ser un string")
        if not isinstance(it, int) or isinstance(it, bool) or it < 1:
            raise ValueError("'iteraciones' debe ser un entero >= 1")
    elif tipo == "esperar":
        s = p.get("segundos")
        if not isinstance(s, (int, float)) or isinstance(s, bool) or s < 0:
            raise ValueError("'segundos' debe ser un número >= 0")
    else:
        raise ValueError(f"tipo desconocido: {tipo}")


# ------------------------------------------------------------------ descargar
async def _una(cliente: httpx.AsyncClient, url: str) -> dict:
    t0 = time.perf_counter()
    try:
        r = await cliente.get(url)
        return {"url": url, "status": r.status_code, "bytes": len(r.content),
                "segundos": round(time.perf_counter() - t0, 4)}
    except httpx.HTTPError as e:  # CancelledError NO es HTTPError: se propaga
        return {"url": url, "error": f"{type(e).__name__}: {e}",
                "segundos": round(time.perf_counter() - t0, 4)}


async def descargar(p: dict) -> dict:
    t0 = time.perf_counter()
    # 'async with' garantiza cerrar las conexiones aunque nos cancelen a mitad.
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cliente:
        resultados = await asyncio.gather(*(_una(cliente, u) for u in p["urls"]))
    return {"resultados": resultados,
            "total_segundos": round(time.perf_counter() - t0, 4)}


# --------------------------------------------------------------------- esperar
async def esperar(p: dict) -> dict:
    await asyncio.sleep(p["segundos"])
    return {"durmio": p["segundos"]}


# --------------------------------------------------------------------- hashear
class _SinCancelacion:
    """Evento falso para el modo bloqueante (nunca se cancela)."""
    def is_set(self) -> bool:
        return False


def hash_por_lotes(texto: str, iteraciones: int, cancelar) -> str:
    """Corre en un PROCESO hijo. Revisa 'cancelar' entre lotes: un Future de
    ProcessPoolExecutor ya iniciado no se puede cancelar desde afuera."""
    h = texto.encode()
    hecho = 0
    while hecho < iteraciones:
        if cancelar.is_set():
            raise InterruptedError("hash cancelado")
        n = min(config.HASH_LOTE, iteraciones - hecho)
        for _ in range(n):
            h = hashlib.sha256(h).digest()
        hecho += n
    return h.hex()


async def hashear(p: dict, proc_pool: ProcessPoolExecutor,
                  manager: SyncManager) -> dict:
    texto, it = p["texto"], p["iteraciones"]
    if config.MODO_BLOQUEANTE:
        # A PROPÓSITO MAL: bloquea el event loop. Solo para la medición 2.
        return {"hash": hash_por_lotes(texto, it, _SinCancelacion()),
                "iteraciones": it}

    loop = asyncio.get_running_loop()
    # manager.Event() hace IPC bloqueante: lo mandamos a un thread.
    cancelar = await asyncio.to_thread(manager.Event)
    try:
        h = await loop.run_in_executor(proc_pool, hash_por_lotes, texto, it, cancelar)
    finally:
        # Si nos cancelaron/timeout, el hijo lo ve en el próximo lote y corta.
        # (set() es IPC de microsegundos; se acepta bloquear ese instante.)
        cancelar.set()
    return {"hash": h, "iteraciones": it}
