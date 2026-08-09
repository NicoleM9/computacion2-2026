import threading
import time


URLS = [
    "http://servidor.com/archivo_0.zip",
    "http://servidor.com/archivo_1.zip",
    "http://servidor.com/archivo_2.zip",
    "http://servidor.com/archivo_3.zip",
    "http://servidor.com/archivo_4.zip"
]

DEMORA = 1


def simular_descarga(url, demora):
    time.sleep(demora)
    print(f"Descargado: {url}")


# =========================
# EJECUCIÓN SECUENCIAL
# =========================

inicio = time.perf_counter()

for url in URLS:
    simular_descarga(url, DEMORA)

tiempo_secuencial = time.perf_counter() - inicio

print(f"\nTiempo secuencial: {tiempo_secuencial:.2f} segundos")


# =========================
# EJECUCIÓN CON THREADS
# =========================

inicio = time.perf_counter()

hilos = [
    threading.Thread(
        target=simular_descarga,
        args=(url, DEMORA)
    )
    for url in URLS
]

for h in hilos:
    h.start()

for h in hilos:
    h.join()

tiempo_paralelo = time.perf_counter() - inicio

print(f"Tiempo con threads: {tiempo_paralelo:.2f} segundos")

mejora = tiempo_secuencial / tiempo_paralelo

print(f"Factor de mejora: {mejora:.2f}x")
