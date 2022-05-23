from sc2.position import Point2
from sc2.unit import Unit
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .safe_35_drone import Safe35Drone
from .strategy import Strategy


class ArmyGroup:
    def __init__(self, bot: BotAI):
        self.bot = bot

        self.unit_tags = []
        self.units: list[Unit] = []
        self.position: Point2 = None
        self.target: Point2 = None
        self.is_regrouping = False
        self.is_retreating = False


    def verify_units(self):
        self.units.clear()
        for tag in self.unit_tags:
            try:
                unit = self.bot.units.by_tag(tag)
                self.units.append(unit)
            except KeyError:
                self.unit_tags.remove(tag)

        if len(self.units) > 0:
            self.position = self.units[0].position

    def add_unit(self, unit: Unit):
        self.unit_tags.append(unit.tag)

    def average_distance(self):
        total_distance = 0
        for unit in self.units:
            total_distance += unit.distance_to(self.position)

        return total_distance / len(self.unit_tags)

    def attack(self):
        # Regroup if needed
        av_dist = self.average_distance()
        if self.is_regrouping:
            if av_dist < 7: # End regrouping and continue
                self.is_regrouping = False
            else: # Stop and keep regrouping
                return
        else:
            if av_dist > 15: # Stop and regroup
                self.regroup()
                return

        # Attack target
        self.is_retreating = False
        destination = self.target
        risk = self.analyze_risk()
        if risk > 1.5:
            self.is_retreating = True
            destination = self.bot.start_location

        # TODO: Split retreat and attack

        # for unit in self.units:
        #     if unit.weapon_ready:
        #         unit.attack(destination)
        #     else:
        #         unit.move(destination)

    # Returns nearby enemies value / group value
    def analyze_risk(self):
        own_value = 0
        for unit in self.units:
            unit_value = self.bot.calculate_unit_value(unit.type_id)
            own_value += unit_value.minerals + unit_value.vespene

        enemy_value = 0
        for unit in self.bot.enemy_units:
            if unit.distance_to(self.position) > 15:
                continue
            unit_value = self.bot.calculate_unit_value(unit.type_id)
            enemy_value += unit_value.minerals + unit_value.vespene

        return enemy_value / own_value

    def regroup(self):
        if not self.is_regrouping:
            self.is_regrouping = True

            # Get central position
            positions: list[Point2] = []
            for unit in self.units:
                positions.append(unit.position)
            total_x = 0
            total_y = 0
            for pos in positions:
                total_x += pos.x
                total_y += pos.y
            self.position = Point2((total_x / len(positions), total_y / len(positions)))

            # Move to central position
            for unit in self.units:
                unit.move(self.position)

    def move(self, destination: Point2):
        for unit in self.units:
            unit.move(destination)


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

        # Attack or rally
        rally_point = bot.townhalls.closest_to(bot.game_info.map_center).position
        groups_at_rally_point = []

        for group in self.army_groups:
            group.verify_units()
            if len(group.unit_tags) > 5:
                group.attack()
            else:
                if group.is_retreating:
                    if group.position.distance_to(rally_point) > 10:
                        group.move(rally_point)
                    else:
                        groups_at_rally_point.append(group)

        if len(groups_at_rally_point) > 1:
            unified_army_group = ArmyGroup(bot)
            unified_army_group.target = groups_at_rally_point[0].target
            unified_army_group.position = groups_at_rally_point[0].position

            for group in groups_at_rally_point:
                for tag in group.unit_tags:
                    unified_army_group.unit_tags.append(tag)
                self.army_groups.remove(group)

            self.army_groups.append(unified_army_group)

        # Transition to late game if large army advantage
        # if army.amount > 30:
        #     self.is_finished = True

    def prefered_follow_up_strategy(self) -> Strategy:
        return Safe35Drone()