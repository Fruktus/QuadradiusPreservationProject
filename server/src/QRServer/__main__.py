import argparse
import asyncio
import logging
import signal
from typing import Coroutine

from QRServer import config, config_handlers
from QRServer.discord import logger as discord_logger
from QRServer.game.gameclient import game_listener
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyclient import lobby_listener
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('main')


class QRServer:
    def __init__(self, address, game_port, lobby_port):
        self.address = address
        self.game_port = game_port
        self.lobby_port = lobby_port
        self.loop = asyncio.new_event_loop()
        self.tasks = []

    def run(self):
        self.loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.stop()))
        self.loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.stop()))
        try:
            self.start_tasks()
            self.loop.run_forever()
        finally:
            self.loop.close()

    def start_tasks(self):
        self.start_task("Discord Logger", discord_logger.get_daemon_task())
        self.start_task("Game Listener", game_listener(self.address, self.game_port, GameServer()))
        self.start_task("Lobby Listener", lobby_listener(self.address, self.lobby_port, LobbyServer()))

    def start_task(self, name: str, task: Coroutine):
        self.tasks.append(self.loop.create_task(task, name=name))

    async def stop(self):
        log.info('Terminating...')
        # stop in reversed order
        for task in reversed(self.tasks):
            log.debug(f'Canceling task "{task.get_name()}"...')
            task.cancel()
            await task
        self.loop.stop()

    def stop_sync(self):
        self.loop.create_task(self.stop())


def main():
    config_handlers.refresh_logger_configuration()
    parser = argparse.ArgumentParser()
    config.setup_argparse(parser)
    args = parser.parse_args()
    config.load_from_args(args)

    log.info('Quadradius server starting')

    address = config.address.get()
    game_port = config.game_port.get()
    lobby_port = config.lobby_port.get()

    QRServer(address, game_port, lobby_port).run()

    log.info('Server stopping, bye')


if __name__ == '__main__':
    main()
