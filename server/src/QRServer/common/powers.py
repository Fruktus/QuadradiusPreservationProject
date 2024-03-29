__powers = [
    'MOAT',
    'PLATEAU',
    'INVERT',
    'HORIZONTAL_TRENCH',
    'HORIZONTAL_WALL',
    'VERTICAL_TRENCH',
    'VERTICAL_WALL',
    'TEACH',
    'LEARN',
    'SCATTER',
    'VIEW_POWER',
    'EXTEND_RADIUS',
    'INVERT_ROW',
    'INVERT_COL',
    'LEARN_COL',
    'LEARN_ROW',
    'TEACH_COL',
    'TEACH_ROW',
    'SCATTER_ROW',
    'SCATTER_COL',
    'VIEW_POWER_ROW',
    'VIEW_POWER_COL',
    'PILFER',
    'PILFER_COL',
    'PILFER_ROW',
    'DOUBLE',
    'KING',
    'KAMIKAZE',
    'KAMIKAZE_COL',
    'KAMIKAZE_ROW',
    'SWAP',
    'SWAP_COL',
    'SWAP_ROW',
    'RECRUIT',
    'RECRUIT_COL',
    'RECRUIT_ROW',
    'PARASITE',
    'PARASITE_COL',
    'PARASITE_ROW',
    'DESTROY',
    'DESTROY_COL',
    'DESTROY_ROW',
    'INHIBIT',
    'INHIBIT_COL',
    'INHIBIT_ROW',
    'REHASH',
    'BOMBS',
    'SMART_BOMBS',
    'TRIPWIRE',
    'TRIPWIRE_COL',
    'TRIPWIRE_ROW',
    'HOLES',
    'HOLES_COL',
    'HOLES_ROW',
    'SNAKE',
    'RANDOM_TELEPORT',
    'HOTSPOT',
    'SCAVENGER',
    'PURIFY',
    'PURIFY_COL',
    'PURIFY_ROW',
    'ORBSPY',
    'ORBSPY_COL',
    'ORBSPY_ROW',
    'SWITCHEROO',
    'RAISE_LOWER',
    'RAISE_LOWER_COL',
    'RAISE_LOWER_ROW',
    'CLEAN_ROW',
    'CLEAN_COL',
    'CLEAN',
    'BANKRUPT',
    'BANKRUPT_COL',
    'BANKRUPT_ROW',
    'MULTIPLY',
    'CANCEL_MULTIPLY',
    'RAISE_BLOCK',
    'LOWER_BLOCK',
    'CLIMB_BLOCK',
    'INVISIBLE',
    'INVINCIBLE',
    'MULTIPLE_MOVES',
    'ANGLE_MOVEMENT',
    'WRAP_AROUND',
    'CENTER_TELEPORT',
    'POWER_PLANT',
    'NETWORK_BRIDGE',
    'RECURSIVE',
    'ONEWAY_WALL',
]


def is_valid(power_name: str):
    return power_name in __powers
