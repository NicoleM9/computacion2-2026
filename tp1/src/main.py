import os
import json
import signal
import multiprocessing as mp
import curses

from src.senales import SignalHandlerSelfPipe
from src.display import TUI

# Importamos las funciones analizadoras directamente desde el recolector
from src.recolector import TRABAJADORES_ANALIZADORES

def main():
    config = {
        "intervals": {
            "resumen": 2.0,
            "memoria": 3.0,
            "fds": 5.0,
            "threads": 2.0,
            "senales": 10.0,
            "scheduling": 10.0,
            "sistema": 2.0
        }
    }
    
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                if "intervals" in cfg:
                    config["intervals"].update(cfg["intervals"])
        except Exception:
            pass

    manager = mp.Manager()
    snapshot_dict = manager.dict()
    running_flag = manager.Value('b', True)

    intervals = {
        k: manager.Value('d', float(v)) 
        for k, v in config["intervals"].items()
    }

    sig_handler = SignalHandlerSelfPipe()
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGUSR1, signal.SIGUSR2]:
        sig_handler.register_signal(sig)
    if hasattr(signal, 'SIGWINCH'):
        sig_handler.register_signal(signal.SIGWINCH)

    # Lanzar los 7 trabajadores en paralelo
    procesos = []
    for nombre, funcion in TRABAJADORES_ANALIZADORES.items():
        # Verificamos que exista el intervalo para esa vista; si no, usará un fallback de 1.0 s
        intervalo_val = intervals.get(nombre, manager.Value('d', 1.0))
        
        p = mp.Process(
            target=funcion, 
            args=(snapshot_dict, intervalo_val, running_flag),
            daemon=True  # Permite que los procesos no bloqueen la salida si el padre muere
        )
        p.start()
        procesos.append(p)

    tui = TUI(snapshot_dict, intervals, running_flag, sig_handler)
    try:
        curses.wrapper(tui.run)
    finally:
        # Señalar a los workers que se detengan
        running_flag.value = False
        sig_handler.close()
        
        # Limpieza rigurosa de los 7 procesos para evitar zombies
        for p in procesos:
            p.join(timeout=0.5)
            if p.is_alive():
                p.terminate()
                p.join(timeout=0.2)
                if p.is_alive():
                    p.kill()
                    p.join()

if __name__ == "__main__":
    main()