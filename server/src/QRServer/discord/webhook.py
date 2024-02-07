import logging

import aiohttp

from QRServer.common.classes import GameResultHistory

log = logging.getLogger('qr.webhook')


def webhook(webhook_name, disable_log=False):
    def webhook_debug(message):
        if not disable_log:
            log.debug(message)

    def decorator(f):
        async def webhook_wrapper(*args, **kwargs):
            config = args[0].config
            webhook_url = config.get(f'discord.webhook.{webhook_name}.url')

            try:
                if webhook_url:
                    webhook_debug(f'Invoking a webhook "{webhook_name}"')
                    json = await f(*args, **kwargs)

                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=json) as response:
                            if response.ok:
                                webhook_debug(f'Webhook "{webhook_name}" invoked successfully')
                            else:
                                text = await response.text()
                                log.error(f'Webhook "{webhook_name}" invocation failed: {response.status}, {text}')
                else:
                    webhook_debug(f'Webhook "{webhook_name}" disabled')
            except Exception:
                log.exception('An error occurred during a webhook invocation')

        return webhook_wrapper

    return decorator


class Webhook:
    def __init__(self, config):
        self.config = config

    @webhook('lobby_joined')
    async def invoke_webhook_lobby_joined(self, username, total_players):
        if total_players == 1:
            description = f'There is {total_players} player waiting in the lobby.'
        else:
            description = f'There are {total_players} players waiting in the lobby.'

        return {'embeds': [{
            'title': f'{username} joined the lobby!',
            'description': description,
            'color': 0x00ff00,
        }]}

    @webhook('lobby_left')
    async def invoke_webhook_lobby_left(self, username, total_players):
        if total_players == 1:
            description = f'There is {total_players} player waiting in the lobby.'
        else:
            description = f'There are {total_players} players waiting in the lobby.'

        return {'embeds': [{
            'title': f'{username} left the lobby!',
            'description': description,
            'color': 0xff0000,
        }]}

    @webhook('lobby_set_comment')
    async def invoke_webhook_lobby_set_comment(self, username, comment):
        return {'embeds': [{
            'title': f'{username} changed their communiqué.',
            'description': comment,
            'color': 0xffa500,
        }]}

    @webhook('lobby_message')
    async def invoke_webhook_lobby_message(self, username, message):
        return {
            'content': f'**{username}:** {message}',
        }

    @webhook('game_started')
    async def invoke_webhook_game_started(self, username, opponent_username):
        return {'embeds': [{
            'title': f'{username} and {opponent_username} have started a match!',
            'color': 0x3232ff,
        }]}

    @webhook('game_ended')
    async def invoke_webhook_game_ended(self, result: 'GameResultHistory'):
        return {'embeds': [{
            'title': f'{result.player_won} beat {result.player_lost} {result.won_score}-{result.lost_score}!',
            'description':
                f'The game lasted {result.time_str()} and took {result.moves} moves.',
            'color': 0x3232ff,
        }]}

    @webhook('logger', disable_log=True)
    async def invoke_webhook_logger(self, data: str):
        return {'content': f'```\n{data}\n```'}
