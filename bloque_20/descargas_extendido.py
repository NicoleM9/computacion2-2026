#!/usr/bin/env python3
"""Ejercicio 3 obligatorio: Concurrencia de clientes con HTTP real, acotación y fallos.

Extensión de descargas.py para la Clase 20.
"""
import asyncio
import time
import httpx
import requests

# Lista de URLs para pruebas reales
URLS = [
    'https://httpbin.org/delay/1',
    'https://example.com',
    'https://python.org',
    'https://fastapi.tiangolo.com',
    'https://httpbin.org/status/200',
    'https://httpbin.org/bytes/1024',
    'https://httpbin.org/uuid',
    'https://httpbin.org/user-agent',
    'https://httpbin.org/ip',
    'https://httpbin.org/headers',
]


# ==========================================
# Parte B: Descargas HTTP Reales con HTTPX
# ==========================================

async def bajar_httpx(cliente, url):
    """Descarga asíncrona real. Reutiliza la sesión para Keep-Alive."""
    resp = await cliente.get(url)
    return url, resp.status_code, len(resp.content)


async def bajar_requests(url):
    """Descarga sincrónica bloqueante usando requests (ANTI-PATRÓN en asyncio)."""
    resp = requests.get(url, timeout=10)
    return url, resp.status_code, len(resp.content)


async def medir_httpx_secuencial(urls):
    async with httpx.AsyncClient(timeout=10) as cliente:
        return [await bajar_httpx(cliente, u) for u in urls]


async def medir_httpx_concurrente(urls):
    async with httpx.AsyncClient(timeout=10) as cliente:
        return await asyncio.gather(*(bajar_httpx(cliente, u) for u in urls))


async def medir_requests_concurrente(urls):
    """Lanzar corrutinas que usan requests síncrono demuestra cómo se rompe el loop."""
    return await asyncio.gather(*(bajar_requests(u) for u in urls))


# ==========================================
# Parte C: Acotar Concurrencia con Semaphore
# ==========================================

async def medir_httpx_acotado(urls, limite):
    sem = asyncio.Semaphore(limite)

    async def acotada(cliente, url):
        async with sem:
            return await bajar_httpx(cliente, url)

    async with httpx.AsyncClient(timeout=10) as cliente:
        return await asyncio.gather(*(acotada(cliente, u) for u in urls))


# ==========================================
# Parte D: Manejo de Fallos (return_exceptions)
# ==========================================

async def medir_con_errores(urls_con_error, usar_return_exceptions=False):
    async with httpx.AsyncClient(timeout=5) as cliente:
        if usar_return_exceptions:
            # Captura excepciones como ítems de la lista devuelta sin cancelar las demás tareas
            return await asyncio.gather(
                *(bajar_httpx(cliente, u) for u in urls_con_error),
                return_exceptions=True
            )
        else:
            # Aborta inmediatamente al encontrar la primera excepción
            return await asyncio.gather(*(bajar_httpx(cliente, u) for u in urls_con_error))


# ==========================================
# MAIN: Ejecución y mediciones paso a paso
# ==========================================

async def main():
    print("=== Parte B: Descargas con HTTP Real ===")
    
    t0 = time.perf_counter()
    res_sec = await medir_httpx_secuencial(URLS)
    t_sec = time.perf_counter() - t0
    print(f"  HTTPX Secuencial         : {t_sec:5.2f}s  ({len(res_sec)} descargas)")

    t0 = time.perf_counter()
    res_conc = await medir_httpx_concurrente(URLS)
    t_conc = time.perf_counter() - t0
    print(f"  HTTPX Concurrent (gather): {t_conc:5.2f}s  ({len(res_conc)} descargas)")

    t0 = time.perf_counter()
    res_req = await medir_requests_concurrente(URLS)
    t_req = time.perf_counter() - t0
    print(f"  Requests 'Async' (Bloqueante): {t_req:5.2f}s  ({len(res_req)} descargas)")


    print("\n=== Parte C: Acotar Concurrencia ===")
    
    LIMITE = 3
    t0 = time.perf_counter()
    res_sem = await medir_httpx_acotado(URLS, LIMITE)
    t_sem = time.perf_counter() - t0
    print(f"  HTTPX Con Semáforo ({LIMITE}) : {t_sem:5.2f}s")


    print("\n=== Parte D: Manejo de Fallos ===")
    urls_mixtas = URLS[:3] + ['https://dominio-invalido-que-no-existe-12345.com'] + URLS[3:5]

    print(" 1. Probando gather normal con URL inválida:")
    try:
        await medir_con_errores(urls_mixtas, usar_return_exceptions=False)
    except Exception as e:
        print(f"    -> Falló de inmediato con excepción: {type(e).__name__}")

    print(" 2. Probando gather con return_exceptions=True:")
    resultados_fallos = await medir_con_errores(urls_mixtas, usar_return_exceptions=True)
    
    exitosas = 0
    fallidas = 0
    for res in resultados_fallos:
        if isinstance(res, Exception):
            fallidas += 1
            print(f"    -> Resultado fallido capturado: {type(res).__name__}")
        else:
            exitosas += 1
    print(f"    -> Resumen: {exitosas} exitosas, {fallidas} fallidas.")


if __name__ == '__main__':
    asyncio.run(main())