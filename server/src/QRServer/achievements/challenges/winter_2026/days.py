"""The 24 days of the calendar for 2026 Winter Event.
A day is one class: its story, objective and check, so reading or tuning a day never needs another file.
This file is for prose/conditions only, `challenge.py` handles timing and running.

The orb crates and the snake crates were swapped at the North Pole,
so the workshop has no orbs and too many snakes. Orbs always fuel powers.
The Quad Gods are unreliable on purpose (blessing or cursing luck),
and snakes may or may not help.
"""
from abc import ABC, abstractmethod

from QRServer.achievements.challenges.winter_2026.power_groups import (
    PowerGroup, DESTRUCTIVE_GROUP, ENHANCEMENT_GROUP, INVENTORY_GROUP, MALFUNCTION_GROUP, MOVEMENT_GROUP,
    ORB_SPY_GROUP, TERRAFORM_GROUP, MULTIPLY, RELOCATE, SNAKE_TUNNELING,
)
from QRServer.achievements.conditions import (
    BaseRecordingCondition, GridSize, OrbPickupCountCondition, PowerUseCountCondition, RemovalBurstCondition,
    PiecesDestroyedCountCondition, ReportCondition, SquadronSize, UniquePowersUsedCondition,
)

Conditions = list[ReportCondition | BaseRecordingCondition]

EVERY_USE = 'Any powers count, not necessarily different ones.'


class WinterDay(ABC):
    """Helper used to configure each event day - set its title, prose, objective and conditions."""
    day_number: int
    title: str
    story: str
    objective: str
    groups: tuple[PowerGroup, ...] = ()  # power groups, shown in additional details in post under "Details"
    notes: str = ''  # also shown under "Details"

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        # Ensure at runtime that class is configured correctly
        missing = [name for name in ('day_number', 'title', 'story', 'objective') if not hasattr(cls, name)]
        if missing:
            raise TypeError(f'{cls.__name__} does not define {", ".join(missing)}')

    @property
    def objective_details(self) -> str:
        """The "Details" text: every post explains the terms it uses."""
        lines = [group.describe() for group in self.groups]
        if self.notes:
            lines.append(self.notes)
        return '\n'.join(lines)

    @abstractmethod
    def conditions(self) -> Conditions:
        pass


# Chapter I: Trouble at the Workshop
# The workshop runs on orbs and the shelves are bare. You scrape together enough to get the first sleigh out,
# and something in the crates starts to hiss.
class Day01(WinterDay):
    day_number = 1
    title = 'A Workshop in Chaos'
    story = ('The workshop runs on orbs, and this morning the shelves are bare. The elves are panicking, nobody '
             'can say where the latest shipment went, and the presents are not going to make themselves. Start by '
             'bringing in whatever orbs you can find.')
    ORBS = 15
    objective = f'Collect **{ORBS}** or more orbs in a ranked match.'

    def conditions(self) -> Conditions:
        return [OrbPickupCountCondition(min_count=self.ORBS)]


class Day02(WinterDay):
    day_number = 2
    title = 'The Elves Need a Hand'
    story = ('The first orbs are in, and the elves are desperate to make every one of them count. Powers are how '
             'this workshop gets things done, and there is one in particular they swear works wonders when there '
             'is never enough to go around.')
    POWER = MULTIPLY
    objective = f'Use the **{POWER.name}** power in a ranked match.'

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(self.POWER.codenames, min_count=1)]


class Day03(WinterDay):
    day_number = 3
    title = 'The Present Pile'
    story = ('With the orbs trickling in, the presents are finally moving, straight into a pile that already '
             'covers half the workshop. The elves need more floor space before the whole place disappears under '
             'boxes, and only a big board has the room.')
    objective = 'Play a ranked match on a **large** or **maximum** board.'

    def conditions(self) -> Conditions:
        return [ReportCondition(grid=(GridSize.LARGE, GridSize.MAXIMUM))]


class Day04(WinterDay):
    day_number = 4
    title = 'Workshop Safety'
    story = ('The powers are working, which is good, and also very loud, which is less good. The elves have started '
             'handing out protective gear between shifts, and you would be wise to grab some enhancements while '
             'they last.')
    ENHANCEMENT_USES = 4
    objective = f'Use enhancement powers **{ENHANCEMENT_USES}** times in a ranked match.'
    groups = (ENHANCEMENT_GROUP,)
    notes = EVERY_USE

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(ENHANCEMENT_GROUP.codenames, min_count=self.ENHANCEMENT_USES)]


