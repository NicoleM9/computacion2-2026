#!/usr/bin/env python3

from multiprocessing import Process, Array
import random


NUM_CUENTAS = 5
SALDO_INICIAL = 1000

NUM_PROCESOS = 3
TRANSFERENCIAS_POR_PROCESO = 100


def mostrar_saldos(cuentas, etiqueta):

    saldos = [
        cuentas[i]
        for i in range(NUM_CUENTAS)
    ]

    total = sum(saldos)

    print(
        f"[{etiqueta}] "
        f"Saldos: {saldos} "
        f"| Total: {total}"
    )


def cajero(cuentas, cajero_id, cantidad):

    for _ in range(cantidad):

        origen = random.randint(
            0,
            NUM_CUENTAS - 1
        )

        destino = random.randint(
            0,
            NUM_CUENTAS - 1
        )

        while destino == origen:

            destino = random.randint(
                0,
                NUM_CUENTAS - 1
            )

        monto = random.randint(1, 50)

        if cuentas[origen] >= monto:

            cuentas[origen] -= monto
            cuentas[destino] += monto

    print(
        f"[Cajero {cajero_id}] "
        f"Completó {cantidad} transferencias"
    )


cuentas = Array(
    "i",
    [SALDO_INICIAL] * NUM_CUENTAS
)

total_esperado = (
    NUM_CUENTAS * SALDO_INICIAL
)

print("=== BANCO ===")

print(
    f"Cuentas: {NUM_CUENTAS}"
)

print(
    f"Saldo total esperado: "
    f"{total_esperado}"
)

mostrar_saldos(
    cuentas,
    "INICIO"
)


procesos = []

for i in range(NUM_PROCESOS):

    p = Process(
        target=cajero,
        args=(
            cuentas,
            i,
            TRANSFERENCIAS_POR_PROCESO
        )
    )

    p.start()

    procesos.append(p)


for p in procesos:
    p.join()


mostrar_saldos(
    cuentas,
    "FINAL"
)


total_final = sum(
    cuentas[i]
    for i in range(NUM_CUENTAS)
)

print("\n=== VERIFICACION ===")

print(
    f"Total esperado: {total_esperado}"
)

print(
    f"Total final: {total_final}"
)

if total_final == total_esperado:

    print(
        "El total se conserva."
    )

else:

    diferencia = (
        total_esperado - total_final
    )

    print(
        f"¡ERROR! Diferencia: {diferencia}"
    )

    print(
        "Posible race condition."
    )
