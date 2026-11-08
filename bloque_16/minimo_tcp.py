import socketserver

class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print(f"Tipo de self.request: {type(self.request)}")
        print(f"ID del handler: {id(self)}")
        datos = self.request.recv(1024)
        if datos:
            self.request.sendall(b"ECHO: " + datos)

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", 8080), EchoHandler) as server:
        server.serve_forever()