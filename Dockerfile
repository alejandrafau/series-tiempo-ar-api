FROM python:3.6-slim

RUN apt-get update && apt-get install -y \
        git \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias primero para aprovechar cache de capas
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir -r requirements/production.txt

# Código
COPY . .

# Directorios de trabajo y docker.env vacío para que django-environ no falle
# (las vars reales vienen por env_file en docker-compose)
RUN mkdir -p staticfiles media logs \
    && touch conf/settings/docker.env

EXPOSE 8000