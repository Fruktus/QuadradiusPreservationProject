import argparse
import asyncio
import logging

from QRServer import config_handlers
from QRServer.config import Config
from QRServer.server import QRServer

log = logging.getLogger('main')


async def main():
    config = Config()
    config_handlers.refresh_logger_configuration(config)
    parser = argparse.ArgumentParser()
    config.setup_argparse(parser)
    args = parser.parse_args()
    config.load_from_args(args)

    log.info('Quadradius server starting')

    await QRServer(config).run()

    log.info('Server stopping, bye')


if __name__ == '__main__':
    asyncio.run(main())
