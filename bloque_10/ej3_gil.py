import threading
import multiprocessing
import time
import math


def cpu_task(n):
    return sum(math.sqrt(i) for i in range(n))


N = 5_000_000


# =========================
# SECUENCIAL
# =========================

inicio = time.perf_counter()

for _ in range(4):
    cpu_task(N)

tiempo_secuencial = time.perf_counter() - inicio

print(f"Secuencial: {tiempo_secuencial:.2f}s")


# =========================
# 4 THREADS
# =========================

inicio = time.perf_counter()

hilos = [
    threading.Thread(target=cpu_task, args=(N,))
    for _ in range(4)
]

for h in hilos:
    h.start()

for h in hilos:
    h.join()

tiempo_threads = time.perf_counter() - inicio

print(f"4 threads:  {tiempo_threads:.2f}s")


# =========================
# 4 PROCESOS
# =========================

inicio = time.perf_counter()

procesos = [
    multiprocessing.Process(target=cpu_task, args=(N,))
    for _ in range(4)
]

for p in procesos:
    p.start()

for p in procesos:
    p.join()

tiempo_procesos = time.perf_counter() - inicio

print(f"4 procesos: {tiempo_procesos:.2f}s")
