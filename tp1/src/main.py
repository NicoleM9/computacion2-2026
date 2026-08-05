import os
import json
import signal
import multiprocessing as mp
import curses

from src.senales import SignalHandlerSelfPipe
from src.recolector import worker_recolector
from src.display import TUI

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

    p_recolector = mp.Process(
        target=worker_recolector, 
        args=(snapshot_dict, intervals, running_flag)
    )
    p_recolector.start()

    tui = TUI(snapshot_dict, intervals, running_flag, sig_handler)
    try:
        curses.wrapper(tui.run)
    finally:
        running_flag.value = False
        sig_handler.close()
        
        p_recolector.join(timeout=1.0)
        if p_recolector.is_alive():
            p_recolector.terminate()

if __name__ == "__main__":
    main()