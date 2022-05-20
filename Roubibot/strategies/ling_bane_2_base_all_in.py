from sc2.position import Point2
from sc2.unit import Unit

from helpers import strategy_analyser, base_identifier
from helpers.unit_selector import amount_of_type
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .safe_35_drone import Safe35Drone
from .strategy import Strategy


class ArmyGroup:
    bot: BotAI
    unit_tags = []

    position: Point2
    target: Point2
    is_regrouping = False

    def __init__(self, bot: BotAI):
        self.bot = bot

    def verify_units(self):
        first_unit = None
        for tag in self.unit_tags:
            try:
                unit = self.bot.units.by_tag(tag)
                if first_unit is None:
                    first_unit = unit
            except KeyError:
                self.unit_tags.remove(tag)

        if first_unit is not None:
            self.position = first_unit.position

    def add_unit(self, unit: Unit):
        self.unit_tags.append(unit.tag)

    def average_distance(self):
        total_distance = 0
        for tag in self.unit_tags:
            try:
                unit = self.bot.units.by_tag(tag)
                total_distance += unit.distance_to(self.position)
            except KeyError:
                self.unit_tags.remove(tag)

        return total_distance / len(self.unit_tags)

    def attack(self):
        av_dist = self.average_distance()
        if self.is_regrouping and av_dist < 7:
            if av_dist < 7:
                self.is_regrouping = False
            else:
                return
        if not self.is_regrouping and av_dist > 15:
            self.regroup()
            return

        for tag in self.unit_tags:
            try:
                unit = self.bot.units.by_tag(tag)
                unit.attack(self.target.position)
            except KeyError:
                self.unit_tags.remove(tag)

    def regroup(self):
        if not self.is_regrouping:
            self.is_regrouping = True

            # Get central position
            positions: list[Point2] = []
            for tag in self.unit_tags:
                try:
                    unit = self.bot.units.by_tag(tag)
                    positions.append(unit.position)
                except KeyError:
                    self.unit_tags.remove(tag)
            total_x = 0
            total_y = 0
            for pos in positions:
                total_x += pos.x
                total_y += pos.y
            self.position = Point2((total_x / len(positions), total_y / len(positions)))

            # Move to central position
            for tag in self.unit_tags:
                try:
                    unit = self.bot.units.by_tag(tag)
                    unit.attack(self.position)
                except KeyError:
                    self.unit_tags.remove(tag)


class LingBane2BaseAllIn(Strategy):
    army_groups: list[ArmyGroup] = []

    async def on_step(self, bot: BotAI):
        # Train overlords
        if bot.supply_left <= 4 and bot.already_pending(UnitTypeId.OVERLORD) == 0:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        economy.reset_saving()

        # Tech
        desired_techs = [economy.tech.tech_zerglings(bot)]
        await economy.execute_tech_coroutines(bot, desired_techs)

        # 19 drones
        await economy.expand_eco(bot, 19, 1)

        # Army
        await economy.expand_army(bot)

        # Get baneling nest if out of larva
        if bot.larva.amount == 0:
            await economy.tech.tech_banelings(bot)

        # Attack
        for group in self.army_groups:
            group.verify_units()
            if len(group.unit_tags) > 5:
                group.attack()
            else:
                group.regroup()

        army = bot.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.BANELING})
        # Create army groups
        for unit in army:
            # Ignore units already in a group
            unit_already_in_group = False
            for army_group in self.army_groups:
                if unit.tag in army_group.unit_tags:
                    unit_already_in_group = True
                    break

            if not unit_already_in_group:
                group_found = False
                # Find nearby group
                for group in self.army_groups:
                    if group.position.distance_to(unit) < 10:
                        group.add_unit(unit)
                        group_found = True
                        break

                # Create new group if no group found
                if not group_found:
                    new_group = ArmyGroup(bot)
                    self.army_groups.append(new_group)

                    new_group.add_unit(unit)
                    new_group.position = unit.position
                    new_group.target = bot.enemy_start_locations[0]

        # Transition to late game if large army advantage
        if army.amount > 30:
            self.is_finished = True

    def prefered_follow_up_strategy(self) -> Strategy:
        return Safe35Drone()