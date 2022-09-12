from typing import List, Coroutine

from routines import routine_manager
from sc2.position import Point2
from sc2.bot_ai import BotAI
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

def execute():
    # Find safe bases
    safe_bases = routine_manager.bot.townhalls
    # TODO: Remove bases where drones should be pulled away from

    # Find unused drones
    unused_drones = []
    for drone in routine_manager.bot.workers:
        if drone.is_idle:
            unused_drones.append(drone)
            continue
        if routine_manager.bot.townhalls.closest_to(drone) not in safe_bases:
            unused_drones.append(drone) # Worker is in danger
            continue

    # Find drones in oversaturated gas
    for extractor in routine_manager.bot.gas_buildings.ready:
        workers_to_take = extractor.surplus_harvesters
        if workers_to_take > 0:
            local_workers = routine_manager.bot.workers.filter(
                lambda unit: unit.order_target == extractor.tag or
                             (unit.is_carrying_vespene and unit.order_target == routine_manager.bot.townhalls.closest_to(extractor).tag)
            )
            while workers_to_take > 0:
                unused_drones.append(local_workers.pop())
                workers_to_take -= 1

    # TODO: Add unused drones to undersaturated gas
    # TODO: Add unused drones to undersaturated minerals
    # TODO: Add unused drones to remaining minerals
    # TODO: Balance mineral oversaturation