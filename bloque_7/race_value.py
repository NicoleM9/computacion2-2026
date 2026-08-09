#!/usr/bin/env python3

from multiprocessing import Process, Value


def incrementar(contador, cantidad, nombre):

    print(f"[{nombre}] Iniciando {cantidad} incrementos...")

    for _ in range(cantidad):
        contador.value += 1

    print(f"[{nombre}] Terminado")


contador = Value("i", 0)

N = 100000
NUM_PROCESOS = 4

procesos = []

for i in range(NUM_PROCESOS):

    p = Process(
        target=incrementar,
        args=(
            contador,
            N,
            f"P{i}"
        )
    )

    p.start()
    procesos.append(p)


for p in procesos:
    p.join()


esperado = NUM_PROCESOS * N
obtenido = contador.value
diferencia = esperado - obtenido

print("\n=== VERIFICACION ===")
print(f"Esperado: {esperado}")
print(f"Obtenido: {obtenido}")
print(f"Diferencia: {diferencia}")

if obtenido == esperado:
    print("No se observaron incrementos perdidos.")
else:
    print("Se observaron incrementos perdidos.")
    print("Existe una race condition.")
