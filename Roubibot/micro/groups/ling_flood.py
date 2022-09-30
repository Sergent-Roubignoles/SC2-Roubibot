from micro.army_group import AttackGroup
from routines import routine_manager
from sc2.ids.unit_typeid import UnitTypeId

enemies_tags_seen: [int] = []

class LingFlood(AttackGroup):
    def attack(self):
        enemy_units = routine_manager.bot.enemy_units.filter(lambda unit: unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE})
        enemy_structures = routine_manager.bot.enemy_structures
        enemy_workers = routine_manager.bot.enemy_units.filter(lambda unit: unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE})

        # TODO: Declare empty unit lists and add each unit as they are filtered

        for enemy in enemy_units:
            if enemy.is_flying:
                continue

            closest_distance = self.attackers[0].distance_to(enemy)
            for attacker in self.attackers:
                distance = attacker.distance_to(enemy)
                if distance < closest_distance:
                    closest_distance = distance

            if closest_distance < 15:
                enemy_value = routine_manager.bot.calculate_cost(enemy.type_id)
                lings_to_assign = (enemy_value.minerals + enemy_value.vespene) / 25 + 1

                # TODO: Assign attackers to this unit

        # TODO: Assign remaining lings to attack workers
