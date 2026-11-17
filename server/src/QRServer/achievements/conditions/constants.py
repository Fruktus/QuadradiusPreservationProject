from enum import StrEnum


class GridSize(StrEnum):
    # COLxROW (measured in tiles)

    # 20x16
    LARGE = 'large'
    # 15x11
    MAXIMUM = 'maximum'
    # 9x9
    NINEXNINE = '9x9'
    # 10x8 (default)
    MEDIUM = 'medium (default)'
    # 6x5
    SMALL = 'small'


class SquadronSize(StrEnum):
    # The actual starting piece count is calculated individually per grid size
    LARGE = 'large (default)'
    MAXIMUM = 'maximum'
    MEDIUM = 'medium'
    SMALL = 'small'
