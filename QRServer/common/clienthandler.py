import abc
import logging
from queue import Queue
from socket import socket
from threading import Thread
from typing import Callable, Optional, Dict, List

log = logging.getLogger('client_handler')


class ClientHandler(abc.ABC):
    cs: Optional[socket]
    in_queue: Queue
    handlers: Dict[bytes, List[Callable[[List[bytes]], None]]]
    username: Optional[str]
    _reader_thread: Thread

    def __init__(self, client_socket: socket):
        self.handlers = {}
        self.cs = client_socket
        self.in_queue = Queue()
        self.username = None

        self._reader_thread = Thread(target=self._socket_reader, daemon=True)
        self._reader_thread.start()

    def get_queue(self):
        return self.in_queue

    def get_socket(self):
        return self.cs

    def _socket_reader(self):
        data = b''
        while self.cs:
            data += self.cs.recv(2048)
            if not data:
                log.debug('No more data to read, finishing')
                self.in_queue.put(b'<DISCONNECTED>')
                break
            elif data[-1] == 0:  # idk why b'\x00' does not work
                data = data.split(b'\x00')[:-1]
                for i in data:
                    self.in_queue.put(i)
                data = b''

    def register_handler(self, prefix: bytes, handler):
        if prefix in self.handlers:
            self.handlers[prefix].append(handler)
        else:
            self.handlers[prefix] = [handler]

    def run(self):
        while self.cs:
            data = self.in_queue.get(block=True)
            values = data.split(b'~')
            log.debug('handling: {}'.format(values))
            prefix = values[0]

            if prefix in self.handlers:
                for handler in self.handlers[prefix]:
                    handler(values)

    def send(self, data: bytes):
        self.cs.send(data)

    def close(self):
        if self.cs:
            try:
                self.cs.shutdown(1)
            except OSError:
                pass
            self.cs.close()
            self.cs = None
