import asyncio
from asyncio import CancelledError
from logging import Handler
from threading import Lock

from QRServer.discord.webhook import Webhook

_messages_lock = Lock()
_messages_buffer = []


class DiscordWebhookHandler(Handler):
    terminator = '\n'

    def __init__(self, config):
        Handler.__init__(self)
        self.setLevel(config.discord_webhook_logger_level.get())

    def emit(self, record):
        msg = self.format(record)
        with _messages_lock:
            _messages_buffer.append(msg)


def get_daemon_task(config):
    return _flush_messages_periodically(config)


async def _flush_messages_periodically(config):
    webhook = Webhook(config)
    delay_s = config.discord_webhook_logger_flush_delay_s.get()
    try:
        while asyncio.get_event_loop().is_running():
            await asyncio.sleep(delay_s)
            await _flush_messages(webhook)
    except CancelledError:
        # ignore
        pass
    finally:
        # make sure that all messages are flushed
        await _flush_messages(webhook)


async def _flush_messages(webhook):
    global _messages_buffer  # noqa: F824
    with _messages_lock:
        if not _messages_buffer:
            return

        messages = [*_messages_buffer]
        _messages_buffer.clear()

    if messages:
        for data in package_messages(messages, 1800):
            await webhook.invoke_webhook_logger(data)


def package_messages(messages, limit):
    buffer = ''
    for message in messages:
        if buffer and len(buffer) + len(message) + 1 > limit:
            yield buffer
            buffer = ''

        if len(message) + 1 > limit:
            suffix = ' ... [truncated]'
            message = message[0:limit - len(suffix) - 1] + suffix

        buffer += message + '\n'

    if buffer:
        yield buffer
