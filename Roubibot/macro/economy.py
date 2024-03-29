from typing import List, Coroutine

from macro import tech
from sc2.bot_ai import BotAI
from sc2.game_data import Cost
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

saving_money = False

async def expand_eco(bot: BotAI, desired_workers: int, desired_gas: int):
    await bot.distribute_workers()

    # Build more extractors
    await get_gas(bot, desired_gas)

    global saving_money

    if tech.saving_money:
        saving_money = True
        return

    # Count active and max workers
    gas_workers = 0
    for extractor in bot.gas_buildings:
        gas_workers += extractor.assigned_harvesters
    max_gas_workers = bot.gas_buildings.amount * 3

    mineral_workers = bot.supply_workers - gas_workers
    max_mineral_workers = 0
    for hatchery in bot.townhalls:
        max_mineral_workers += hatchery.ideal_harvesters

    max_total_workers = max_mineral_workers + max_gas_workers

    # # Build more hatcheries
    # exploitable_mineral_fields = []
    # for mineral_field in bot.mineral_field:
    #     for hatchery in bot.townhalls.ready:
    #         if mineral_field.distance_to(hatchery) < 10:
    #             exploitable_mineral_fields.append(mineral_field)
    #             break

    if mineral_workers >= max_mineral_workers:
        # Expand if desired
        desired_mineral_workers = desired_workers - 3 * desired_gas
        if max_mineral_workers < desired_mineral_workers or (max_mineral_workers < desired_mineral_workers + 16 and bot.minerals > 500) :
            if not bot.already_pending(UnitTypeId.HATCHERY):
                next_expansion = await bot.get_next_expansion()  # TODO:Check for occupied locations
                if next_expansion is not None:
                    cost = bot.calculate_cost(UnitTypeId.HATCHERY)
                    if can_afford_while_saving(bot, cost):
                        await bot.build(UnitTypeId.HATCHERY, next_expansion)
                    else:
                        saving_money = True
                        return # Save for hatchery

    # Build minimum queens
    current_queens = bot.units(UnitTypeId.QUEEN).amount + bot.already_pending(UnitTypeId.QUEEN)
    desired_queens = bot.townhalls.amount + 1
    if current_queens < desired_queens:
        if bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount == 0:
            await tech.tech_zerglings(bot)
        else:
            cost = bot.calculate_cost(UnitTypeId.QUEEN)
            if not can_afford_while_saving(bot, cost):
                saving_money = True
                return
            idle_townhalls = bot.townhalls.ready.idle
            if idle_townhalls.amount > 0:
                idle_townhalls.random.train(UnitTypeId.QUEEN)

    # Build more drones
    current_workers = int(bot.supply_workers + bot.already_pending(UnitTypeId.DRONE))
    if current_workers < max_total_workers:
        cost = bot.calculate_cost(UnitTypeId.DRONE)
        if can_afford_while_saving(bot, cost):
            bot.train(UnitTypeId.DRONE)

    # # Get 1 extra hatchery if floating minerals
    # if bot.minerals > 400 and not bot.already_pending(UnitTypeId.HATCHERY):
    #     extra_mineral_fields = desired_mineral_fields - len(exploitable_mineral_fields)
    #     if not extra_mineral_fields >= 8:
    #         next_expansion = await bot.get_next_expansion()
    #         if next_expansion is not None:
    #             cost = bot.calculate_cost(UnitTypeId.HATCHERY)
    #             if can_afford_while_saving(bot, cost):
    #                 await bot.build(UnitTypeId.HATCHERY, next_expansion)

async def get_gas(bot: BotAI, desired_gas: int):
    global saving_money

    exploitable_extractors = bot.gas_buildings.filter(lambda unit: unit.has_vespene)
    if exploitable_extractors.amount + bot.already_pending(UnitTypeId.EXTRACTOR) < desired_gas:
        unexploited_geysers = []
        for geyser in bot.vespene_geyser:
            for hatchery in bot.townhalls.ready:
                if geyser.distance_to(hatchery) < 10:
                    unexploited_geysers.append(geyser)
                    continue
        if len(unexploited_geysers) > 0:
            target_geyser = unexploited_geysers[0]
            cost = bot.calculate_cost(UnitTypeId.EXTRACTOR)
            if can_afford_while_saving(bot, cost):
                bot.workers.closest_to(target_geyser).build_gas(target_geyser)
            else:
                saving_money = True
                return # Save for extractor

