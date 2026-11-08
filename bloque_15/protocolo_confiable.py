#!/usr/bin/env python3
import socket
import struct

def empaquetar(seq: int, payload: bytes) -> bytes:
    return struct.pack('!I', seq) + payload

def desempaquetar(datos: bytes):
    (seq,) = struct.unpack('!I', datos[:4])
    return seq, datos[4:]

# --- CLIENTE CONFIABLE ---
def cliente_confiable(host, puerto, mensaje: bytes):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    seq_actual = 1
    intentos_max = 5

    msg_empaquetado = empaquetar(seq_actual, mensaje)
    
    for intento in range(intentos_max):
        try:
            sock.sendto(msg_empaquetado, (host, puerto))
            datos, _ = sock.recvfrom(65535)
            seq_resp, payload_resp = desempaquetar(datos)
            
            # Descartar respuestas con número de secuencia incorrecto
            if seq_resp == seq_actual:
                return payload_resp
        except TimeoutError:
            pass
            
    raise TimeoutError("Falló la entrega confiable.")

# --- SERVIDOR CONFIABLE DEDUPLICADO ---
def servidor_confiable(puerto):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', puerto))
    
    # Mapeo: direccion_cliente -> (ultimo_seq_visto, ultima_respuesta)
    historial_clientes = {}
    trabajos_reales = 0

    print(f"Servidor confiable UDP listo en puerto {puerto}...")
    
    while True:
        datos, cliente = sock.recvfrom(65535)
        if len(datos) < 4:
            continue
            
        seq, payload = desempaquetar(datos)
        
        if cliente in historial_clientes and historial_clientes[cliente][0] == seq:
            # Reenviar respuesta previa sin repetir trabajo
            _, resp_guardada = historial_clientes[cliente]
            sock.sendto(empaquetar(seq, resp_guardada), cliente)
        else:
            # Trabajo real de la capa de aplicación
            trabajos_reales += 1
            respuesta_payload = payload.upper()
            
            historial_clientes[cliente] = (seq, respuesta_payload)
            print(f"[TRABAJO REAL #{trabajos_reales}] Procesado seq={seq} de {cliente}")
            
            sock.sendto(empaquetar(seq, respuesta_payload), cliente)