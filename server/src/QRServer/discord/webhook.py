import logging

import aiohttp

from QRServer import config
from QRServer.common.classes import GameResultHistory

log = logging.getLogger('webhook')


def webhook(webhook_name):
    def decorator(f):
        async def webhook_wrapper(*args, **kwargs):
            webhook_url = config.get(f'discord.webhook.{webhook_name}.url')

            try:
                if webhook_url:
                    log.debug(f'Invoking a webhook "{webhook_name}"')
                    json = await f(*args, **kwargs)

                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=json) as response:
                            log.debug(f'Webhook "{webhook_name}" invoked, status: {response.status}')
                else:
                    log.debug(f'Webhook "{webhook_name}" disabled')
            except Exception:
                log.exception('An error occurred during a webhook invocation')

        return webhook_wrapper

    return decorator


@webhook('lobby_joined')
async def invoke_webhook_lobby_joined(username, total_players):
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
async def invoke_webhook_lobby_left(username, total_players):
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
async def invoke_webhook_lobby_set_comment(username, comment):
    return {'embeds': [{
        'title': f'{username} changed their communiqué.',
        'description': comment,
        'color': 0xffa500,
    }]}


@webhook('lobby_message')
async def invoke_webhook_lobby_message(username, message):
    return {
        'content': f'**{username}:** {message}',
    }


@webhook('game_started')
async def invoke_webhook_game_started(username, opponent_username):
    return {'embeds': [{
        'title': f'{username} and {opponent_username} have started a match!',
        'color': 0x3232ff,
    }]}


@webhook('game_ended')
async def invoke_webhook_game_ended(result: 'GameResultHistory'):
    return {'embeds': [{
        'title': f'{result.player_won} beat {result.player_lost} {result.won_score}-{result.lost_score}!',
        'description':
            f'The game lasted {result.time_str()} and took {result.moves} moves.',
        'color': 0x3232ff,
    }]}
