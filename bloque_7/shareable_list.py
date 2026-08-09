#!/usr/bin/env python3

from multiprocessing import Process
from multiprocessing import shared_memory


def actualizar_datos(nombre):

    lista = shared_memory.ShareableList(
        name=nombre
    )

    lista[0] = 42
    lista[1] = 3.14159
    lista[2] = "actualizado"
    lista[3] = False

    print(
        "[WORKER] Lista actualizada:",
        list(lista)
    )

    lista.shm.close()


lista = shared_memory.ShareableList(
    [
        0,
        0.0,
        "                    ",
        True
    ],
    name="mi_lista_comp"
)

print("Antes:", list(lista))

p = Process(
    target=actualizar_datos,
    args=(lista.shm.name,)
)

p.start()
p.join()

print("Después:", list(lista))

# Verificación
esperado = [
    42,
    3.14159,
    "actualizado",
    False
]

print("\n=== VERIFICACION ===")

if list(lista) == esperado:
    print("Datos correctos.")
else:
    print("ERROR en los datos.")

lista.shm.close()
lista.shm.unlink()
