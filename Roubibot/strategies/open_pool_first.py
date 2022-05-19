from helpers import strategy_analyser, base_identifier
from helpers.unit_selector import amount_of_type
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .early_ling_push import EarlyLingPush
from .strategy import Strategy


class OpenPoolFirst(Strategy):
    finished = False
    scout_sent = False

    async def on_step(self, bot: BotAI):
        await bot.distribute_workers()

        # Train overlords
        if bot.supply_left <= 1 and bot.already_pending(UnitTypeId.OVERLORD) == 0:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        # Get 17 drones
        if amount_of_type(bot, UnitTypeId.ZERGLING) < 17:
            if not bot.can_afford(UnitTypeId.DRONE):
                return
            bot.train(UnitTypeId.DRONE)

        economy.reset_saving()
        # Tech pool first
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount + bot.already_pending(UnitTypeId.SPAWNINGPOOL) < 1:
            await economy.tech.try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)
            if economy.tech.saving_money:
                return # Save for spawning pool

        # Then hatch
        if bot.townhalls.amount + bot.already_pending(UnitTypeId.HATCHERY) < 2:
            next_expansion = await bot.get_next_expansion()
            if next_expansion is not None:
                if bot.can_afford(UnitTypeId.HATCHERY):
                    # Drone scout
                    if not self.scout_sent:
                        scout = bot.workers.gathering.first
                        scout.move(bot.enemy_start_locations[0])
                        scout.move(base_identifier.enemy_natural, queue=True)
                        scout.hold_position(queue=True)
                        self.scout_sent = True
                    await bot.build(UnitTypeId.HATCHERY, next_expansion)
                else:
                    return # Save for hatchery

        # Then gas
        await economy.get_gas(bot, 1)
        if bot.structures(UnitTypeId.EXTRACTOR).amount > 0:
            self.is_finished = True

    def prefered_follow_up_strategy(self) -> Strategy:
        return EarlyLingPush()