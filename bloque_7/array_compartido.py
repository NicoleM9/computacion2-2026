#!/usr/bin/env python3

from multiprocessing import Process, Array
import time


def calcular_rango(resultado, inicio, fin):

    for i in range(inicio, fin):
        resultado[i] = i * i


TAMAÑO = 1000
NUM_PROCESOS = 4

resultado = Array("i", TAMAÑO)

chunk = TAMAÑO // NUM_PROCESOS

inicio_tiempo = time.time()

procesos = []

for i in range(NUM_PROCESOS):

    inicio = i * chunk

    if i == NUM_PROCESOS - 1:
        fin = TAMAÑO
    else:
        fin = (i + 1) * chunk

    p = Process(
        target=calcular_rango,
        args=(
            resultado,
            inicio,
            fin
        )
    )

    p.start()
    procesos.append(p)


for p in procesos:
    p.join()


duracion = time.time() - inicio_tiempo

print(f"Cálculo completado en {duracion:.4f}s")

print(f"resultado[0] = {resultado[0]}")
print(f"resultado[10] = {resultado[10]}")
print(f"resultado[99] = {resultado[99]}")
print(f"resultado[999] = {resultado[999]}")


errores = 0

for i in range(TAMAÑO):

    if resultado[i] != i * i:
        errores += 1


print(f"Errores: {errores}")

if errores == 0:
    print("VERIFICACION: TODOS LOS RESULTADOS SON CORRECTOS")
else:
    print("VERIFICACION: HAY ERRORES")
