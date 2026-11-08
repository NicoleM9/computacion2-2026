import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(2)
s.connect(('localhost', 9999))
s.send(b'hola')

try:
    s.recv(4096)
except ConnectionRefusedError:
    print('ConnectionRefusedError')
except TimeoutError:
    print('timeout')