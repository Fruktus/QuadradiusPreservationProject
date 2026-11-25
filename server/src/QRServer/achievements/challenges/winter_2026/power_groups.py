from dataclasses import dataclass, field

from QRServer.common import powers


@dataclass(frozen=True)
class Power:
    """Singular power from the game.
    `codename` is the internal name, `name` is the client's.
    `codenames` also holds the `_ROW` / `_COL` versions of a ranged power, where those exist."""
    codename: str
    name: str
    codenames: frozenset[str] = field(init=False, compare=False, repr=False)
    ranged: bool = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not powers.is_valid(self.codename):
            raise ValueError(f'Winter power {self.codename} ({self.name}) does not exist')
        versions = {v for v in (f'{self.codename}_ROW', f'{self.codename}_COL') if powers.is_valid(v)}
        object.__setattr__(self, 'codenames', frozenset({self.codename, *versions}))
        object.__setattr__(self, 'ranged', bool(versions))


@dataclass(frozen=True)
class PowerGroup:
    """A set of powers grouped by theme"""
    label: str
    meaning: str
    members: tuple[Power, ...]
    codenames: frozenset[str] = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if len(set(self.members)) != len(self.members):
            raise ValueError(f'A power is twice in the {self.label} group')
        object.__setattr__(self, 'codenames', frozenset().union(*(member.codenames for member in self.members)))

    def describe(self) -> str:
        names = ', '.join(member.name for member in self.members)
        versions = '; Radial/Row/Column versions count' if any(member.ranged for member in self.members) else ''
        return f'**{self.label}**: {self.meaning} ({names}{versions}).'


# Offensive
DESTROY = Power('DESTROY', 'Destroy')
KAMIKAZE = Power('KAMIKAZE', 'Kamikaze')
ACIDIC = Power('HOLES', 'Acidic')
BOMBS = Power('BOMBS', 'Bombs')
SMART_BOMBS = Power('SMART_BOMBS', 'Smart Bombs')
SNAKE_TUNNELING = Power('SNAKE', 'Snake Tunneling')
BANKRUPT = Power('BANKRUPT', 'Bankrupt')

# Map
RAISE_TILE = Power('RAISE_BLOCK', 'Raise Tile')
LOWER_TILE = Power('LOWER_BLOCK', 'Lower Tile')
PLATEAU = Power('PLATEAU', 'Plateau')
MOAT = Power('MOAT', 'Moat')
WALL_ROW = Power('HORIZONTAL_WALL', 'Wall Row')
WALL_COLUMN = Power('VERTICAL_WALL', 'Wall Column')
TRENCH_ROW = Power('HORIZONTAL_TRENCH', 'Trench Row')
TRENCH_COLUMN = Power('VERTICAL_TRENCH', 'Trench Column')
INVERT = Power('INVERT', 'Invert')
DREDGE = Power('RAISE_LOWER', 'Dredge')
REFURB = Power('CLEAN', 'Refurb')
BUNKER = Power('ONEWAY_WALL', 'Bunker')

# Movement
MOVE_AGAIN = Power('MULTIPLE_MOVES', 'Move Again')
MOVE_DIAGONAL = Power('ANGLE_MOVEMENT', 'Move Diagonal')
FLAT_TO_SPHERE = Power('WRAP_AROUND', 'Flat To Sphere')
CLIMB_TILE = Power('CLIMB_BLOCK', 'Climb Tile')
CENTERPULT = Power('CENTER_TELEPORT', 'Centerpult')
HOTSPOT = Power('HOTSPOT', 'Hotspot')
SWITCHEROO = Power('SWITCHEROO', 'Switcheroo')
RECURSIVE = Power('RECURSIVE', 'Recursive')
RELOCATE = Power('RANDOM_TELEPORT', 'Relocate')
SCRAMBLE = Power('SCATTER', 'Scramble')

