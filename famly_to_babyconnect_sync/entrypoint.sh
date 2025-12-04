#!/usr/bin/env bash
set -euo pipefail

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"
DATA_DIR="${DATA_DIR:-/data}"
LOG_DIR="${LOG_DIR:-${DATA_DIR}/logs}"
FAMLY_PROFILE_DIR="${FAMLY_PROFILE_DIR:-${DATA_DIR}/famly-profile}"
BABYCONNECT_PROFILE_DIR="${BABYCONNECT_PROFILE_DIR:-${DATA_DIR}/babyconnect-profile}"

mkdir -p "${DATA_DIR}" "${LOG_DIR}" "${FAMLY_PROFILE_DIR}" "${BABYCONNECT_PROFILE_DIR}"

exec uvicorn backend.api.main:app --host "${APP_HOST}" --port "${APP_PORT}"
