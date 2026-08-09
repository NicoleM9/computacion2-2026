#!/usr/bin/env python3

from multiprocessing import Process, shared_memory
import struct
import time


NUM = 10
TAMAÑO = NUM * 4 + 1


def productor(nombre, cantidad):

    shm = shared_memory.SharedMemory(
        name=nombre
    )

    print("[PRODUCTOR] Escribiendo valores...")

    for i in range(cantidad):

        struct.pack_into(
            "i",
            shm.buf,
            i * 4,
            i * i
        )

    # Indicar que terminó
    shm.buf[-1] = 1

    print("[PRODUCTOR] Datos escritos")

    shm.close()


def consumidor(nombre, cantidad):

    shm = shared_memory.SharedMemory(
        name=nombre
    )

    print("[CONSUMIDOR] Esperando datos...")

    while shm.buf[-1] != 1:
        time.sleep(0.01)

    valores = []

    for i in range(cantidad):

        valor = struct.unpack_from(
            "i",
            shm.buf,
            i * 4
        )[0]

        valores.append(valor)

    print("[CONSUMIDOR] Valores:", valores)

    esperados = [
        i * i
        for i in range(cantidad)
    ]

    if valores == esperados:
        print("[CONSUMIDOR] VERIFICACION CORRECTA")
    else:
        print("[CONSUMIDOR] ERROR")

    shm.close()


shm = shared_memory.SharedMemory(
    create=True,
    size=TAMAÑO
)

print("Memoria creada:", shm.name)

productor_proceso = Process(
    target=productor,
    args=(shm.name, NUM)
)

consumidor_proceso = Process(
    target=consumidor,
    args=(shm.name, NUM)
)

consumidor_proceso.start()
productor_proceso.start()

productor_proceso.join()
consumidor_proceso.join()

shm.close()
shm.unlink()

print("Memoria compartida eliminada.")
