import abc
import logging
from queue import Queue
from socket import socket
from threading import Thread
from typing import Callable, Optional, Dict, List, TypeVar, Type

from QRServer.common import messages
from QRServer.common.messages import ResponseMessage, RequestMessage

log = logging.getLogger('client_handler')

RMT = TypeVar('RMT', bound=RequestMessage)


class ClientHandler(abc.ABC):
    cs: Optional[socket]
    in_queue: Queue
    handlers: Dict[bytes, List[Callable[[List[bytes]], None]]]
    message_handlers: Dict[Type[RequestMessage], List[Callable[[RequestMessage], None]]]
    username: Optional[str]
    _reader_thread: Thread

    def __init__(self, client_socket: socket):
        self.handlers = {}
        self.message_handlers = {}
        self.cs = client_socket
        self.in_queue = Queue()
        self.username = None

        self._reader_thread = Thread(target=self._socket_reader, daemon=True)
        self._reader_thread.start()

    def _socket_reader(self):
        while self.cs:
            try:
                data = self.cs.recv(2048)
            except ConnectionResetError:
                data = None

            if not data:
                log.debug('No more data to read, finishing')
                self.in_queue.put(b'<DISCONNECTED>')
                break
            elif data[-1] == 0:
                data = data.split(b'\x00')[:-1]
                for i in data:
                    self.in_queue.put(i)

    def register_handler(self, prefix: bytes, handler):
        """Deprecated, do not use"""
        if prefix in self.handlers:
            self.handlers[prefix].append(handler)
        else:
            self.handlers[prefix] = [handler]

    def register_message_handler(self, mtype: Type[RMT], handler: Callable[[RMT], None]):
        if mtype in self.message_handlers:
            self.message_handlers[mtype].append(handler)
        else:
            self.message_handlers[mtype] = [handler]

    def run(self):
        while self.cs:
            data = self.in_queue.get(block=True)
            values = data.split(messages.delim.encode('ascii'))
            prefix = values[0]

            message = RequestMessage.from_data(data)

            try:
                if message is not None:
                    log.debug('Handling: {}'.format(message))
                    mtype = type(message)
                    if mtype in self.message_handlers:
                        for handler in self.message_handlers[mtype]:
                            handler(message)
                    else:
                        log.error('No handler for message type {}'.format(mtype))
                elif prefix in self.handlers:
                    log.warning('Deprecated handling: {}'.format(values))
                    for handler in self.handlers[prefix]:
                        handler(values)
                else:
                    log.debug('Unhandled message received: {}'.format(str(data)))
            except StopHandlerException:
                return

    def send(self, data: bytes):
        """Deprecated, do not use"""
        log.warning('Using deprecated method to send {}'.format(data))
        log.debug('Sending {} to {}'.format(data, self.username))
        self.cs.send(data)

    def send_msg(self, message: ResponseMessage):
        log.debug('Sending {} to {}'.format(message, self.username))
        try:
            self.cs.send(message.to_data())
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
