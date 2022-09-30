from macro import economy
from micro.army_group import AttackGroup
from micro.groups.ling_flood import LingFlood
from routines import army_group_routine
from sc2.ids.unit_typeid import UnitTypeId
from sc2.bot_ai import BotAI
from strategies.safe_35_drone import Safe35Drone
from strategies.strategy import Strategy


class TwelvePool(Strategy):
    scout_sent = False
    bot = None

    async def on_step(self, bot: BotAI):
        if self.bot is None:
            self.bot = bot

        await bot.distribute_workers()

        # Tech pool first
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount + bot.already_pending(UnitTypeId.SPAWNINGPOOL) < 1:
            await economy.tech.try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)
            if economy.tech.saving_money:
                return # Save for spawning pool
        else:
            if bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount > 0:

                # Keep min. 2 free supply
                if bot.supply_left < 2 and bot.already_pending(UnitTypeId.OVERLORD) < 1:
                    if bot.can_afford(UnitTypeId.OVERLORD):
                        bot.train(UnitTypeId.OVERLORD)
                    else:
                        return # Save for overlord

                # Build 12 lings
                zerglings = bot.units(UnitTypeId.ZERGLING)
                if zerglings.amount < 12:
                    for larva in bot.larva:
                        larva.train(UnitTypeId.ZERGLING)
                else:
                    # Attack
                    zergling_group: LingFlood = LingFlood()
                    for zergling in zerglings:
                        zergling_group.attacker_tags.append(zergling.tag)
                    zergling_group.target = bot.enemy_start_locations[0]

                    army_group_routine.army_groups.append(zergling_group)
                    self.is_finished = True

                # Queen if floating
                if bot.units(UnitTypeId.QUEEN).amount + bot.already_pending(UnitTypeId.QUEEN) < 1:
                    bot.train(UnitTypeId.QUEEN)

                # B2 if floating
                if bot.townhalls.amount + bot.already_pending(UnitTypeId.HATCHERY) < 2:
                    next_expansion = await bot.get_next_expansion()
                    if next_expansion is not None:
                        if bot.can_afford(UnitTypeId.HATCHERY):
                            await bot.build(UnitTypeId.HATCHERY, next_expansion)

            else: # While pool finishes

                # Get 2 drones
                if bot.workers.amount < 13:
                    bot.train(UnitTypeId.DRONE)

                # Then 1 overlord
                else:
                    if bot.supply_left < 5 and bot.already_pending(UnitTypeId.OVERLORD) < 1:
                        bot.train(UnitTypeId.OVERLORD)

    def prefered_follow_up_strategy(self) -> Strategy:
        return Safe35Drone()