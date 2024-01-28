import asyncio
import logging
import socket
from asyncio import CancelledError

log = logging.getLogger('listener')


async def listen_for_connections(conn_host, conn_port, handler, name):
    log.info(f'{name} starting on {conn_host}:{conn_port}')
    clients = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((conn_host, conn_port))
        server.listen(5)
        server.setblocking(False)
        log.info(f'{name} started on {conn_host}:{conn_port}')

        loop = asyncio.get_event_loop()
        try:
            while True:
                client_socket, _ = await loop.sock_accept(server)
                clients.append(loop.create_task(handler(client_socket)))
        except (KeyboardInterrupt, CancelledError):
            for client in clients:
                client.cancel()
            server.shutdown(1)
            server.close()
    await asyncio.gather(*clients)
