ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:latest
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    HEADLESS=true \
    DB_PATH=/data/db.sqlite \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install runtime dependencies and Playwright browsers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        python3-setuptools \
        python3-wheel \
        build-essential \
        wget \
        curl \
        ca-certificates \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY backend ./backend
COPY frontend/dist ./frontend/dist
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