# Upgrades
JUMP_PROOF = Power('INVINCIBLE', 'Jump Proof')
INVISIBLE = Power('INVISIBLE', 'Invisible')
GROW_QUADRADIUS = Power('EXTEND_RADIUS', 'Grow Quadradius')
SCAVENGER = Power('SCAVENGER', 'Scavenger')
NETWORK_BRIDGE = Power('NETWORK_BRIDGE', 'Network Bridge')

# Malfunctions
SPYWARE = Power('VIEW_POWER', 'Spyware')
PARASITE = Power('PARASITE', 'Parasite')
INHIBIT = Power('INHIBIT', 'Inhibit')
TRIPWIRE = Power('TRIPWIRE', 'Tripwire')

# Inventory
TEACH = Power('TEACH', 'Teach')
LEARN = Power('LEARN', 'Learn')
PILFER = Power('PILFER', 'Pilfer')
BENEFICIARY = Power('KING', 'Beneficiary')
TWO_X = Power('DOUBLE', '2x')
POWER_PLANT = Power('POWER_PLANT', 'Power Plant')

# Orbs
ORB_SPY = Power('ORBSPY', 'Orb Spy')
ORBIC_REHASH = Power('REHASH', 'Orbic Rehash')

# Squadron
MULTIPLY = Power('MULTIPLY', 'Multiply')
SWAP = Power('SWAP', 'Swap')
RECRUIT = Power('RECRUIT', 'Recruit')
PURIFY = Power('PURIFY', 'Purify')


# # # # # #
# Groups  #
# # # # # #

DESTRUCTIVE_GROUP = PowerGroup(
    'Destructive', 'powers which destroy pieces',
    (DESTROY, KAMIKAZE, ACIDIC, BOMBS, SMART_BOMBS, SNAKE_TUNNELING),
)

TERRAFORM_GROUP = PowerGroup(
    'Terraform', 'powers which reshape the tiles of the arena',
    (RAISE_TILE, LOWER_TILE, PLATEAU, MOAT, WALL_ROW, WALL_COLUMN, TRENCH_ROW, TRENCH_COLUMN,
     INVERT, DREDGE, REFURB, BUNKER),
)

MOVEMENT_GROUP = PowerGroup(
    'Movement', 'powers which change how or where a piece moves',
    (MOVE_AGAIN, MOVE_DIAGONAL, FLAT_TO_SPHERE, CLIMB_TILE, RELOCATE, SCRAMBLE, CENTERPULT, HOTSPOT,
     SWITCHEROO, RECURSIVE),
)

# Overlaps with Movement and Inventory
ENHANCEMENT_GROUP = PowerGroup(
    'Enhancement', 'powers which permanently upgrade a piece',
    (MOVE_DIAGONAL, FLAT_TO_SPHERE, CLIMB_TILE, JUMP_PROOF, INVISIBLE, GROW_QUADRADIUS,
     SCAVENGER, NETWORK_BRIDGE, CENTERPULT, SWITCHEROO),
)

# Tripwire only kills if the piece moves, so it is a fault and not Destructive
MALFUNCTION_GROUP = PowerGroup(
    'Malfunction', 'powers which leave a lasting fault on opponent pieces',
    (SPYWARE, PARASITE, INHIBIT, TRIPWIRE),
)

INVENTORY_GROUP = PowerGroup(
    'Inventory', 'powers which copy, steal or share powers between pieces',
    (TEACH, LEARN, PILFER, BENEFICIARY, TWO_X, SCAVENGER, POWER_PLANT, NETWORK_BRIDGE),
)

ORB_SPY_GROUP = PowerGroup(
    'Orb Spy', 'powers which reveal the orbs that will spawn on the tiles around you',
    (ORB_SPY,),
)

ALL_GROUPS: tuple[PowerGroup, ...] = (
    DESTRUCTIVE_GROUP, TERRAFORM_GROUP, MOVEMENT_GROUP, ENHANCEMENT_GROUP, MALFUNCTION_GROUP, INVENTORY_GROUP,
    ORB_SPY_GROUP,
)
