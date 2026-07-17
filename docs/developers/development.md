# Development

Hay dos formas de levantar el entorno local:

- **Opción A — Todo en Docker** (`docker-compose-full.yml`): la más simple, todos los servicios corren en contenedores.
- **Opción B — Infra en Docker, app en crudo**: Elasticsearch, PostgreSQL, Redis y MinIO corren en Docker; la app Django y los workers corren en un virtualenv local. Útil para desarrollo activo con hot-reload.

## Requerimientos

- Docker y Docker Compose (ambas opciones)
- Python 3.6 y virtualenv (solo Opción B)

---

## Opción A — Todo en Docker

### 1. Configurar el entorno

```bash
cp conf/settings/.env.example_prod conf/settings/.env
```

Editar `conf/settings/.env` y completar los valores reales:

- `DATABASE_PASSWORD` — contraseña de PostgreSQL
- `SECRET_KEY` y `DJANGO_SECRET_KEY` — claves secretas de Django
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` — credenciales de MinIO
- `STATIC_ROOT=/app/staticfiles`
- `MEDIA_ROOT=/app/media`
- `DJANGO_SETTINGS_MODULE=conf.settings.local`

### 2. Construir la imagen

```bash
docker compose -f docker-compose-full.yml build
```

La primera vez tarda algunos minutos porque instala dependencias (incluyendo `django-datajsonar` desde el repo).

### 3. Levantar infraestructura

```bash
docker compose -f docker-compose-full.yml up -d postgres redis elasticsearch minio
```

Esperar ~30 segundos a que Elasticsearch inicialice. Se puede verificar con:

```bash
docker compose -f docker-compose-full.yml logs elasticsearch | tail -20
```

### 4. Levantar la app

```bash
docker compose -f docker-compose-full.yml up -d app nginx
```

El entrypoint corre `migrate` y `collectstatic` automáticamente. La app queda disponible en `http://localhost` y el admin en `http://localhost/admin`.

### 5. Crear superusuario

```bash
docker compose -f docker-compose-full.yml exec app python manage.py createsuperuser
```

### 6. Levantar workers (para tareas asíncronas)

```bash
docker compose -f docker-compose-full.yml up -d worker-indexing worker-api-index worker-misc
```

Los workers disponibles y las colas que escuchan:

| Worker | Colas |
|---|---|
| `worker-indexing` | `indexing`, `dj_indexing` |
| `worker-api-index` | `api_index`, `collection_index` |
| `worker-misc` | `meta_indexing`, `upkeep`, `default` |

### Operaciones habituales

```bash
# Logs en tiempo real
docker compose -f docker-compose-full.yml logs -f app

# Rebuild después de cambios en el código
docker compose -f docker-compose-full.yml build app
docker compose -f docker-compose-full.yml up -d app worker-indexing worker-api-index worker-misc

# Correr un management command
docker compose -f docker-compose-full.yml exec app python manage.py <comando>

# Shell Django
docker compose -f docker-compose-full.yml exec app python manage.py shell

# Bajar todo sin borrar datos
docker compose -f docker-compose-full.yml down

# Bajar y borrar volúmenes (borra todos los datos)
docker compose -f docker-compose-full.yml down -v
```

---

## Opción B — Infra en Docker, app en crudo

### 1. Levantar servicios de infraestructura

```bash
docker compose up -d
```

Esto levanta PostgreSQL (5432), Elasticsearch (9200), Redis (6379) y MinIO (9000) en puertos locales usando `docker-compose.yml`.

### 2. Crear virtualenv e instalar dependencias

```bash
pyenv virtualenv 3.6.6 stiempo-api
pyenv activate stiempo-api
pip install -r requirements/local.txt
```

### 3. Configuración

```bash
cp conf/settings/local_example.py conf/settings/local.py
export DJANGO_SETTINGS_MODULE=conf.settings.local
```

Ajustar `conf/settings/local.py` si algún host o puerto difiere del default.

### 4. Migraciones

```bash
python manage.py migrate
```

### 5. Web server

```bash
python manage.py runserver
```

La app queda disponible en `http://127.0.0.1:8000`.

### Workers opcionales

Por defecto en `local.py` las colas tienen `ASYNC=False`, por lo que las tareas corren sincrónicas sin necesidad de workers. Para testear el flujo asíncrono completo, cambiar en `local.py`:

```python
for queue in RQ_QUEUES.values():
    queue['ASYNC'] = True
```

Y levantar workers en terminales separadas:

```bash
python manage.py rqworker indexing dj_indexing
python manage.py rqworker api_index collection_index
python manage.py rqworker meta_indexing upkeep default
```

---

## Tests

```bash
scripts/tests.sh
```

También hay scripts para estilos (`scripts/pycodestyle.sh`) y pylint (`scripts/pylint.sh`).
