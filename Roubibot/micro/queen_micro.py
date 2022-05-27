import random

import numpy as np

from helpers import color_map
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

bot: BotAI

def queen_routine(iteration: int):
    assign_inject_queens()
    defend()
    inject()
    spread_creep(iteration)

base_queen_pairs = {}

def assign_inject_queens():
    global base_queen_pairs

    # Delete dead bases
    for registered_base_tag in base_queen_pairs.keys():
        if registered_base_tag not in bot.structures.tags:
            del base_queen_pairs[registered_base_tag]
        else:
            # Delete dead queens
            if base_queen_pairs[registered_base_tag] not in bot.units.tags:
                base_queen_pairs[registered_base_tag] = None

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

all_map_points = None

def spread_creep(iteration: int):
    global all_map_points
    if all_map_points is None:
        all_map_points = get_whole_map()

    # Spread creep
    if iteration % 100 == 0:
        tumor_target_locations = []
        for point in get_whole_map():
            if is_border_of_creep(point):
                point_is_valid = True
                for base_location in bot.expansion_locations_list: # Do not spread on base locations
                    if point.distance_to(base_location) < 8:
                        point_is_valid = False
                        break
                if point_is_valid:
                    tumor_target_locations.append(point)
        random.shuffle(tumor_target_locations)

        for queen in bot.units(UnitTypeId.QUEEN):
            if queen.tag not in base_queen_pairs.values() and queen.is_idle and queen.energy >= 25:
                while len(tumor_target_locations) > 0:
                    target = tumor_target_locations.pop()
                    target_is_safe = True
                    for structure in bot.enemy_structures: # Do not bring queens close to enemy base
                        if target.distance_to(structure) < 20:
                            target_is_safe = False
                            break
                    if target_is_safe:
                        if not queen.is_attacking:
                            queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, target)
                        break

        tumors = bot.structures(UnitTypeId.CREEPTUMORBURROWED)
        for tumor in tumors:
            if len(tumor_target_locations) > 0:
                for tile in tumor_target_locations:
                    if tumor.distance_to(tile) <= 10:
                        tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, tile)
                        break

def is_border_of_creep(position: Point2):
    if bot.has_creep(position):
        for neighbor_tile in position.neighbors8:
            if not bot.has_creep(neighbor_tile) and bot.in_placement_grid(neighbor_tile):
                return True
    return False

def get_whole_map():
    map_area = bot.game_info.playable_area
    points = [
        Point2((a, b)) for (b, a), value in np.ndenumerate(bot.game_info.pathing_grid.data_numpy)
        if value == 1 and map_area.x <= a < map_area.x + map_area.width and map_area.y <= b < map_area.y + map_area.height
    ]
    # bool_map = [[0 for y in range(map_area.height)] for x in range(map_area.width)]
    # for point in points:
    #     bool_map[point.x - map_area.x][point.y - map_area.y] = 1
    # color_map.color_map(bool_map)
    return points
