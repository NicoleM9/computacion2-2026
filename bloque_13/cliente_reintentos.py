import socket
import time

def conectar_con_reintentos(host, puerto, intentos=5):
    espera = 1
    for i in range(intentos):
        try:
            s = socket.create_connection((host, puerto))
            print("¡Conectado!")
            return s
        except ConnectionRefusedError:
            print(f"Intento {i+1} fallido. Reintentando en {espera}s...")
            time.sleep(espera)
            espera *= 2
    raise Exception("Servidor no disponible.")

if __name__ == '__main__':
    conectar_con_reintentos('localhost', 8080)