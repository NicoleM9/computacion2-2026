
#!/usr/bin/env python3
"""Fork + exec para ejecutar ls."""

import os

print(f"Padre (PID {os.getpid()}): voy a ejecutar 'ls -la /tmp'")

pid = os.fork()

if pid == 0:

    # HIJO
    print(f"Hijo (PID {os.getpid()}): haciendo exec...")

    os.execlp("ls", "ls", "-la", "/tmp")

    # Solo llega aquí si exec falla
    print("ERROR: exec falló")

    os._exit(1)

else:

    # PADRE
    _, status = os.wait()

    codigo = os.WEXITSTATUS(status)

    print(f"\nPadre: ls terminó con código {codigo}")