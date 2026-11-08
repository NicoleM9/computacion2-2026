#!/usr/bin/env python3
"""Servidor de comandos extendido con chat, nicknames, broadcast y timeouts.

Extensión del Ejercicio 4 sobre comandos.py.
"""
import socket
import socketserver
import sys
import threading
import time


class Handler(socketserver.StreamRequestHandler):

    def setup(self):
        """Se llama ANTES de handle(). Configura timeout e inicializa estado."""
        super().setup()               # imprescindible: crea rfile/wfile
        
        # 4. Agregamos timeout de 30 segundos de inactivacion
        self.timeout = 30.0
        
        # 1. Nick por defecto (usamos la IP:Puerto como identificador inicial)
        self.nick = f'{self.client_address[0]}:{self.client_address[1]}'

        with self.server.lock:
            self.server.conexiones += 1
            # 2. Guardamos la instancia del handler (self) para poder mandarle mensajes en BROADCAST
            self.server.activos.add(self)

    def finish(self):
        """Se llama DESPUÉS de handle(), incluso si hubo excepción."""
        with self.server.lock:
            self.server.activos.discard(self)
        super().finish()

    def responder(self, texto):
        """Envía un mensaje a este cliente capturando posibles errores de socket."""
        try:
            self.wfile.write((texto + '\n').encode('utf-8'))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # El cliente se desconectó de forma abrupta

    def handle(self):
        self.responder('Servidor de comandos extendido. Escribí AYUDA.')
        
        try:
            for linea in self.rfile:                    # framing por líneas
                partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
                if not partes:
                    continue
                cmd, resto = partes[0].upper(), (partes[1] if len(partes) > 1 else '')

                if cmd == 'TIME':
                    self.responder(time.strftime('%Y-%m-%d %H:%M:%S'))
                elif cmd == 'ECHO':
                    self.responder(resto)
                elif cmd == 'QUIEN':
                    with self.server.lock:
                        # Mostramos los nicks de todos los conectados
                        nicks = sorted(h.nick for h in self.server.activos)
                    self.responder(f'{len(nicks)} conectados: ' + ', '.join(nicks))
                elif cmd == 'CONTADOR':
                    with self.server.lock:
                        n = self.server.conexiones
                    self.responder(f'Conexiones totales desde el arranque: {n}')
                
                # 1. Comando NICK <nombre>
                elif cmd == 'NICK':
                    if resto:
                        nuevo_nick = resto.strip()
                        viejo_nick = self.nick
                        self.nick = nuevo_nick
                        self.responder(f'*** Tu nick ahora es {self.nick}')
                    else:
                        self.responder('*** Error: NICK requiere un argumento. Uso: NICK <nombre>')

                # 2 y 3. Comando BROADCAST <texto> con manejo de desconexiones
                elif cmd == 'BROADCAST':
                    if resto:
                        mensaje = f'[{self.nick}]: {resto}'
                        # Copiamos la lista bajo el lock para evitar race conditions al iterar
                        with self.server.lock:
                            destinatarios = list(self.server.activos)

                        # 3. Enviamos a todos. Si uno se desconecta justo mientras se le escribe,
                        # responder() captura la excepcion sin cortar la iteracion a los demas.
                        for destino in destinatarios:
                            if destino != self:
                                destino.responder(mensaje)
                    else:
                        self.responder('*** Error: BROADCAST requiere texto. Uso: BROADCAST <texto>')

                elif cmd == 'AYUDA':
                    self.responder('TIME | ECHO <texto> | QUIEN | CONTADOR | NICK <nombre> | BROADCAST <texto> | QUIT')
                elif cmd == 'QUIT':
                    self.responder('Chau')
                    return                              # cierra la conexión
                else:
                    self.responder(f'Comando desconocido: {cmd}')

        except (socket.timeout, TimeoutError):
            # 4. Manejo del timeout de 30 segundos
            print(f'[-] Cliente {self.client_address} ({self.nick}) desconectado por inactividad (timeout 30s)')

    def handle_error(self, *args):
        """Si handle() explota, el servidor NO se cae."""
        print(f'Error atendiendo a {self.client_address}')


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conexiones = 0
        # Ahora guardamos referencias a los objetos Handler activos
        self.activos = set()
        self.lock = threading.Lock()


if __name__ == '__main__':
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with Servidor(('0.0.0.0', puerto), Handler) as srv:
        print(f'Escuchando en 0.0.0.0:{puerto}')
        print('Probá: nc localhost', puerto)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')