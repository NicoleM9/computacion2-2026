#!/usr/bin/env python3

from multiprocessing import Pool
import time
import math


def cpu_task(n):
    return sum(math.sqrt(i) for i in range(n))


N = 500_000
TAREAS = 8


if __name__ == "__main__":

    print("=== Procesamiento secuencial ===")

    inicio = time.time()

    resultados = [
        cpu_task(N)
        for _ in range(TAREAS)
    ]

    tiempo_secuencial = time.time() - inicio

    print(f"Tiempo secuencial: {tiempo_secuencial:.2f} segundos")

    print("\n=== Procesamiento paralelo ===")

    for workers in [1, 2, 4, 8]:

        inicio = time.time()

        with Pool(workers) as pool:
            resultados = pool.map(
                cpu_task,
                [N] * TAREAS
            )

        tiempo_paralelo = time.time() - inicio

        speedup = tiempo_secuencial / tiempo_paralelo

        print(
            f"Pool({workers}): "
            f"{tiempo_paralelo:.2f}s "
            f"(speedup: {speedup:.2f}x)"
        )
