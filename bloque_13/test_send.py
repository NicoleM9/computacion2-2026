import socket

datos = b'X' * (10 * 1024 * 1024) # 10 MB
with socket.create_connection(('localhost', 8080)) as s:
    enviados = s.send(datos)
    print(f'Total a enviar: {len(datos)} bytes. Enviados con send(): {enviados} bytes.')