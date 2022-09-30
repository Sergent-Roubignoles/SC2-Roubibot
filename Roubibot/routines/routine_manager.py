from typing import List, Coroutine

from routines import drone_routine, army_group_routine

from sc2.unit import Unit
from sc2.position import Point2
from sc2.bot_ai import BotAI
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

bot: BotAI

def execute_routines():
    # Pre routines: gathers game info used by main routines

    # Main routines
    drone_routine.execute()
    army_group_routine.execute()