"""Servidor de latencia fija para las mediciones (solo librería estándar).
GET /delay/N  ->  responde 200 con 1024 bytes después de N segundos."""
import asyncio
import signal

CUERPO = b"x" * 1024


async def manejar(lector, escritor):
    try:
        linea = await lector.readline()
        while (await lector.readline()) not in (b"\r\n", b"\n", b""):
            pass  # descartar cabeceras
        partes = linea.decode(errors="replace").split()
        ruta = partes[1] if len(partes) > 1 else "/"
        segundos = 0.0
        if ruta.startswith("/delay/"):
            try:
                segundos = float(ruta.split("/")[2].split("?")[0])
            except (ValueError, IndexError):
                pass
        await asyncio.sleep(min(segundos, 60))
        escritor.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
            b"Content-Length: %d\r\nConnection: close\r\n\r\n" % len(CUERPO) + CUERPO)
        await escritor.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        escritor.close()


async def main():
    parar = asyncio.Event()
    loop = asyncio.get_running_loop()
    for s in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(s, parar.set)
    servidor = await asyncio.start_server(manejar, "0.0.0.0", 8080, backlog=2048)
    print("latencia escuchando en :8080", flush=True)
    async with servidor:
        await parar.wait()


if __name__ == "__main__":
    asyncio.run(main())
