#!/usr/bin/env python3
import socket

def recibir_lineas(sock):
    buffer = b''
    while True:
        pedazo = sock.recv(4096)
        if not pedazo:
            if buffer:
                yield buffer
            return
        buffer += pedazo
        while b'\n' in buffer:
            linea, buffer = buffer.split(b'\n', 1)
            yield linea + b'\n'

def servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 8080))
        srv.listen(5)
        print("Servidor por delimitador activo...")
        while True:
            conn, _ = srv.accept()
            with conn:
                for linea in recibir_lineas(conn):
                    respuesta = linea.strip().upper() + b'\n'
                    conn.sendall(respuesta)

if __name__ == '__main__':
    servidor()