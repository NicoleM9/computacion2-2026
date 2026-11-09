import time
from multiprocessing import Process, Pipe

def hijo(conn):
    for i in range(1, 6):
        # 1. Esperar mensaje del Padre
        msg_recibido = conn.recv()
        print(f"  [Hijo] Recibió: '{msg_recibido}'")
        
        # 2. Responder al Padre
        msg_respuesta = f"PONG {i}"
        time.sleep(0.1)
        conn.send(msg_respuesta)
    
    conn.close()

if __name__ == '__main__':
    # Pipe(duplex=True) crea un canal bidireccional
    padre_conn, hijo_conn = Pipe(duplex=True)

    p_hijo = Process(target=hijo, args=(hijo_conn,))
    p_hijo.start()

    print("[Padre] Iniciando juego de Ping-Pong...")
    for i in range(1, 6):
        msg_envio = f"PING {i}"
        print(f"[Padre] Envió: '{msg_envio}'")
        padre_conn.send(msg_envio)
        
        # Esperar respuesta del Hijo
        respuesta = padre_conn.recv()
        print(f"[Padre] Recibió de vuelta: '{respuesta}'\n")

    p_hijo.join()
    padre_conn.close()
    print("Partida de Ping-Pong terminada.")