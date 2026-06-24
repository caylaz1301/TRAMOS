FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=9999

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY knowledge_base ./knowledge_base
COPY main.py .
COPY init_db.py .
COPY deploy/backend-entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 9999

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9999/health', timeout=5).read()"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-9999} --workers ${UVICORN_WORKERS:-1}"]
