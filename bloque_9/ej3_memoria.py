#!/usr/bin/env python3

from multiprocessing import Process, Value, Array


def incrementar(contador, n_veces, identificador):

    for _ in range(n_veces):

        with contador.get_lock():
            contador.value += 1

    print(
        f"Worker {identificador} terminó "
        f"sus {n_veces} incrementos"
    )


def llenar_array(arr, valor_inicial, identificador):

    tamaño_por_proceso = len(arr) // 4

    inicio = identificador * tamaño_por_proceso
    fin = inicio + tamaño_por_proceso

    for i in range(inicio, fin):
        arr[i] = valor_inicial + i


if __name__ == "__main__":

    # =========================
    # VALUE
    # =========================

    contador = Value('i', 0)

    procesos = []

    for i in range(4):

        p = Process(
            target=incrementar,
            args=(contador, 10000, i)
        )

        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    print("\n=== Verificación del contador ===")
    print(f"Esperado: 40000")
    print(f"Obtenido: {contador.value}")

    if contador.value == 40000:
        print("VERIFICACIÓN CORRECTA")
    else:
        print("ERROR")

    # =========================
    # ARRAY
    # =========================

    arr = Array('i', 100)

    procesos = []

    for i in range(4):

        p = Process(
            target=llenar_array,
            args=(arr, 1000, i)
        )

        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    print("\n=== Verificación del Array ===")

    print("Primeros 10:")
    print(list(arr)[:10])

    print("\nÚltimos 10:")
    print(list(arr)[-10:])

    errores = 0

    for i in range(100):

        esperado = 1000 + i

        if arr[i] != esperado:
            errores += 1

    print(f"\nErrores encontrados: {errores}")

    if errores == 0:
        print("VERIFICACIÓN CORRECTA")
