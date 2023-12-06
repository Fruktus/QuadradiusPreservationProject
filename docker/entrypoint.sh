#!/bin/sh
set -e

printf "&myIPAddress=%s&chatPort=%s&gamePort=%s" \
  "${ADDRESS}" "${LOBBY_PORT}" "${GAME_PORT}" > /qr/http/address.txt

(cd /qr/http && \
  echo "Starting HTTP server at http://${ADDRESS}:${HTTP_PORT}/" && \
  python -m http.server "${HTTP_PORT}" 2>&1) | awk '{print "[http] " $0}' >&2 &
(cd /qr/server && python -m QRServer -c /config.toml "$@")
