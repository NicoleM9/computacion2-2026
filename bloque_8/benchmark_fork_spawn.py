import time
import multiprocessing as mp

def tarea_nula():
    pass

def medir_creacion(metodo, n_procesos=100):
    # Intentar establecer el método de inicio (solo puede setearse una vez por ejecución)
    try:
        mp.set_start_method(metodo, force=True)
    except RuntimeError:
        pass

    t0 = time.perf_counter()
    procesos = []
    
    for _ in range(n_procesos):
        p = mp.Process(target=tarea_nula)
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    t_total = time.perf_counter() - t0
    return t_total

if __name__ == '__main__':
    print("=== Benchmark de Creación de Procesos (100 ejecuciones) ===")
    
    # 1. Medición con FORK
    t_fork = medir_creacion('fork', 100)
    print(f"Tiempo total con 'fork' : {t_fork:.4f} segundos")

    # 2. Medición con SPAWN
    t_spawn = medir_creacion('spawn', 100)
    print(f"Tiempo total con 'spawn': {t_spawn:.4f} segundos")

    print(f"\n'fork' fue aproximadamente {t_spawn / t_fork:.2f} veces más rápido que 'spawn'.")