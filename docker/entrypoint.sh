#!/bin/sh

printf "&myIPAddress=%s&chatPort=%s&gamePort=%s" \
  "${ADDRESS}" "${LOBBY_PORT}" "${GAME_PORT}" > /qr/http/address.txt

(cd /qr/http && python -m http.server 2>&1) | sed -e 's/^/[http] /' &
(cd /qr/server && python -m QRServer -b 0.0.0.0 -p 3000 -q 3001)
