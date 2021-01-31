FROM python:3.9-alpine

ENV ADDRESS="127.0.0.1"
ENV LOBBY_PORT="3000"
ENV GAME_PORT="3001"

RUN mkdir -p /qr/http && \
    mkdir -p /qr/server/QRServer && \
    wget classic.quadradius.com/quadradius_game.swf -O /qr/http/quadradius_game.swf && \
    wget classic.quadradius.com/quadradius_lobby.swf -O /qr/http/quadradius_lobby.swf

COPY docker /
COPY QRServer /qr/server/QRServer

EXPOSE 8000
EXPOSE 3000
EXPOSE 3001

ENTRYPOINT ["/entrypoint.sh"]