class Day05(WinterDay):
    day_number = 5
    title = 'A Few Missing Pieces'
    story = ('Between the powers and the chaos, pieces keep going missing. The elves are counting what is left and '
             'would very much like to keep as much of it as they can, so finish the job with a decent number '
             'still standing.')
    PIECES_LEFT = 5
    objective = f'Win a ranked match with at least **{PIECES_LEFT}** of your pieces left.'

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True, min_pieces=self.PIECES_LEFT)]


class Day06(WinterDay):
    day_number = 6
    title = 'Santa\'s First Delivery'
    story = ('The first sleigh is loaded, and the elves are smiling for the first time in days. It takes a proper '
             'effort to get it out the door, and just as it lifts off, something in the crates starts to hiss.')
    POWER_USES = 8
    objective = f'Win a ranked match and use at least **{POWER_USES}** powers along the way.'

    # Cancel Multiply may be recorded as a power use and add one
    def conditions(self) -> Conditions:
        return [ReportCondition(won=True), PowerUseCountCondition(min_count=self.POWER_USES)]


# Chapter II: The Great Snake Escape
# The hissing was a snake. The orb crates were swapped with snake crates, and the snakes spread through the
# workshop (and, it turns out, are sitting on the missing orbs). By the end they are penned in.
class Day07(WinterDay):
    day_number = 7
    title = 'They\'re Getting Everywhere!'
    story = ('The hiss was a snake. Then another, and then a dozen more. The crates have been opened and the '
             'snakes are slipping between benches and shelves faster than anyone can catch them, so you will '
             'have to keep moving to keep up.')
    MOVEMENT_USES = 3
    objective = f'Use movement powers **{MOVEMENT_USES}** times in a ranked match.'
    groups = (MOVEMENT_GROUP,)

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(MOVEMENT_GROUP.codenames, min_count=self.MOVEMENT_USES)]


class Day08(WinterDay):
    day_number = 8
    title = 'Snake Whisperer'
    story = ('The elves have heard that some people can talk a snake into helping, and that others get nothing '
             'but a blank stare. They are desperate enough to find out which kind you are, and tunnels seem like '
             'a good place to start.')
    POWER = SNAKE_TUNNELING
    objective = f'Use the **{POWER.name}** power in a ranked match.'

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(self.POWER.codenames, min_count=1)]


class Day09(WinterDay):
    day_number = 9
    title = 'Don\'t Let Them Bite!'
    story = ('Friendly or not, the snakes have found the toy shelves and are making a mess of them. The elves '
             'have run out of patience and would like a few of them gone, preferably in a way that sticks.')
    DESTRUCTIVE_USES = 2
    objective = f'Use destructive powers **{DESTRUCTIVE_USES}** times in a ranked match.'
    groups = (DESTRUCTIVE_GROUP,)
    notes = EVERY_USE

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(DESTRUCTIVE_GROUP.codenames, min_count=self.DESTRUCTIVE_USES)]


class Day10(WinterDay):
    day_number = 10
    title = 'Snake Charmer'
    story = ('Gentle methods are not working. The snakes have bunched up in one big nest, and the elves have a '
             'plan: a single big blow to clear the lot at once. It might work brilliantly, or just make the '
             'mess bigger.')
    COMBO_DESTROYED_PIECES = 3
    objective = f'Destroy **{COMBO_DESTROYED_PIECES}** or more pieces with a single power in a ranked match.'

    def conditions(self) -> Conditions:
        return [RemovalBurstCondition(min_count=self.COMBO_DESTROYED_PIECES)]


class Day11(WinterDay):
    day_number = 11
    title = 'The Great Round-Up'
    story = ('The snakes are cornered, and they have been sitting on something. As the nests come apart, the '
             'missing orbs turn up stuffed between the crates. The elves want every last one recovered, and the '
             'snakes cleared out of the way in the process.')
    ORBS = 18
    PIECES_DESTROYED = 7
    objective = (f'Collect **{ORBS}** or more orbs and get **{PIECES_DESTROYED}** or more pieces destroyed '
                 f'in the same ranked match.')

    def conditions(self) -> Conditions:
        return [OrbPickupCountCondition(min_count=self.ORBS),
                PiecesDestroyedCountCondition(min_count=self.PIECES_DESTROYED)]


