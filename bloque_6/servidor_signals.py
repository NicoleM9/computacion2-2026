#!/usr/bin/env python3

"""
Servidor que responde a señales.

Uso:
    python3 servidor_signals.py

Señales:
    kill -HUP <pid>   -> Recargar config
    kill -USR1 <pid>  -> Mostrar stats
    kill -USR2 <pid>  -> Rotar logs
    kill <pid>        -> Shutdown limpio
"""

import signal
import time
import os


class Servidor:

    def __init__(self):

        self.ejecutando = True

        self.config = {
            "max_conexiones": 100,
            "timeout": 30
        }

        self.stats = {
            "requests": 0,
            "errores": 0,
            "inicio": time.time()
        }

        self._registrar_manejadores()

    def _registrar_manejadores(self):

        signal.signal(
            signal.SIGTERM,
            self._shutdown
        )

        signal.signal(
            signal.SIGINT,
            self._shutdown
        )

        signal.signal(
            signal.SIGHUP,
            self._reload_config
        )

        signal.signal(
            signal.SIGUSR1,
            self._mostrar_stats
        )

        signal.signal(
            signal.SIGUSR2,
            self._rotar_logs
        )

    def _shutdown(self, sig, frame):

        nombre = signal.Signals(sig).name

        print(
            f"\n[{nombre}] "
            f"Iniciando shutdown..."
        )

        self.ejecutando = False

    def _reload_config(self, sig, frame):

        print(
            "\n[SIGHUP] "
            "Recargando configuración..."
        )

        self.config["max_conexiones"] += 10

        self.config["recargado"] = time.ctime()

        print(
            f"[SIGHUP] Nueva config: "
            f"{self.config}"
        )

    def _mostrar_stats(self, sig, frame):

        uptime = time.time() - self.stats["inicio"]

        print(
            "\n[SIGUSR1] === Estadísticas ==="
        )

        print(f"  Uptime: {uptime:.1f}s")
        print(
            f"  Requests: "
            f"{self.stats['requests']}"
        )
        print(
            f"  Errores: "
            f"{self.stats['errores']}"
        )
        print(
            f"  Config: "
            f"{self.config}"
        )

    def _rotar_logs(self, sig, frame):

        print(
            "\n[SIGUSR2] Rotando logs..."
        )

        print(
            "[SIGUSR2] Logs rotados a "
            f"server.log.{int(time.time())}"
        )

    def procesar_request(self):

        self.stats["requests"] += 1

        time.sleep(0.1)

        if self.stats["requests"] % 10 == 0:
            self.stats["errores"] += 1

    def run(self):

        print(
            f"Servidor iniciado "
            f"(PID {os.getpid()})"
        )

        print("Comandos disponibles:")

        print(
            f"  kill -HUP {os.getpid()} "
            "-> Recargar config"
        )

        print(
            f"  kill -USR1 {os.getpid()} "
            "-> Ver stats"
        )

        print(
            f"  kill -USR2 {os.getpid()} "
            "-> Rotar logs"
        )

        print(
            f"  kill {os.getpid()} "
            "-> Shutdown"
        )

        print()

        while self.ejecutando:

            self.procesar_request()

        print("Realizando cleanup...")

        time.sleep(0.5)

        print(
            "Servidor terminado. "
            f"Requests procesadas: "
            f"{self.stats['requests']}"
        )


if __name__ == "__main__":

    servidor = Servidor()

    servidor.run()
