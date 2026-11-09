import os
from multiprocessing import Process


def tarea_hijo():
    """Función que ejecutará el proceso secundario (hijo)."""
    print(f"[Hijo] PID actual: {os.getpid()}")
    print(f"[Hijo] PID del Padre: {os.getppid()}")


if __name__ == "__main__":
    # 1. Se crea la instancia del proceso indicando la función a ejecutar
    p = Process(target=tarea_hijo)

    # 2. Se inicia la ejecución del nuevo proceso en el Sistema Operativo
    p.start()
    print(f"[Padre] Creé al proceso hijo con PID: {p.pid}")

    # 3. El padre espera a que el hijo termine (hace la limpieza automática)
    p.join()
    print("[Padre] El hijo finalizó. Proceso completado.")