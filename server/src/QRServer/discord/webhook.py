import aiohttp
from QRServer import config


async def send_webhook_joined_lobby(username, total_players):
    url = config.discord_webhook_lobby_url.get()
    if url:
        if total_players == 1:
            description = f'There is {total_players} player waiting in the lobby.'
        else:
            description = f'There are {total_players} players waiting in the lobby.'

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={'embeds': [{
                'title': f'{username} joined the lobby!',
                'description': description,
                'color': 0x00ff00,
            }]}):
                pass


async def send_webhook_left_lobby(username, total_players):
    url = config.discord_webhook_lobby_url.get()
    if url:
        if total_players == 1:
            description = f'There is {total_players} player waiting in the lobby.'
        else:
            description = f'There are {total_players} players waiting in the lobby.'

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={'embeds': [{
                'title': f'{username} left the lobby!',
                'description': description,
                'color': 0xff0000,
            }]}):
                pass
