#!/usr/bin/env python3

import threading
import time
import random


class CuentaInsegura:
    def __init__(self, saldo):
        self.saldo = saldo

    def depositar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)
        self.saldo = actual + cantidad

    def retirar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)

        if actual >= cantidad:
            self.saldo = actual - cantidad
            return True

        return False


cuenta = CuentaInsegura(1000)


def operaciones_aleatorias():
    for _ in range(100):
        if random.choice([True, False]):
            cuenta.depositar(10)
        else:
            cuenta.retirar(10)


threads = [
    threading.Thread(target=operaciones_aleatorias)
    for _ in range(10)
]

for t in threads:
    t.start()

for t in threads:
    t.join()


print(f"Saldo inicial: $1000")
print(f"Saldo obtenido: ${cuenta.saldo}")
print("El resultado puede variar debido a la race condition.")
