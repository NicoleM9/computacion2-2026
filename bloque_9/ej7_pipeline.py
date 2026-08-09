#!/usr/bin/env python3

from multiprocessing import Process, Queue
import time


def etapa_multiplicar(entrada, salida):

    while True:

        dato = entrada.get()

        if dato is None:

            salida.put(None)

            break

        time.sleep(0.05)

        resultado = dato * 2

        salida.put(resultado)


def etapa_sumar(entrada, salida):

    while True:

        dato = entrada.get()

        if dato is None:

            salida.put(None)

            break

        time.sleep(0.05)

        resultado = dato + 10

        salida.put(resultado)


def etapa_formatear(entrada, salida):

    while True:

        dato = entrada.get()

        if dato is None:

            salida.put(None)

            break

        time.sleep(0.05)

        resultado = f"resultado_{dato:03d}"

        salida.put(resultado)


if __name__ == "__main__":

    q1 = Queue()
    q2 = Queue()
    q3 = Queue()
    q4 = Queue()

    p1 = Process(
        target=etapa_multiplicar,
        args=(q1, q2)
    )

    p2 = Process(
        target=etapa_sumar,
        args=(q2, q3)
    )

    p3 = Process(
        target=etapa_formatear,
        args=(q3, q4)
    )

    p1.start()
    p2.start()
    p3.start()

    # Alimentar pipeline

    for i in range(10):

        q1.put(i)

    q1.put(None)

    # Recibir resultados

    print("=== RESULTADOS ===")

    while True:

        resultado = q4.get()

        if resultado is None:
            break

        print(f"Final: {resultado}")

    p1.join()
    p2.join()
    p3.join()

    print("\nPipeline terminado.")
