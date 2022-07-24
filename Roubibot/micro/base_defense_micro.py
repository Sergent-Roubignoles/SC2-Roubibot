from sc2.units import Units

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

ground_threats: Units
air_threats: Units

def defense_routine(bot: BotAI):
    global ground_threats
    global air_threats

    ground_threats = bot.enemy_units.filter(lambda enemy: not enemy.is_flying)
    air_threats = bot.enemy_units.filter(lambda enemy: enemy.is_flying)

    drone_self_defense(bot)


def drone_self_defense(bot: BotAI):
    if ground_threats.amount > 0:
        for drone in bot.workers:
            closest_threat = ground_threats.closest_to(drone)

            # Can threat can attack drone?
            if closest_threat.distance_to(drone) < closest_threat.ground_range:
                # Attack only if threat is close to a base
                townhalls = bot.townhalls
                if townhalls.amount > 0:
                    closest_townhall = townhalls.closest_to(drone)
                    if closest_threat.distance_to(closest_townhall) > 12:
                        # Prevent drone from chasing threat
                        drone.move(closest_townhall.position)
                        continue

                drone.attack(closest_threat.position)
            else:
                continue # Drones should only attack units that are threatening them
