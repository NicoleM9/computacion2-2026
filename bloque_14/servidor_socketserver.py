import socketserver

class EchoHandler(socketserver.StreamRequestHandler):
    def handle(self):
        for linea in self.rfile:
            self.wfile.write(linea.upper())
            self.wfile.flush()

class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    with Servidor(('0.0.0.0', 8080), EchoHandler) as srv:
        print("Servidor ThreadingTCPServer corriendo...")
        srv.serve_forever()