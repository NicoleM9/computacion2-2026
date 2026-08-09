#!/usr/bin/env python3

from multiprocessing import Process, Array, Value
import math


TAMAÑO = 100
NUM_PROCESOS = 4


def calcular_senos(resultado, inicio, fin, suma):

    suma_local = 0.0

    for i in range(inicio, fin):

        valor = math.sin(i * 0.01)

        resultado[i] = valor

        suma_local += valor

    # Intencionalmente sin sincronización
    suma.value += suma_local


resultado = Array("d", TAMAÑO)

suma = Value("d", 0.0)

chunk = TAMAÑO // NUM_PROCESOS

procesos = []

for i in range(NUM_PROCESOS):

    inicio = i * chunk
    fin = (
        TAMAÑO
        if i == NUM_PROCESOS - 1
        else (i + 1) * chunk
    )

    p = Process(
        target=calcular_senos,
        args=(
            resultado,
            inicio,
            fin,
            suma
        )
    )

    p.start()
    procesos.append(p)


for p in procesos:
    p.join()


print("=== Primeros 20 resultados ===")

for i in range(20):
    print(
        f"resultado[{i}] = "
        f"{resultado[i]:.6f}"
    )


suma_esperada = sum(
    math.sin(i * 0.01)
    for i in range(TAMAÑO)
)

print("\n=== VERIFICACION ARRAY ===")

errores = 0

for i in range(TAMAÑO):

    esperado = math.sin(i * 0.01)

    if abs(resultado[i] - esperado) > 1e-12:
        errores += 1


print(f"Errores en Array: {errores}")

print("\n=== VERIFICACION SUMA ===")

print(f"Suma esperada: {suma_esperada:.12f}")
print(f"Suma obtenida: {suma.value:.12f}")
print(
    f"Diferencia: "
    f"{suma_esperada - suma.value:.12f}"
)

if errores == 0:
    print("Array correcto.")

if abs(suma.value - suma_esperada) < 1e-10:
    print("La suma coincide.")
else:
    print("La suma puede presentar race condition.")
