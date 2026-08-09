import threading
import time


# ==================================================
# VERSIÓN INSEGURA
# ==================================================

saldo_inseguro = 1000


def retirar_inseguro(monto):
    global saldo_inseguro

    if saldo_inseguro >= monto:

        time.sleep(0.001)

        saldo_inseguro -= monto


hilos = [
    threading.Thread(
        target=retirar_inseguro,
        args=(200,)
    )
    for _ in range(10)
]


for h in hilos:
    h.start()

for h in hilos:
    h.join()


print("=== Sin Lock ===")
print(f"Saldo final: ${saldo_inseguro}")


# ==================================================
# VERSIÓN SEGURA
# ==================================================

saldo_seguro = 1000

lock = threading.Lock()


def retirar_seguro(monto):
    global saldo_seguro

    with lock:

        if saldo_seguro >= monto:

            time.sleep(0.001)

            saldo_seguro -= monto

            print(
                f"Retiro de ${monto} OK. "
                f"Saldo: ${saldo_seguro}"
            )

        else:

            print(
                f"Saldo insuficiente para ${monto}. "
                f"Saldo: ${saldo_seguro}"
            )


hilos = [
    threading.Thread(
        target=retirar_seguro,
        args=(200,)
    )
    for _ in range(10)
]


for h in hilos:
    h.start()

for h in hilos:
    h.join()


print("\n=== Con Lock ===")
print(f"Saldo final: ${saldo_seguro}")
