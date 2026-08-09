import threading
import queue
import time


resultados = {}

resultados_lock = threading.Lock()


def procesar_imagen(nombre):

    time.sleep(0.5)

    return f"{nombre} -> procesada"


def worker(cola, worker_id):

    contador = 0

    while True:

        imagen = cola.get()

        if imagen is None:
            cola.task_done()
            break

        resultado = procesar_imagen(imagen)

        print(f"Worker-{worker_id}: {resultado}")

        contador += 1

        cola.task_done()

    with resultados_lock:
        resultados[f"Worker-{worker_id}"] = contador


cola = queue.Queue()


workers = [
    threading.Thread(
        target=worker,
        args=(cola, i)
    )
    for i in range(4)
]


for w in workers:
    w.start()


inicio = time.perf_counter()


# Agregar 20 imágenes
for i in range(1, 21):
    cola.put(f"imagen_{i:03d}.jpg")


# Esperar que todas sean procesadas
cola.join()


# Señales de finalización
for _ in workers:
    cola.put(None)


for w in workers:
    w.join()


tiempo = time.perf_counter() - inicio


print("\n=== Verificación ===")
print(f"Tiempo total: {tiempo:.2f}s")

print("\nImágenes por worker:")

for nombre, cantidad in resultados.items():
    print(f"  {nombre}: {cantidad} imágenes")
