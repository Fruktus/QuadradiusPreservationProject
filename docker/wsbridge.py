#!/usr/bin/env python3
"""
Minimal websockify replacement: WebSocket -> TCP, optionally with a PROXY v1 header.

usage: wsbridge.py [-h] [--proxy-protocol] [--name NAME] LISTEN_PORT HOST:PORT

  LISTEN_PORT        port to listen on (binds 127.0.0.1 only)
  HOST:PORT          TCP target to forward to
  --proxy-protocol   send a PROXY v1 line first, using X-Real-IP / X-Real-Port
                     from the WebSocket upgrade request
  --name NAME        log prefix, e.g. "lobby" -> "[wsbridge lobby]"
"""
import argparse
import asyncio
import ipaddress
import logging

from aiohttp import web, WSMsgType

log = logging.getLogger('wsbridge')


def proxy_header(src_ip, src_port, dst_ip, dst_port):
    try:
        src = ipaddress.ip_address(src_ip)
    except ValueError:
        return b'PROXY UNKNOWN\r\n'

    if src.version == 6 and src.ipv4_mapped:
        src = src.ipv4_mapped
        src_ip = str(src)

    dst = ipaddress.ip_address(dst_ip)

    if src.version != dst.version:
        dst_ip = f'::ffff:{dst_ip}' if src.version == 6 else '127.0.0.1'

    proto = 'TCP4' if src.version == 4 else 'TCP6'

    return f'PROXY {proto} {src_ip} {dst_ip} {src_port} {dst_port}\r\n'.encode()


def parse_port(value) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return 0
    return port if 0 <= port <= 65535 else 0


async def handle(request: web.Request) -> web.StreamResponse:
    host, port, use_pp = request.app['target']
    ip = request.headers.get('X-Real-IP') or request.remote or '0.0.0.0'
    src_port = parse_port(request.headers.get('X-Real-Port'))

    ws = web.WebSocketResponse(protocols=('binary',))
    await ws.prepare(request)

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except OSError as e:
        log.warning('[%s]:%s -> [%s]:%s connect failed: %s', ip, src_port, host, port, e)
        await ws.close(code=1011)
        return ws

    log.debug('[%s]:%s connected', ip, src_port)

    async def tcp_to_ws():
        try:
            while data := await reader.read(65536):
                await ws.send_bytes(data)
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            await ws.close()

    pump = None
    try:
        if use_pp:
            dst_ip, dst_port = writer.get_extra_info('peername')[:2]
            writer.write(proxy_header(ip, src_port, dst_ip, dst_port))

        pump = asyncio.create_task(tcp_to_ws())

        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                writer.write(msg.data)
            elif msg.type == WSMsgType.TEXT:
                writer.write(msg.data.encode())
            else:
                break
            await writer.drain()
    except ConnectionError:
        pass
    finally:
        if pump:
            pump.cancel()
        writer.close()
        log.debug('[%s]:%s disconnected', ip, src_port)
    return ws


def main():
    ap = argparse.ArgumentParser(description='WebSocket -> TCP bridge')
    ap.add_argument('listen_port', type=int)
    ap.add_argument('target', metavar='HOST:PORT')
    ap.add_argument('--proxy-protocol', action='store_true',
                    help='prefix the TCP stream with a PROXY v1 header')
    ap.add_argument('--name', default='bridge', help='log prefix')
    args = ap.parse_args()

    host, _, port = args.target.rpartition(':')
    if not host or not port.isdigit():
        ap.error('target must be HOST:PORT')

    prefix = f'[wsbridge {args.name}]'.replace('%', '%%')
    logging.basicConfig(
        level=logging.INFO,
        format=f'{prefix} %(asctime)s %(levelname)s: %(message)s',
    )

    app = web.Application()
    app['target'] = (host, int(port), args.proxy_protocol)
    app.router.add_get('/{tail:.*}', handle)

    log.info('Listening on 127.0.0.1:%d -> %s:%d (proxy protocol: %s)',
             args.listen_port, host, int(port), 'on' if args.proxy_protocol else 'off')

    web.run_app(app, host='127.0.0.1', port=args.listen_port, print=None, access_log=None)


if __name__ == '__main__':
    main()
