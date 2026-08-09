import threading
import time


class ContadorHilo(threading.Thread):

    def __init__(self, nombre, limite):
        super().__init__(name=nombre)

        self.limite = limite
        self.resultado = ""

    def run(self):

        numeros = []

        for i in range(1, self.limite + 1):
            numeros.append(str(i))
            time.sleep(0.1)

        self.resultado = ", ".join(numeros)


hilos = [
    ContadorHilo("Contador-1", 5),
    ContadorHilo("Contador-2", 8),
    ContadorHilo("Contador-3", 3)
]


for h in hilos:
    h.start()


for h in hilos:
    h.join()


print("\n=== Resultados ===")

for h in hilos:
    print(f"[{h.name}] resultado: {h.resultado}")
