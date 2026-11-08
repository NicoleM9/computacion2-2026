import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Comentada en el test 1
s.settimeout(2.0)

try:
    s.sendto(b'DISCOVER?', ('255.255.255.255', 8082))
except PermissionError as e:
    print(f"Error: {e}")