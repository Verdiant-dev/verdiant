FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App-Code
COPY app /app/app

# Alembic-Konfiguration und Migrationen
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
