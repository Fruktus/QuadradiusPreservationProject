import argparse
import asyncio
import logging
import signal
from typing import Coroutine

from QRServer import config_handlers
from QRServer.config import Config
from QRServer.db.connector import create_connector
from QRServer.discord import logger as discord_logger
from QRServer.game.gameclient import game_listener
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyclient import lobby_listener
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('main')


class QRServer:
    def __init__(self, config):
        self.config = config
        self.connector = None
        self.loop = asyncio.new_event_loop()
        self.tasks = []

    def run(self):
        self.loop.add_signal_handler(signal.SIGINT, self.stop_sync)
        self.loop.add_signal_handler(signal.SIGTERM, self.stop_sync)
        try:
            self.loop.run_until_complete(self.setup_connector())
            self.start_tasks()
            self.loop.run_forever()
        finally:
            self.loop.close()

    async def setup_connector(self):
        self.connector = await create_connector(self.config)

    def start_tasks(self):
        self.start_task("Discord Logger", discord_logger.get_daemon_task(self.config))
        game_server = GameServer(self.config, self.connector)
        lobby_server = LobbyServer()
        self.start_task("Game Listener", game_listener(self.config, self.connector, game_server))
        self.start_task("Lobby Listener", lobby_listener(self.config, self.connector, lobby_server))

    def start_task(self, name: str, task: Coroutine):
        self.tasks.append(self.loop.create_task(task, name=name))

    async def stop(self):
        log.info('Terminating...')
        # stop in reversed order
        for task in reversed(self.tasks):
            log.debug(f'Canceling task "{task.get_name()}"...')
            task.cancel()
            await task
        await self.connector.close()
        self.loop.stop()

    def stop_sync(self):
        self.loop.create_task(self.stop())


def main():
    config = Config()
    config_handlers.refresh_logger_configuration(config)
    parser = argparse.ArgumentParser()
    config.setup_argparse(parser)
    args = parser.parse_args()
    config.load_from_args(args)

    log.info('Quadradius server starting')

    QRServer(config).run()

    log.info('Server stopping, bye')


if __name__ == '__main__':
    main()
