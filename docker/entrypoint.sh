#!/bin/sh
set -e

(websockify 8100 127.0.0.1:3000 2>&1) | awk -W interactive '{print "[websockify lobby] " $0}' >&2 &
(websockify 8101 127.0.0.1:3001 2>&1) | awk -W interactive '{print "[websockify game] " $0}' >&2 &
(nginx -g 'daemon off;' 2>&1) | awk -W interactive '{print "[nginx] " $0}' >&2 &
python -m QRServer -c /config.toml "$@"