class Day12(WinterDay):
    day_number = 12
    title = 'The Snakes Strike Back'
    story = ('The last few snakes are not going quietly. A few well-placed walls and trenches should pen them in '
             'for good, and then the elves can finally ask the question that has been bothering them all week: '
             'where did the rest of the orbs go?')
    TERRAFORM_USES = 1
    objective = 'Win a ranked match and use a terraform power.'
    groups = (TERRAFORM_GROUP,)

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True),
                PowerUseCountCondition(TERRAFORM_GROUP.codenames, min_count=self.TERRAFORM_USES)]


# Chapter III: The Orb Workshop
# With the snakes penned, you track down where the rest of the orbs went. The Quad Gods get involved, with
# unreliable results, the experiments pile up, and the day 18 reveals what caused all this.
class Day13(WinterDay):
    day_number = 13
    title = 'Where Did All the Orbs Go?'
    story = ('With the snakes penned in, the elves have noticed that the orb shelves are still half empty. The '
             'crate labels are no help at all, and someone will have to go and look for the missing orbs '
             'themselves. A bit of spying should do it.')
    ORB_SPY_USES = 1
    objective = 'Use an **orb spy** power in a ranked match.'

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(ORB_SPY_GROUP.codenames, min_count=self.ORB_SPY_USES)]


class Day14(WinterDay):
    day_number = 14
    title = 'Divine Intervention'
    story = ('The trail leads somewhere none of the elves expected, so they have decided to ask the Quad Gods to '
             'nudge things back where they belong. Opinions differ on whether the Gods bless or curse, but there '
             'is nobody else left to ask.')
    POWER = RELOCATE
    objective = f'Use the **{POWER.name}** power in a ranked match.'

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(self.POWER.codenames, min_count=1)]


class Day15(WinterDay):
    day_number = 15
    title = 'Forbidden Experiments'
    story = ('Whatever the Gods did, it did not fix everything, and the elves are not waiting around for a second '
             'answer. They are copying, borrowing and occasionally swiping each other\'s tricks. Some of the '
             'results are promising, and others probably should not have left the workshop.')
    INVENTORY_USES = 3
    objective = f'Use inventory powers **{INVENTORY_USES}** times in a ranked match.'
    groups = (INVENTORY_GROUP,)
    notes = EVERY_USE

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(INVENTORY_GROUP.codenames, min_count=self.INVENTORY_USES)]


class Day16(WinterDay):
    day_number = 16
    title = 'Orb Overload'
    story = ('The orbs are trickling back in, and the elves are burning through them as fast as they arrive. Every '
             'bench is trying a different power, and the more of them you can try before the day is out, the '
             'better.')
    DISTINCT_POWERS = 12
    objective = f'Use **{DISTINCT_POWERS}** different powers in a ranked match.'
    notes = 'The Row, Column and Radial versions count as separate ones.'

    def conditions(self) -> Conditions:
        return [UniquePowersUsedCondition(min_count=self.DISTINCT_POWERS)]


class Day17(WinterDay):
    day_number = 17
    title = 'The Gods Are Watching'
    story = ('The elves are sure the Quad Gods are watching today. Whether that means blessed luck or cursed luck '
             'is anyone\'s guess, but a tight 9x9 board leaves less room for either to hide.')
    objective = 'Win a ranked match on a **9x9** board.'

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True, grid=GridSize.NINEXNINE)]


class Day18(WinterDay):
    day_number = 18
    title = 'A Little Christmas Magic'
    story = ('Blessed or not, it worked. The orbs are coming in steadily, the powers are finally working together, '
             'and the elves have found the mistake behind all of it: the orb crates were swapped with the snake '
             'crates before they ever left the dock. All that is left is the final push.')
    POWER_USES = 12
    ORBS = 18
    objective = (f'Win a ranked match using at least **{POWER_USES}** powers and collecting **{ORBS}** or more '
                 f'orbs.')
    notes = 'Every use of any power counts.'

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True),
                PowerUseCountCondition(min_count=self.POWER_USES),
                OrbPickupCountCondition(min_count=self.ORBS)]


