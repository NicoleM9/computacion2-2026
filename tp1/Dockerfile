FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y forzar buffer directo en stdio
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Requerido por curses para manejar colores y dimensiones de terminal
ENV TERM=xterm-256color

WORKDIR /app

# Copiar el código fuente
COPY . /app

# Comando de ejecución principal
CMD ["python3", "src/main.py"]