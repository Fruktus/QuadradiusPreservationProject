FROM python:3.9

ARG WEBSOCKIFY_VERSION="0.11.0"

RUN mkdir -p /data && \
    mkdir -p /qr/http && \
    mkdir -p /qr/websockify && \
    mkdir -p /qr/server/QRServer && \
    # install SWFs
    wget https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_game.swf -O /qr/http/quadradius_game.swf && \
    wget https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_lobby.swf -O /qr/http/quadradius_lobby.swf && \
    echo "251175fb815f5f2229e4560a9963d2136a04fd084700a56da78353310c6edac7  /qr/http/quadradius_game.swf" | sha256sum -c && \
    echo "33253685acc0cb63c36b60aba2e11b910eff722ad9d29618d34c04bfb5f8838d  /qr/http/quadradius_lobby.swf" | sha256sum -c && \
    # install websockify
    wget https://github.com/novnc/websockify/archive/refs/tags/v${WEBSOCKIFY_VERSION}.zip -O /tmp/websockify.zip && \
    unzip /tmp/websockify.zip -d /qr/websockify && \
    rm -f /tmp/websockify.zip && \
    (cd /qr/websockify/websockify-${WEBSOCKIFY_VERSION}/ && python3 setup.py install)


COPY docker /
COPY server/QRServer /qr/server/QRServer
COPY server/requirements.txt /qr/server/
RUN python -m pip install -r /qr/server/requirements.txt

EXPOSE 8000
EXPOSE 3000
EXPOSE 3001
EXPOSE 8100
EXPOSE 8101

ENTRYPOINT ["/entrypoint.sh"]
