from micro.army_group import AttackGroup
from routines import routine_manager
from sc2.ids.unit_typeid import UnitTypeId
from unit import Unit


class LingFlood(AttackGroup):
    ling_tags_with_orders: [int]
    #enemy_ling_dict = {}

    def attack(self):
        # TODO: Declare these lists as empty, then add each unit as they are filtered
        enemy_units = routine_manager.bot.enemy_units.filter(lambda unit: unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE} and not unit.is_flying)
        enemy_structures = routine_manager.bot.enemy_structures
        enemy_workers = routine_manager.bot.enemy_units.filter(lambda unit: unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE})

        self.update_attacker_list()

        enemy_dict = {}
        for enemy in routine_manager.bot.all_enemy_units:
            enemy_dict[enemy] = set()

        for ling in self.attackers:
            target: Unit = None
            if isinstance(ling.order_target, int):
                try:
                    target = routine_manager.bot.all_units.by_tag(ling.order_target)
                    enemy_dict[target].add(ling)
                except KeyError:
                    pass
            # Maybe find new target

        lings_without_orders: [Unit] = []
        for ling in self.attackers:
            if not ling.is_attacking:
                lings_without_orders.append(ling)

        if len(lings_without_orders) > 0:
            for ling in lings_without_orders:
                if enemy_units.amount > 0:
                    # Kill army
                    ling.attack(enemy_units.closest_to(ling))
                    continue
                if enemy_workers.amount > 0:
                    # Kill workers
                    ling.attack(enemy_workers.closest_to(ling))
                    continue
                # Move to enemy main
                ling.move(routine_manager.bot.enemy_start_locations[0])