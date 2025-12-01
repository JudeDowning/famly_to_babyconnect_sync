# Base image with Python and Playwright browsers
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend ./backend

# Copy frontend build artefacts (assumes `npm run build` has been run)
COPY frontend/dist ./frontend/dist

# Expose app port
EXPOSE 8000

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV HEADLESS=true
ENV DB_PATH=/data/db.sqlite

# Ensure /data exists for DB and browser profiles
RUN mkdir -p /data

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
