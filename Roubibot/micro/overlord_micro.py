from sc2.ids.ability_id import AbilityId

from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.bot_ai import BotAI

bot: BotAI
enemy_uses_hidden_units = True

async def verify_no_hidden_units(unit: Unit):
    global enemy_uses_hidden_units
    if not enemy_uses_hidden_units:
        if unit_is_hidden(unit):
            enemy_uses_hidden_units = True
            await bot.chat_send("Hidden units detected!")

def unit_is_hidden(unit: Unit):
    return unit.is_cloaked or unit.is_burrowed or unit.is_hallucination

def overlord_routine():
    create_overseers()
    micro_overseers()
    micro_changelings()
    place_overlords()

def create_overseers():
    if enemy_uses_hidden_units:
        if bot.units(UnitTypeId.OVERSEER).amount + bot.already_pending(UnitTypeId.OVERSEER) < 1:
            if bot.structures.of_type({UnitTypeId.LAIR, UnitTypeId.HIVE}).amount > 0:
                if bot.can_afford(UnitTypeId.OVERSEER):
                    overlords = bot.units(UnitTypeId.OVERLORD)
                    if overlords.amount > 0:
                        overlord_to_morph = bot.units(UnitTypeId.OVERLORD).closest_to(bot.start_location)
                        overlord_to_morph(AbilityId.MORPH_OVERSEER)

def micro_overseers():
    for overseer in bot.units(UnitTypeId.OVERSEER):
        if overseer.energy >= 50:
            overseer(AbilityId.SPAWNCHANGELING_SPAWNCHANGELING)

    hidden_units = bot.enemy_units.filter(lambda unit: unit_is_hidden(unit))
    if hidden_units.amount > 0:
        for overseer in bot.units(UnitTypeId.OVERSEER):
            overseer.move(hidden_units.closest_to(overseer).position)

def micro_changelings():
    for changeling in bot.units(UnitTypeId.CHANGELING):
        if changeling.is_idle:
            changeling.move(bot.enemy_start_locations[0])

our_expansion_locations = []
def find_our_expansion_locations():
    if len(our_expansion_locations) > 0:
        return
    for base in bot.expansion_locations_list:
        if bot.start_location.distance_to(base) < bot.enemy_start_locations[0].distance_to(base):
            our_expansion_locations.append(base)

position_overlord_pairs = {}
def place_overlords():
    find_our_expansion_locations()
    for point in our_expansion_locations:
        if point not in position_overlord_pairs.keys():
            position_overlord_pairs[point] = None

    overlords = bot.units(UnitTypeId.OVERLORD)

    # Find free overlords
    free_overlords = []
    for overlord in overlords:
        if overlord.tag not in position_overlord_pairs.values():
            free_overlords.append(overlord)
        if bot.structures({UnitTypeId.LAIR, UnitTypeId.HIVE}).amount > 0:
            overlord(AbilityId.BEHAVIOR_GENERATECREEPON)

    for position in position_overlord_pairs.keys():
        if position_overlord_pairs[position] is None:
            # Add new overlord
            if len(free_overlords) > 0:
                overlord_to_assign = free_overlords.pop()
                overlord_to_assign.move(position)
                overlord_to_assign.hold_position(True)
                position_overlord_pairs[position] = overlord_to_assign.tag
        else:
            if position_overlord_pairs[position] not in overlords.tags:
                # Remove dead overlord
                position_overlord_pairs[position] = None