# syntax=docker/dockerfile:1.7
# Digest = index multi-arsitektur (amd64+arm64) dari registry; perbarui lewat Dependabot/PR, jangan menebak.
ARG PYTHON_IMAGE=python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# ---- base: venv di /opt/venv (di luar bind mount -> tidak bentrok dengan host) ----
FROM ${PYTHON_IMAGE} AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv PATH=/opt/venv/bin:$PATH
RUN python -m venv /opt/venv
WORKDIR /app
COPY requirements.txt requirements-dev.txt constraints.txt ./

# ---- dev: dependensi dev + non-root + hot reload ----
FROM base AS dev
RUN pip install -r requirements-dev.txt -c constraints.txt
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} app && useradd -m -u ${UID} -g ${GID} app \
    && apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data/media && chown app:app /data/media
COPY --chown=app:app docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
USER app
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--no-access-log"]

# ---- prod: hanya dependensi runtime, tanpa reload ----
FROM base AS prod
RUN pip install -r requirements.txt -c constraints.txt
# apt-get upgrade: menarik patch keamanan Debian yang belum ada di base image yang di-pin (mis. zlib1g, ditemukan Trivy).
RUN groupadd -g 1000 app && useradd -m -u 1000 -g 1000 app \
    && apt-get update && apt-get -y --no-install-recommends upgrade \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data/media && chown app:app /data/media
COPY --chown=app:app . .
COPY --chown=app:app docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
USER app
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
