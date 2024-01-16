FROM python:3.9 as server-builder

COPY server /server
WORKDIR /server
RUN pip install '.[dev]' && python setup.py bdist_wheel

FROM python:3.9
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /data && \
    mkdir -p /qr/http && \
    # install nginx
    apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/* && \
    # install SWFs
    wget https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_game.swf -O /qr/http/quadradius_game.swf && \
    wget https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_lobby.swf -O /qr/http/quadradius_lobby.swf && \
    echo "251175fb815f5f2229e4560a9963d2136a04fd084700a56da78353310c6edac7  /qr/http/quadradius_game.swf" | sha256sum -c && \
    echo "33253685acc0cb63c36b60aba2e11b910eff722ad9d29618d34c04bfb5f8838d  /qr/http/quadradius_lobby.swf" | sha256sum -c && \
    # install websockify
    pip install websockify

COPY docker /
COPY --from=server-builder /server/dist/QRServer-*.whl /qr/server/
RUN pip install /qr/server/*.whl

EXPOSE 8000
EXPOSE 3000
EXPOSE 3001

ENTRYPOINT ["/entrypoint.sh"]