async def expand_army(bot: BotAI, max_army_supply = None):
    if max_army_supply is not None:
        if bot.supply_army >= max_army_supply:
            return

    if bot.supply_used == 200:
        return

    global saving_money

    # # Queens
    # if not saving_money and bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount > 0:
    #     if bot.can_afford(UnitTypeId.QUEEN):
    #         idle_hatcheries = bot.structures(UnitTypeId.HATCHERY).idle
    #         if idle_hatcheries.amount > 0:
    #             idle_hatcheries.first.train(UnitTypeId.QUEEN)

    # Ultralisks
    if not saving_money and bot.structures(UnitTypeId.ULTRALISKCAVERN).ready.amount > 0:
        ultralisks = bot.units(UnitTypeId.ULTRALISK).amount + bot.already_pending(UnitTypeId.ULTRALISK)
        if ultralisks * 6 < 0.15 * bot.supply_army:
            if bot.can_afford(UnitTypeId.ULTRALISK):
                bot.train(UnitTypeId.ULTRALISK)
            else:
                saving_money = True

    # Broodlords
    if not saving_money and bot.structures(UnitTypeId.GREATERSPIRE).ready.amount > 0:
        corruptors = bot.units(UnitTypeId.CORRUPTOR)
        if corruptors.amount > 1:
            if bot.can_afford(UnitTypeId.BROODLORD):
                corruptors.first(AbilityId.MORPHTOBROODLORD_BROODLORD)
            else:
                saving_money = True

    # Corruptors
    if not saving_money and bot.structures({UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE}).ready.amount > 0:
        corruptor_count = bot.units(UnitTypeId.CORRUPTOR).amount + bot.already_pending(UnitTypeId.CORRUPTOR)
        broodlord_count = bot.units(UnitTypeId.BROODLORD).amount + bot.already_pending(UnitTypeId.BROODLORD)
        if (corruptor_count + broodlord_count) * 4 < 0.33 * bot.supply_army:
            if bot.can_afford(UnitTypeId.CORRUPTOR):
                bot.train(UnitTypeId.CORRUPTOR)
            else:
                saving_money = True

    # Banelings
    if not saving_money and bot.structures(UnitTypeId.BANELINGNEST).ready.amount > 0:
        zerglings = bot.units(UnitTypeId.ZERGLING)
        # Keep 66/33 ling-bane ratio
        if bot.can_afford(UnitTypeId.BANELING) and zerglings.amount > 2 *bot.units({UnitTypeId.BANELING, UnitTypeId.BANELINGCOCOON}).amount:
            zerglings.closest_to(bot.start_location)(AbilityId.MORPHZERGLINGTOBANELING_BANELING)

    # Roaches
    if not saving_money and bot.structures(UnitTypeId.ROACHWARREN).ready.amount > 0:
        if bot.can_afford(UnitTypeId.ROACH):
            bot.train(UnitTypeId.ROACH)

    # Zerglings
    if not saving_money and can_afford_unit_while_saving(bot, UnitTypeId.ZERGLING) and bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount > 0:
        bot.train(UnitTypeId.ZERGLING)

async def execute_tech_coroutines(bot: BotAI, techs: List[Coroutine]):
    tech.saving_money = False

    for coroutine in techs:
        await coroutine

def reset_saving():
    global saving_money
    saving_money = False
    tech.saving_money = False
    tech.reset_amount_to_save()

def can_afford_while_saving(bot: BotAI, cost: Cost):
    max_saving = min(tech.minerals_to_save, tech.gas_to_save)

    extra_minerals = max(bot.minerals - max_saving, 0)
    extra_gas = max(bot.vespene - max_saving, 0)

    # if extra_minerals < cost.minerals:
    #     global saving_money
    #     saving_money = True
    #     return False
    # return True

    return cost.minerals <= extra_minerals and cost.vespene <= extra_gas

def can_afford_unit_while_saving(bot: BotAI, unit: UnitTypeId):
    return can_afford_while_saving(bot, bot.calculate_cost(unit))