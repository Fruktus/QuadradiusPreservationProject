#!/bin/sh
set -e

BRIDGE_ARGS=""
SERVER_ARGS=""
if [ "${QR_PROXY_PROTOCOL:-0}" = "1" ]; then
    BRIDGE_ARGS="--proxy-protocol"
    SERVER_ARGS="--use-proxy-protocol"
fi

python /wsbridge.py 8100 127.0.0.1:3000 --name lobby $BRIDGE_ARGS &
python /wsbridge.py 8101 127.0.0.1:3001 --name game $BRIDGE_ARGS &
(nginx -g 'daemon off;' 2>&1) | awk '{print "[nginx] " $0; fflush()}' >&2 &
python -m QRServer -c /config.toml $SERVER_ARGS "$@"
