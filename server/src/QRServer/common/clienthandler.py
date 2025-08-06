import abc
import logging
from asyncio import CancelledError, StreamWriter, StreamReader, IncompleteReadError, LimitOverrunError
from datetime import datetime
from typing import Callable, TypeVar, Type, AsyncIterable, Coroutine

from QRServer.common import messages, utils
from QRServer.common.messages import ResponseMessage, RequestMessage, Message
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbUser

log = logging.getLogger('qr.client_handler')

RMT = TypeVar('RMT', bound=RequestMessage)


class ClientHandler(abc.ABC):
    connected_at: datetime
    config: Config
    connector: DbConnector
    reader: StreamReader
    writer: StreamWriter
    handlers: dict[bytes, list[Callable[[list[bytes]], Coroutine]]]
    message_handlers: dict[Type[RequestMessage], list[Callable[[RequestMessage], Coroutine]]]
    _username: str | None

    def __init__(self, config, connector, reader: StreamReader, writer: StreamWriter):
        self.connected_at = datetime.now()
        self.config = config
        self.connector = connector
        self.handlers = {}
        self.message_handlers = {}
        self.reader = reader
        self.writer = writer
        self._username = None

    @property
    def username(self) -> str:
        return self._username

    async def _socket_read(self) -> AsyncIterable[bytes]:
        while True:
            try:
                data = await self.reader.readuntil(b'\x00')
            except (ConnectionError, CancelledError, IncompleteReadError):
                data = None
            except LimitOverrunError:
                log.exception("Limit overrun error")
                data = None

            if not data:
                log.debug(f'No more data to read from {self.username}, finishing')
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

            message = Message.from_data(data)

            try:
                if message is not None:
                    log.debug(f'Handling: {message} from {self.username}')
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
        log.warning(f'Using deprecated method to send {data!r}')
        log.debug(f'Sending {data!r} to {self.username}')
        self.writer.write(data)
        await self.writer.drain()

    async def send_msg(self, message: ResponseMessage):
        log.debug(f'Sending {message} to {self.username}')
        try:
            self.writer.write(message.to_data())
            await self.writer.drain()
        except ConnectionError:
            raise StopHandlerException()

    async def authenticate_user(self, username, password) -> DbUser | None:
        is_guest = utils.is_guest(username, password)
        auth_disabled = self.config.auth_disable.get()
        auto_register = self.config.auto_register.get()
        db_user = await self.connector.authenticate_user(
            username=username,
            password=None if is_guest or auth_disabled else password.encode('ascii'),
            auto_create=(is_guest or auto_register or auth_disabled),
            verify_password=(not auth_disabled))
        if db_user:
            self._username = username
        return db_user

    def close(self):
        self.writer.close()

    def close_and_stop(self):
        self.close()
        raise StopHandlerException()


class StopHandlerException(Exception):
    pass
