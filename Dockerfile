FROM python:3.6-alpine

ENV ADDRESS="127.0.0.1"
ENV LOBBY_PORT="3000"
ENV GAME_PORT="3001"

RUN mkdir -p /data && \
    mkdir -p /qr/http && \
    mkdir -p /qr/server/QRServer && \
    wget classic.quadradius.com/quadradius_game.swf -O /qr/http/quadradius_game.swf && \
    wget classic.quadradius.com/quadradius_lobby.swf -O /qr/http/quadradius_lobby.swf && \
    echo "251175fb815f5f2229e4560a9963d2136a04fd084700a56da78353310c6edac7  /qr/http/quadradius_game.swf" | sha256sum -c && \
    echo "33253685acc0cb63c36b60aba2e11b910eff722ad9d29618d34c04bfb5f8838d  /qr/http/quadradius_lobby.swf" | sha256sum -c

COPY requirements.txt /
RUN python -m pip install -r requirements.txt && \
    rm requirements.txt

COPY docker /
COPY QRServer /qr/server/QRServer

EXPOSE 8000
EXPOSE 3000
EXPOSE 3001

ENTRYPOINT ["/entrypoint.sh"]
