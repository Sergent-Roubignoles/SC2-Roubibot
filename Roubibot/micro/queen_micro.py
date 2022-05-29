import random

import numpy as np

from helpers import color_map
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

bot: BotAI

async def queen_routine(iteration: int):
    assign_inject_queens()
    defend()
    inject()
    await spread_creep(iteration)

base_queen_pairs = {}

def assign_inject_queens():
    global base_queen_pairs

    # Delete dead bases
    base_tags_to_delete = []
    for registered_base_tag in base_queen_pairs.keys():
        if registered_base_tag not in bot.structures.tags:
            base_tags_to_delete.append(registered_base_tag)
        else:
            # Delete dead queens
            if base_queen_pairs[registered_base_tag] not in bot.units.tags:
                base_queen_pairs[registered_base_tag] = None
    for tag in base_tags_to_delete:
        del base_queen_pairs[tag]

    unreserved_queens = bot.units(UnitTypeId.QUEEN).filter(lambda unit: unit.tag not in base_queen_pairs.values())

    for base in bot.townhalls:
        # Add new bases
        if base.tag not in base_queen_pairs.keys():
            base_queen_pairs[base.tag] = None
        # Add queens to bases without queens
        if base_queen_pairs[base.tag] is None and unreserved_queens.amount > 0:
            closest_queen = unreserved_queens.closest_to(base)
            unreserved_queens.remove(closest_queen)
            base_queen_pairs[base.tag] = closest_queen.tag

def defend():
    for queen in bot.units(UnitTypeId.QUEEN):
        threatening_queen = bot.enemy_units.filter(lambda e: e.target_in_range(queen))
        if threatening_queen.amount > 0:
            closest_threat = threatening_queen.closest_to(queen)
            queen.attack(closest_threat.position)

def inject():
    # Get inject queens
    inject_queens = []
    for queen in bot.units(UnitTypeId.QUEEN):
        if queen.tag in base_queen_pairs.values():
            inject_queens.append(queen)

    # Inject if necessary
    for base in bot.townhalls.ready:
        if base.tag in base_queen_pairs.keys() and not base.has_buff(BuffId.QUEENSPAWNLARVATIMER):
            # Find inject queen
            inject_queen_tag = base_queen_pairs[base.tag]
            if inject_queen_tag is not None:
                for queen in inject_queens:
                    if queen.tag == inject_queen_tag:
                        # Inject
                        if not queen.is_attacking and queen.energy >= 25:
                            queen(AbilityId.EFFECT_INJECTLARVA, base)
                        break

tumor_points = []

def find_tumor_points():
    global tumor_points
    if len(tumor_points) > 0:
        return

    # Get all points
    map_area = bot.game_info.playable_area
    all_map_points = [
        Point2((a, b)) for (b, a), value in np.ndenumerate(bot.game_info.pathing_grid.data_numpy)
        if value == 1 and map_area.x <= a < map_area.x + map_area.width and map_area.y <= b < map_area.y + map_area.height
    ]

    # Create tumor grid
    tumor_points = []
    for point in all_map_points:
        if (point.x % 16 == 0 and point.y % 8 == 0) or (point.x % 16 == 8 and point.y % 8 == 4):
            # Do not place on base locations
            close_to_base = False
            for base in bot.expansion_locations_list:
                if point.distance_to(base) < 5:
                    close_to_base = True
                    break
            if not close_to_base:
                tumor_points.append(point)

    # Draw tumor points
    # bool_map = [[0 for y in range(map_area.height)] for x in range(map_area.width)]
    # for point in all_map_points:
    #     bool_map[point.x - map_area.x][point.y - map_area.y] = 1
    # for point in tumor_points:
    #     bool_map[point.x - map_area.x][point.y - map_area.y] = 10
    # color_map.color_map(bool_map)

async def spread_creep(iteration: int):
    if iteration % 10 == 0:
        find_tumor_points()
        placable_tumor_points = []
        for point in tumor_points:
            if bot.has_creep(point) and bot.in_placement_grid(point):
                placable_tumor_points.append(point)

        for queen in bot.units(UnitTypeId.QUEEN):
            if queen.tag not in base_queen_pairs.values() and queen.is_idle and queen.energy >= 25:
                # Find all valid points close to queen
                valid_targets = []
                for point in placable_tumor_points:
                    if point.distance_to(queen.position) < 30:
                        if await bot.can_place_single(AbilityId.BUILD_CREEPTUMOR_QUEEN, point):
                            valid_targets.append(point)

                # Pick point that is closest to enemy
                if len(valid_targets) > 0:
                    closest_to_enemy = valid_targets.pop()
                    enemy_pos = bot.enemy_start_locations[0]
                    for target in valid_targets:
                        if enemy_pos.distance_to(target) < enemy_pos.distance_to(closest_to_enemy):
                            closest_to_enemy = target
                    queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, closest_to_enemy)
                    break

        tumors = bot.structures(UnitTypeId.CREEPTUMORBURROWED)
        for tumor in tumors:
            for point in placable_tumor_points:
                if bot.has_creep(point):
                    distance = point.distance_to(tumor.position)
                    if 3 < distance < 10:
                        if await bot.can_place_single(AbilityId.BUILD_CREEPTUMOR_TUMOR, point):
                            tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, point)
                            break
