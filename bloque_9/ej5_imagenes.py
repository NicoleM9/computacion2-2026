#!/usr/bin/env python3

from multiprocessing import Pool
import time
import random


def crear_imagen(tamaño):

    return [
        [
            random.randint(0, 255)
            for _ in range(tamaño)
        ]
        for _ in range(tamaño)
    ]


def aplicar_filtro(imagen):

    tamaño = len(imagen)

    resultado = [
        [0] * tamaño
        for _ in range(tamaño)
    ]

    for i in range(1, tamaño - 1):

        for j in range(1, tamaño - 1):

            suma = 0

            for di in [-1, 0, 1]:

                for dj in [-1, 0, 1]:

                    suma += imagen[i + di][j + dj]

            resultado[i][j] = suma // 9

    return resultado


def procesar_imagen(datos):

    indice, imagen = datos

    inicio = time.time()

    resultado = aplicar_filtro(imagen)

    duracion = time.time() - inicio

    checksum = sum(
        sum(fila)
        for fila in resultado
    )

    return indice, duracion, checksum


if __name__ == "__main__":

    NUM_IMAGENES = 8
    TAMAÑO = 100

    print(
        f"Creando {NUM_IMAGENES} imágenes "
        f"de {TAMAÑO}x{TAMAÑO}..."
    )

    imagenes = [
        (i, crear_imagen(TAMAÑO))
        for i in range(NUM_IMAGENES)
    ]

    # ==========================
    # SECUENCIAL
    # ==========================

    print("\n=== Procesamiento secuencial ===")

    inicio = time.time()

    resultados_secuenciales = []

    for imagen in imagenes:

        resultado = procesar_imagen(imagen)

        resultados_secuenciales.append(resultado)

    tiempo_secuencial = time.time() - inicio

    print(
        f"Tiempo secuencial: "
        f"{tiempo_secuencial:.4f}s"
    )

    # ==========================
    # PARALELO
    # ==========================

    print("\n=== Procesamiento paralelo ===")

    inicio = time.time()

    with Pool(4) as pool:

        resultados = pool.map(
            procesar_imagen,
            imagenes
        )

    tiempo_paralelo = time.time() - inicio

    # ==========================
    # RESULTADOS
    # ==========================

    print("\nResultados:")

    for indice, duracion, checksum in resultados:

        print(
            f"Imagen {indice}: "
            f"{duracion:.4f}s "
            f"checksum={checksum}"
        )

    print(
        f"\nTiempo paralelo: "
        f"{tiempo_paralelo:.4f}s"
    )

    speedup = (
        tiempo_secuencial /
        tiempo_paralelo
    )

    print(f"Speedup: {speedup:.2f}x")

    # ==========================
    # VERIFICACIÓN
    # ==========================

    print("\n=== VERIFICACIÓN ===")

    if len(resultados) == NUM_IMAGENES:
        print("Cantidad de imágenes correcta.")
    else:
        print("ERROR: faltan imágenes.")

    if speedup > 1:
        print("El procesamiento paralelo fue más rápido.")
    else:
        print(
            "El procesamiento paralelo "
            "no fue más rápido en esta ejecución."
        )
