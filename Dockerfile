# Supply an approved immutable image digest for production builds.
ARG PYTHON_IMAGE=python:3.12.13-slim-bookworm
FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src \
    CASSANDRE_CC_STORE_PATH=/data/store_snapshot.json
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock \
    && groupadd --gid 10001 cassandre \
    && useradd --uid 10001 --gid 10001 --no-create-home cassandre \
    && mkdir /data && chown 10001:10001 /data
COPY src /app/src
COPY scripts /app/scripts
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"
# Never raise workers above one with this snapshot implementation.
CMD ["python", "-m", "uvicorn", "cassandre_cc.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
