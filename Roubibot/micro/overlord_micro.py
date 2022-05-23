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