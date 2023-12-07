#!/bin/bash
set -e

HOST="127.0.0.1"

ruffle \
  --power low \
  --no-gui \
  --socket-allow "${HOST}:3000" \
  --socket-allow "${HOST}:3001" \
  "http://${HOST}:8000/quadradius_lobby.swf"
