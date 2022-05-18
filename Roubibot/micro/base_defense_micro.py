from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId


def emergency_response(bot: BotAI):
    threats = []
    for enemy in bot.enemy_units:
        if enemy.is_attacking:
            threats.append(enemy)
            continue
        for base in bot.townhalls:
            if base.health_percentage < 1:
                if enemy.distance_to(base) < 20:
                    threats.append(enemy)
                    break

    if len(threats) == 0:
        return

    for unit in bot.units.exclude_type(UnitTypeId.OVERLORD):
        if not unit.is_attacking:
            if unit.type_id == UnitTypeId.DRONE:
                for enemy in threats:
                    if unit.distance_to(enemy) < 5:
                        unit.attack(enemy.position)
                        break
            elif unit.type_id == UnitTypeId.QUEEN:
                for enemy in threats:
                    if unit.distance_to(enemy) < 20:
                        unit.attack(enemy.position)
                        break
            else:
                closest_enemy = threats[0]
                for enemy in threats:
                    if enemy.distance_to(unit) < closest_enemy.distance_to(unit):
                        closest_enemy = enemy
                unit.attack(closest_enemy.position)
        else:
            if unit.type_id == UnitTypeId.DRONE:
                # Prevent drones form chasing enemies
                closest_townhall = bot.townhalls.closest_to(unit)
                if closest_townhall.distance_to(unit) > 15:
                    unit.move(closest_townhall)
