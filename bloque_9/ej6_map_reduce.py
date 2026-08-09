#!/usr/bin/env python3

from multiprocessing import Pool
from functools import reduce


TEXTOS = [
    "el rapido zorro marron salta sobre el perro perezoso",
    "el perro duerme bajo el arbol mientras el zorro corre",
    "rapido como el viento el zorro vuelve a saltar sobre el perro",
    "el arbol es viejo y el perro lo mira con curiosidad",
    "saltar correr el zorro y el perro juegan bajo el arbol",
]


def mapper(texto):

    conteo = {}

    for palabra in texto.lower().split():

        conteo[palabra] = (
            conteo.get(palabra, 0) + 1
        )

    return conteo


def reducer(diccionario1, diccionario2):

    resultado = diccionario1.copy()

    for palabra, cantidad in diccionario2.items():

        resultado[palabra] = (
            resultado.get(palabra, 0)
            + cantidad
        )

    return resultado


if __name__ == "__main__":

    print("=== MAP ===")

    with Pool(4) as pool:

        conteos = pool.map(
            mapper,
            TEXTOS
        )

    print("Conteos parciales:")

    for i, conteo in enumerate(conteos):

        print(f"\nTexto {i}:")
        print(conteo)

    print("\n=== REDUCE ===")

    conteo_total = reduce(
        reducer,
        conteos
    )

    palabras_ordenadas = sorted(
        conteo_total.items(),
        key=lambda x: -x[1]
    )

    print("\nTop palabras:")

    for palabra, cantidad in palabras_ordenadas[:10]:

        print(
            f"{palabra:15s} {cantidad}"
        )

    # Verificación

    total_palabras = sum(
        conteo_total.values()
    )

    print(
        f"\nTotal de palabras contabilizadas: "
        f"{total_palabras}"
    )
