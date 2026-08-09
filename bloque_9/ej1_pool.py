#!/usr/bin/env python3

from multiprocessing import Pool
import time
import random


def cuadrado(x):
    duracion = random.uniform(0.1, 1.0)
    time.sleep(duracion)
    return x ** 2


def suma(a, b):
    return a + b


if __name__ == "__main__":

    with Pool(4) as pool:

        print("== map ==")
        print(pool.map(cuadrado, range(8)))

        print("\n== map_async ==")
        resultado_async = pool.map_async(cuadrado, range(8))

        print(f"¿Listo inmediatamente? {resultado_async.ready()}")
        print(f"Resultados: {resultado_async.get()}")

        print("\n== imap ==")
        for resultado in pool.imap(cuadrado, range(8)):
            print(f"  llegó: {resultado}")

        print("\n== imap_unordered ==")
        for resultado in pool.imap_unordered(cuadrado, range(8)):
            print(f"  llegó: {resultado}")

        print("\n== starmap ==")
        print(pool.starmap(suma, [
            (1, 2),
            (3, 4),
            (5, 6)
        ]))

        print("\n== apply_async ==")
        resultado = pool.apply_async(cuadrado, (10,))

        print(f"¿Listo? {resultado.ready()}")
        print(f"Resultado: {resultado.get()}")
