import abc
import asyncio
import logging
from asyncio import CancelledError
from queue import Queue
from socket import socket
from threading import Thread
from typing import Callable, Optional, Dict, List, TypeVar, Type, AsyncIterable, Coroutine

from QRServer.common import messages
from QRServer.common.messages import ResponseMessage, RequestMessage

log = logging.getLogger('qr.client_handler')

RMT = TypeVar('RMT', bound=RequestMessage)


class ClientHandler(abc.ABC):
    cs: Optional[socket]
    in_queue: Queue
    handlers: Dict[bytes, List[Callable[[List[bytes]], Coroutine]]]
    message_handlers: Dict[Type[RequestMessage], List[Callable[[RequestMessage], Coroutine]]]
    username: Optional[str]
    _reader_thread: Thread

    def __init__(self, client_socket: socket):
        self.handlers = {}
        self.message_handlers = {}
        self.cs = client_socket
        self.in_queue = Queue()
        self.username = None

    async def _socket_read(self) -> AsyncIterable[bytes]:
        loop = asyncio.get_event_loop()
        while self.cs:
            try:
                data = await loop.sock_recv(self.cs, 2048)
            except (ConnectionResetError, CancelledError):
                data = None

            if not data:
                log.debug('No more data to read, finishing')
                yield b'<DISCONNECTED>'
                return
            elif data[-1] == 0:
                data = data.split(b'\x00')[:-1]
                for i in data:
                    yield i

    def register_handler(self, prefix: bytes, handler):
        """Deprecated, do not use"""
        if prefix in self.handlers:
            self.handlers[prefix].append(handler)
        else:
            self.handlers[prefix] = [handler]

    def register_message_handler(self, mtype: Type[RMT], handler: Callable[[RMT], Coroutine]):
        if mtype in self.message_handlers:
            self.message_handlers[mtype].append(handler)
        else:
            self.message_handlers[mtype] = [handler]

    async def run(self):
        async for data in self._socket_read():
            values = data.split(messages.delim.encode('ascii'))
            prefix = values[0]

            message = RequestMessage.from_data(data)

            try:
                if message is not None:
                    log.debug(f'Handling: {message}')
                    mtype = type(message)
                    if mtype in self.message_handlers:
                        for handler in self.message_handlers[mtype]:
                            await handler(message)
                    else:
                        log.error(f'No handler for message type {mtype}')
                elif prefix in self.handlers:
                    log.warning(f'Deprecated handling: {values}')
                    for handler in self.handlers[prefix]:
                        await handler(values)
                else:
                    if self.username:
                        log.debug(f'Unhandled message received: {data}')
            except StopHandlerException:
                log.debug('Stopping handler')
                return
            except Exception:
                log.exception(f'Error when processing message: {message}')
                return

    async def send(self, data: bytes):
        """Deprecated, do not use"""
        loop = asyncio.get_event_loop()
        log.warning(f'Using deprecated method to send {data}')
        log.debug(f'Sending {data} to {self.username}')
        await loop.sock_sendall(self.cs, data)

    async def send_msg(self, message: ResponseMessage):
        loop = asyncio.get_event_loop()
        log.debug(f'Sending {message} to {self.username}')
        try:
            await loop.sock_sendall(self.cs, message.to_data())
        except BrokenPipeError:
            raise StopHandlerException()

    def close(self):
        if self.cs:
            try:
                self.cs.shutdown(1)
            except OSError:
                pass
            self.cs.close()
            self.cs = None
        raise StopHandlerException()


class StopHandlerException(Exception):
    pass
