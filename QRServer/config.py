from dataclasses import dataclass


@dataclass
class Config:
    SWF_VER = 5
    LOBBY_PORT = 3000
    GAME_PORT = 3001
    HOST = 'localhost'
