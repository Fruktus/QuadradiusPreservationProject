#!/bin/sh
set -e
HTTP_PORT=8000

(cd /qr/http && \
  echo "Starting HTTP server on port ${HTTP_PORT}" && \
  python -m http.server "${HTTP_PORT}" 2>&1) | awk -W interactive '{print "[http] " $0}' >&2 &
(websockify 8100 127.0.0.1:3000 2>&1) | awk -W interactive '{print "[websockify lobby] " $0}' >&2 &
(websockify 8101 127.0.0.1:3001 2>&1) | awk -W interactive '{print "[websockify game] " $0}' >&2 &
(cd /qr/server && python -m QRServer -c /config.toml "$@")
