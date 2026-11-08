#!/usr/bin/env python3
"""HTTP sin frameworks: servidor extendido con soporte DELETE e HTTP/1.1.

Extensión de la Clase 19 basada en crudo.py.
"""
import http.server
import json
import socket
import socketserver
import sys
import threading
import time

PUERTO = 8080


def mostrar_jerarquia():
    """http.server no inventa nada: es socketserver con HTTP encima."""
    print('=' * 66)
    print('1. De qué está hecho http.server')
    print('=' * 66)
    for clase in (http.server.HTTPServer,
                  http.server.ThreadingHTTPServer,
                  http.server.BaseHTTPRequestHandler):
        bases = ', '.join(b.__name__ for b in clase.__bases__)
        print(f'  {clase.__name__:<24} -> {bases}')
    print('\n  Todo viene de la clase 16: TCPServer, ThreadingMixIn y')
    print('  StreamRequestHandler (el que trae rfile/wfile con framing).')


class Handler(http.server.BaseHTTPRequestHandler):
    """El framework llama a do_GET, do_POST o do_DELETE según el método del pedido."""

    # 4. Cambiamos el protocolo a HTTP/1.1 para soportar keep-alive nativamente
    protocol_version = "HTTP/1.1"

    def _responder(self, codigo, datos=None):
        """Genera y envía la respuesta HTTP adecuada."""
        if datos is not None:
            cuerpo = json.dumps(datos).encode('utf-8')
            self.send_response(codigo)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(cuerpo)))   # framing por longitud
            self.end_headers()
            self.wfile.write(cuerpo)
        else:
            # Respuestas sin cuerpo (ej: 204 No Content)
            self.send_response(codigo)
            self.send_header('Content-Length', '0')
            self.end_headers()

    def do_GET(self):
        self._responder(200, {'metodo': 'GET', 'ruta': self.path})

    def do_POST(self):
        # Hay que leer EXACTAMENTE Content-Length bytes
        n = int(self.headers.get('Content-Length', 0))
        cuerpo = self.rfile.read(n)
        self._responder(201, {'metodo': 'POST', 'recibido': cuerpo.decode('utf-8', errors='replace')})

    # 1. Agregamos el método do_DELETE
    def do_DELETE(self):
        # En HTTP, para un DELETE exitoso conviene devolver 204 No Content
        # o 200 OK con un JSON de confirmación.
        self._responder(204)

    def log_message(self, formato, *args):
        pass                      # silenciar el log por defecto


def hablar_http_a_mano(puerto):
    """Un pedido HTTP escrito byte por byte sobre un socket."""
    print('\n' + '=' * 66)
    print('2. Un pedido HTTP escrito a mano (probando HTTP/1.1)')
    print('=' * 66)

    pedido = (
        b'GET /tareas/42 HTTP/1.1\r\n'
        b'Host: localhost\r\n'
        b'Accept: application/json\r\n'
        b'Connection: close\r\n'
        b'\r\n'                      # línea vacía: acá terminan los headers
    )
    print('  --- lo que mandamos ---')
    print('  ' + pedido.decode().replace('\r\n', '\\r\\n\n  ').rstrip())

    with socket.create_connection(('localhost', puerto), timeout=5) as s:
        s.sendall(pedido)
        respuesta = b''
        while True:
            pedazo = s.recv(4096)
            if not pedazo:
                break
            respuesta += pedazo

    print('\n  --- lo que volvió ---')
    cabeza, _, cuerpo = respuesta.partition(b'\r\n\r\n')
    for linea in cabeza.decode().splitlines():
        print(f'  {linea}')
    print(f'  (línea vacía)')
    print(f'  {cuerpo.decode()}')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'servidor':
        with http.server.ThreadingHTTPServer(('', PUERTO), Handler) as srv:
            print(f'Escuchando en http://localhost:{PUERTO}')
            print('Probá:')
            print('  curl localhost:8080/hola')
            print('  curl -X POST localhost:8080/ -d "algo"')
            print('  curl -X DELETE localhost:8080/tareas/1 -v')
            print('  curl -X PATCH localhost:8080/ -v')
            srv.serve_forever()
        return

    mostrar_jerarquia()

    servidor = http.server.ThreadingHTTPServer(('', PUERTO), Handler)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    time.sleep(0.3)
    try:
        hablar_http_a_mano(PUERTO)
    finally:
        servidor.shutdown()
        servidor.server_close()


if __name__ == '__main__':
    main()