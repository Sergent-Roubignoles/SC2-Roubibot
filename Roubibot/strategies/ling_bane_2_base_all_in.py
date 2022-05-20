from helpers import strategy_analyser, base_identifier
from helpers.unit_selector import amount_of_type
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .safe_35_drone import Safe35Drone
from .strategy import Strategy


class LingBane2BaseAllIn(Strategy):
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
        army = bot.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.BANELING})
        if army.amount >= 6:
            for unit in army:
                unit.attack(bot.enemy_start_locations[0])

        if army.amount > 30:
            self.is_finished = True


    def prefered_follow_up_strategy(self) -> Strategy:
        return Safe35Drone()