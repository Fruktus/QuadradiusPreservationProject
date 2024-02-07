import unittest
from tempfile import TemporaryDirectory
from typing import Optional

from QRServer.__main__ import QRServer
from QRServer.config import Config


class QuadradiusIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    _data_dir: Optional[TemporaryDirectory]
    _config: Optional[Config]
    _server: Optional[QRServer]

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)
        self._server = None

    @property
    def server(self) -> QRServer:
        return self._server

    @property
    def config(self) -> Config:
        return self._config

    async def itSetUpConfig(self, config):
        pass

    async def itSetUp(self):
        pass

    async def itTearDown(self):
        pass

    async def asyncSetUp(self):
        self._data_dir = TemporaryDirectory()

        config = Config()
        config.set('address', '127.0.0.1')
        config.set('port.lobby', 0)
        config.set('port.game', 0)
        config.set('data.dir', self._data_dir.name)
        await self.itSetUpConfig(config)
        self._config = config
        self._server = QRServer(config)
        await self._server.start()
        await self.itSetUp()

    async def asyncTearDown(self):
        try:
            await self.itTearDown()
        finally:
            await self._server.stop()
            self._data_dir.cleanup()
