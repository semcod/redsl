FROM python:3.12-slim

WORKDIR /app

# Systemowe zależności
RUN apt-get update && \
    apt-get install -y --no-install-recommends git patch && \
    rm -rf /var/lib/apt/lists/*

# Zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod aplikacji
COPY app/ ./app/
COPY config/ ./config/

# Katalog na wyniki refaktoryzacji
RUN mkdir -p /app/refactor_output /tmp/refactor_memory

ENV PYTHONUNBUFFERED=1
ENV REFACTOR_DRY_RUN=true

# API mode
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
