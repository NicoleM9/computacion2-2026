import threading
import queue
import urllib.request
import time


def worker(cola, resultados, lock):

    while True:

        url = cola.get()

        if url is None:
            cola.task_done()
            break

        inicio = time.time()

        try:

            response = urllib.request.urlopen(
                url,
                timeout=10
            )

            datos = response.read()

            with lock:
                resultados.append({
                    "url": url,
                    "ok": True,
                    "bytes": len(datos),
                    "tiempo": time.time() - inicio
                })

        except Exception as e:

            with lock:
                resultados.append({
                    "url": url,
                    "ok": False,
                    "error": str(e),
                    "tiempo": time.time() - inicio
                })

        cola.task_done()


if __name__ == "__main__":

    urls = [
        "https://www.python.org",
        "https://docs.python.org",
        "https://pypi.org",
        "https://www.google.com",
        "https://www.github.com"
    ]

    NUM_WORKERS = 4

    cola = queue.Queue()

    resultados = []

    lock = threading.Lock()


    # Crear pool fijo de workers
    workers = [
        threading.Thread(
            target=worker,
            args=(cola, resultados, lock)
        )
        for _ in range(NUM_WORKERS)
    ]


    for w in workers:
        w.start()


    inicio = time.time()


    # Agregar URLs
    for url in urls:
        cola.put(url)


    # Esperar que todas las URLs sean procesadas
    cola.join()


    # Enviar señal de finalización
    for _ in workers:
        cola.put(None)


    # Esperar a los workers
    for w in workers:
        w.join()


    tiempo_total = time.time() - inicio


    # Estadísticas
    exitosas = sum(
        1 for r in resultados
        if r["ok"]
    )

    fallidas = len(resultados) - exitosas

    bytes_total = sum(
        r.get("bytes", 0)
        for r in resultados
    )


    print("\n=== RESULTADOS ===")

    print(
        f"Descargas exitosas: "
        f"{exitosas}/{len(urls)}"
    )

    print(f"Descargas fallidas: {fallidas}")

    print(
        f"Bytes totales: "
        f"{bytes_total:,}"
    )

    print(
        f"Tiempo total: "
        f"{tiempo_total:.2f}s"
    )


    print("\n=== DETALLE ===")

    for resultado in resultados:

        if resultado["ok"]:

            print(
                f"OK | "
                f"{resultado['url']} | "
                f"{resultado['bytes']:,} bytes | "
                f"{resultado['tiempo']:.2f}s"
            )

        else:

            print(
                f"ERROR | "
                f"{resultado['url']} | "
                f"{resultado['error']} | "
                f"{resultado['tiempo']:.2f}s"
            )
