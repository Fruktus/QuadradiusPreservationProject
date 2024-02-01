import argparse
import asyncio
import logging
import signal
import sys
from threading import Thread
from typing import Coroutine

from QRServer import config, config_handlers
from QRServer.discord import logger as discord_logger
from QRServer.cli import QRCmd
from QRServer.game.gameclient import game_listener
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyclient import lobby_listener
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('main')


def handle_exit(sig, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, handle_exit)


class ServerThread(Thread):
    def __init__(self, address, game_port, lobby_port):
        Thread.__init__(self, daemon=True)
        self.address = address
        self.game_port = game_port
        self.lobby_port = lobby_port
        self.loop = asyncio.new_event_loop()
        self.tasks = []

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_listeners())

    async def start_listeners(self):
        discord_task = asyncio.create_task(discord_logger.get_daemon_task())
        self.tasks.append(discord_task)

        game_task = asyncio.create_task(game_listener(self.address, self.game_port, GameServer()))
        lobby_task = asyncio.create_task(lobby_listener(self.address, self.lobby_port, LobbyServer()))
        self.tasks.append(game_task)
        self.tasks.append(lobby_task)
        await asyncio.gather(*self.tasks)

    def stop(self):
        async def _stop_loop():
            # stop in reversed order
            for task in reversed(self.tasks):
                task.cancel()
                await task

        self.run_within_event_loop(_stop_loop())
        self.loop.close()

    def run_within_event_loop(self, coro: Coroutine):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()


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

    server_thread = ServerThread(address, game_port, lobby_port)
    server_thread.start()
    # since now, we should be aware that the event loop
    # is running in the background, accessing any shared data
    # is not safe without run_within_event_loop

    try:
        if sys.stdout.isatty():
            cmd = QRCmd(server_thread)
            cmd.cmdloop_with_interrupt()
        else:
            # this will wait forever
            server_thread.join()
    except (KeyboardInterrupt, EOFError):
        log.info('Terminating...')
        server_thread.stop()
        server_thread.join()

    log.info('Server stopping, bye')


if __name__ == '__main__':
    main()
