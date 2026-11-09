import time
import os
from multiprocessing import Process, Queue

# Elemento centinela para notificar el fin de la transmisión
CENTINELA = None

def productor(cola):
    print(f"[Productor PID {os.getpid()}] Generando 10 ítems...")
    for i in range(1, 11):
        item = f"Producto-{i}"
        cola.put(item)
        print(f"  [Productor] Generó: {item}")
        time.sleep(0.1)
    
    # Enviar la señal de parada (centinela)
    cola.put(CENTINELA)
    print("[Productor] Finalizó el envío.")

def consumidor(cola):
    print(f"[Consumidor PID {os.getpid()}] Esperando ítems...")
    while True:
        item = cola.get() # Bloquea hasta que haya un elemento disponible
        if item is CENTINELA:
            print("[Consumidor] Recibió centinela. Apagando...")
            break
        print(f"    [Consumidor] Procesó: {item}")
        time.sleep(0.2)

if __name__ == '__main__':
    cola_compartida = Queue()

    p_prod = Process(target=productor, args=(cola_compartida,))
    p_cons = Process(target=consumidor, args=(cola_compartida,))

    p_prod.start()
    p_cons.start()

    p_prod.join()
    p_cons.join()
    print("Pipeline Productor-Consumidor finalizado con éxito.")