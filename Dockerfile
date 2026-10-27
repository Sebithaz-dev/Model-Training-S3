FROM python:3.11-slim

ARG GIT_SHA=local
LABEL org.opencontainers.image.source="https://github.com/Sebithaz-dev/Model-Training-S3" \
      org.opencontainers.image.description="Job de entrenamiento del clasificador Citi Bike" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ml ./ml
COPY config ./config
COPY scripts ./scripts

# Usuario sin privilegios: el job no necesita root
RUN useradd --create-home --uid 10001 trainer \
    && mkdir -p data ml/artefactos \
    && chown -R trainer:trainer /app
USER 10001

CMD ["python", "-m", "scripts.run_pipeline"]
