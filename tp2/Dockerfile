FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Formato exec: Python es PID 1 y recibe SIGTERM directamente.
CMD ["python", "-m", "app.main"]