# Chapter IV: The Final Preparations
# The mix-up is untangled and the orbs are flowing again. Fill the shelves, get the last shipment out,
# clear out the stragglers and load the sleigh.
class Day19(WinterDay):
    day_number = 19
    title = 'Back to Work!'
    story = ('With the crates labelled properly, the orbs are flowing again and the workshop is back in business. '
             'The elves are rebuilding the stockpile for the final stretch, one orb at a time.')
    ORBS = 22
    objective = f'Collect **{ORBS}** or more orbs in a ranked match.'

    def conditions(self) -> Conditions:
        return [OrbPickupCountCondition(min_count=self.ORBS)]


class Day20(WinterDay):
    day_number = 20
    title = 'The Last Delivery'
    story = ('The final shipment has arrived, bigger than any before it. The elves are racing to get all of it '
             'onto the sleigh, and Santa is not leaving without a full load.')
    ORBS = 26
    objective = f'Win a ranked match and collect **{ORBS}** or more orbs.'

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True), OrbPickupCountCondition(min_count=self.ORBS)]


class Day21(WinterDay):
    day_number = 21
    title = 'Christmas Combat'
    story = ('A few stray snakes have slipped through the cracks, and the elves are not letting them anywhere near '
             'the sleigh. Clear them out and be thorough about it, because Christmas will not be saved by being '
             'polite.')
    PIECES_DESTROYED = 12
    objective = f'Destroy **{PIECES_DESTROYED}** or more pieces in a ranked match.'

    def conditions(self) -> Conditions:
        return [PiecesDestroyedCountCondition(min_count=self.PIECES_DESTROYED)]


class Day22(WinterDay):
    day_number = 22
    title = 'Everything Must Go!'
    story = ('The last stragglers need a final clear-out. The elves want a few heavy hitters to do the clearing, '
             'and a well-placed glitch or two to keep everyone else out of the way.')
    DESTRUCTIVE_USES = 3
    MALFUNCTION_USES = 1
    objective = (f'Use destructive powers **{DESTRUCTIVE_USES}** times and a malfunction power in the same '
                 f'ranked match.')
    groups = (DESTRUCTIVE_GROUP, MALFUNCTION_GROUP)

    def conditions(self) -> Conditions:
        return [PowerUseCountCondition(DESTRUCTIVE_GROUP.codenames, min_count=self.DESTRUCTIVE_USES),
                PowerUseCountCondition(MALFUNCTION_GROUP.codenames, min_count=self.MALFUNCTION_USES)]


class Day23(WinterDay):
    day_number = 23
    title = 'Christmas Eve Panic'
    story = ('The sleigh is almost packed, and the clock on the workshop wall is not on your side. Santa has to '
             'be gone before Christmas Eve is over, and the elves need one fast, clean finish.')
    MINUTES = 15
    objective = f'Win a ranked match in **{MINUTES}** minutes or less (hint: smaller board may help).'

    def conditions(self) -> Conditions:
        return [ReportCondition(won=True, max_seconds=self.MINUTES * 60)]


class Day24(WinterDay):
    day_number = 24
    title = 'The Great Christmas Mix-Up'
    story = ('It is finally Christmas. The crates are labelled, the snakes are penned and the sleigh is stocked '
             'with orbs, and for once nothing has been mixed up. All that is left is to load it properly, with '
             'the full crew on a big board. Merry Christmas!')
    objective = 'Play a ranked match on a **large** board with a **large** squadron.'

    def conditions(self) -> Conditions:
        return [ReportCondition(grid=GridSize.LARGE, squadron=SquadronSize.LARGE)]


DAYS: tuple[WinterDay, ...] = (
    Day01(), Day02(), Day03(), Day04(), Day05(), Day06(), Day07(), Day08(), Day09(), Day10(), Day11(), Day12(),
    Day13(), Day14(), Day15(), Day16(), Day17(), Day18(), Day19(), Day20(), Day21(), Day22(), Day23(), Day24(),
)

_numbers = sorted(day.day_number for day in DAYS)
if _numbers != list(range(1, 25)):
    raise ValueError(f'Every day from 1 to 24 has to be defined exactly once, got {_numbers}')
