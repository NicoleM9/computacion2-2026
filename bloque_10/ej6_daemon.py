import threading
import time


def loop_infinito(label):

    while True:
        print(f"[{label}] trabajando...")
        time.sleep(1)


h = threading.Thread(
    target=loop_infinito,
    args=("daemon",),
    daemon=True
)

h.start()

time.sleep(3)

print("Main terminó: el daemon muere automáticamente")
