import socket
import struct

def recibir_exacto(sock, n):
    buffer = b''
    while len(buffer) < n:
        pedazo = sock.recv(n - len(buffer))
        if not pedazo:
            return None
        buffer += pedazo
    return buffer

def enviar_mensaje(sock, payload: bytes):
    header = struct.pack('!I', len(payload))
    sock.sendall(header + payload)

def recibir_mensaje(sock):
    header = recibir_exacto(sock, 4)
    if not header:
        return None
    longitud = struct.unpack('!I', header)[0]
    return recibir_exacto(sock, longitud)