#!/usr/bin/env python3

from multiprocessing import Process, Manager
import time
import random


def worker(shared_dict, shared_list, identificador):

    duracion = random.uniform(0.2, 1.0)

    time.sleep(duracion)

    shared_dict[f"worker_{identificador}"] = {
        "status": "done",
        "result": identificador ** 2,
        "duracion": round(duracion, 2)
    }

    shared_list.append(
        f"Worker {identificador} "
        f"completó en {duracion:.2f}s"
    )


if __name__ == "__main__":

    with Manager() as manager:

        diccionario = manager.dict()
        lista = manager.list()

        procesos = []

        for i in range(5):

            p = Process(
                target=worker,
                args=(diccionario, lista, i)
            )

            p.start()
            procesos.append(p)

        for p in procesos:
            p.join()

        print("=== Diccionario compartido ===")

        for clave, valor in diccionario.items():
            print(f"{clave}: {valor}")

        print("\n=== Lista compartida ===")

        for elemento in lista:
            print(elemento)
