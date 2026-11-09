import time
import random
import os
from multiprocessing import Process

def worker(id_worker):
    demora = random.uniform(0.5, 2.0)
    print(f"Worker {id_worker} (PID {os.getpid()}) durmiendo {demora:.2f}s...")
    time.sleep(demora)
    print(f"Worker {id_worker} finalizado.")

if __name__ == '__main__':
    t_inicio = time.perf_counter()
    procesos = []

    # 1. Crear y arrancar los 5 procesos
    for i in range(1, 6):
        p = Process(target=worker, args=(i,))
        procesos.append(p)
        p.start()

    # 2. Esperar a que TODOS los procesos terminen
    for p in procesos:
        p.join()

    t_total = time.perf_counter() - t_inicio
    print(f"\nTodos los workers terminaron. Tiempo total medido: {t_total:.2f}s")