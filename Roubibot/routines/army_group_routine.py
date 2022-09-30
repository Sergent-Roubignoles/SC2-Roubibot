from typing import List, Coroutine

from micro.army_group import AttackGroup
from routines import routine_manager
from sc2.position import Point2
from sc2.bot_ai import BotAI
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

army_groups: [AttackGroup] = []


def execute():
    army_group: AttackGroup
    for army_group in army_groups:
        army_group.update_attacker_list()
        if len(army_group.attackers) == 0:
            army_groups.remove(army_group)
        else:
            army_group.attack()
