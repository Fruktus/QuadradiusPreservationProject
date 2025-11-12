from aiohttp import web


def create_v1_app(game_server, lobby_server):
    """
    Api V1 sub-app - provides all endpoints served under /api/v1/
    """
    app_v1 = web.Application()
    app_v1['game_server'] = game_server
    app_v1['lobby_server'] = lobby_server

    app_v1.add_routes([
        web.get('/health', _v1_health),
        web.get('/game/stats', _v1_game_stats),
        web.get('/lobby/stats', _v1_lobby_stats),
    ])

    return app_v1


async def _v1_health(_request: web.Request):
    return web.json_response({})


async def _v1_game_stats(request: web.Request):
    player_count = request.app['game_server'].get_player_count()
    return web.json_response({
        'player_count': player_count,
    })


async def _v1_lobby_stats(request: web.Request):
    player_count = request.app['lobby_server'].get_player_count()
    return web.json_response({
        'player_count': player_count,
    })
