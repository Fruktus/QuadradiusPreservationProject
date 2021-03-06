import logging
import os


def refresh_logger_configuration():
    from QRServer import config

    log_level = logging.DEBUG if config.log_verbose.get() else logging.INFO

    if config.log_long.get():
        log_formatter = logging.Formatter(
            '{asctime} {threadName:10} [{name:24}] {levelname:7} {message}',
            style='{')
    else:
        log_formatter = logging.Formatter(
            '[{asctime}.{msecs:3.0f}] {levelname} {message}',
            style='{',
            datefmt='%H:%M:%S')

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(log_formatter)
    root_logger.handlers = [handler]


def create_data_dir():
    from QRServer import config

    os.makedirs(config.data_dir.get(), exist_ok=True)
