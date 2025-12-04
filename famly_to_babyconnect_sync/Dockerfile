ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:latest
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    HEADLESS=true \
    DB_PATH=/data/db.sqlite \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    VIRTUAL_ENV=/opt/famly-sync-venv

ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /app

# Install runtime dependencies and Playwright browsers
RUN apk add --no-cache \
        python3 \
        py3-pip \
        py3-setuptools \
        py3-wheel \
        py3-virtualenv \
        build-base \
        bash \
        wget \
        curl \
        ca-certificates \
        libstdc++ \
        nss \
        mesa-gles \
        fontconfig \
        ttf-dejavu

COPY requirements.txt .
RUN python3 -m venv "${VIRTUAL_ENV}" \
    && . "${VIRTUAL_ENV}/bin/activate" \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY backend ./backend
COPY frontend/dist ./frontend/dist
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
