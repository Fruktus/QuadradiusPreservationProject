import abc
import logging
from asyncio import CancelledError, StreamWriter, StreamReader, IncompleteReadError
from typing import Callable, Dict, List, TypeVar, Type, AsyncIterable, Coroutine

from QRServer.common import messages
from QRServer.common.messages import ResponseMessage, RequestMessage

log = logging.getLogger('qr.client_handler')

RMT = TypeVar('RMT', bound=RequestMessage)


class ClientHandler(abc.ABC):
    reader: StreamReader
    writer: StreamWriter
    handlers: Dict[bytes, List[Callable[[List[bytes]], Coroutine]]]
    message_handlers: Dict[Type[RequestMessage], List[Callable[[RequestMessage], Coroutine]]]

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.handlers = {}
        self.message_handlers = {}
        self.reader = reader
        self.writer = writer

    @property
    @abc.abstractmethod
    def username(self) -> str:
        ...

    async def _socket_read(self) -> AsyncIterable[bytes]:
        while True:
            try:
                data = await self.reader.readuntil(b'\x00')
            except (ConnectionResetError, CancelledError, IncompleteReadError):
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
        try:
            await self._run()
        finally:
            self.writer.close()

    async def _run(self):
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
        log.warning(f'Using deprecated method to send {data}')
        log.debug(f'Sending {data} to {self.username}')
        self.writer.write(data)
        await self.writer.drain()

    async def send_msg(self, message: ResponseMessage):
        log.debug(f'Sending {message} to {self.username}')
        try:
            self.writer.write(message.to_data())
            await self.writer.drain()
        except ConnectionResetError:
            raise StopHandlerException()

    def close(self):
        self.writer.close()
        raise StopHandlerException()


class StopHandlerException(Exception):
    pass
