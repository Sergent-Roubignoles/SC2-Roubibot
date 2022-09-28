import io
import json
import os.path
import random
from typing import List

from routines import routine_manager
from sc2.unit import Unit
from helpers import strategy_analyser, base_identifier
from micro import queen_micro, overlord_micro
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from strategies import strategy
from strategies.open_pool_first import OpenPoolFirst
from strategies.twelve_pool import TwelvePool

data_path = "Data\\opponents.json"

class Roubibot(BotAI):

    current_strategy = TwelvePool()
    opening_strategy: strategy

    async def on_start(self):
        print("Game started")
        base_identifier.identify_bases(self)

        overlord_micro.bot = self
        queen_micro.bot = self

        routine_manager.bot = self

        if self.opponent_id is None:
            self.opponent_id = "Unknown"

        if os.path.isfile(data_path):
            data: dict
            with open(data_path) as json_file:
                data = json.load(json_file)

            if "opponent history" in data.keys():
                if self.opponent_id in data["opponent history"].keys():
                    if TwelvePool.__name__ in data["opponent history"][self.opponent_id].keys():
                        if "Defeat" in data["opponent history"][self.opponent_id][TwelvePool.__name__]:
                            self.current_strategy = OpenPoolFirst()

        self.opening_strategy = self.current_strategy


    async def on_step(self, iteration):
        if self.townhalls.amount > 0 and self.workers.amount > 0:
            # Main code
            await strategy_analyser.update_unit_list(self)

            if self.current_strategy.is_finished:
                self.current_strategy = self.current_strategy.prefered_follow_up_strategy()
                #await self.chat_send("New strategy: " + self.current_strategy.__class__.__name__)
            await self.current_strategy.on_step(self)

            move_scout(self)
            build_emergency_workers(self)

            await queen_micro.queen_routine(iteration)
            overlord_micro.overlord_routine()

            routine_manager.execute_routines()

    def on_end(self, result):
        print("Game ended.")

        if not os.path.isfile(data_path):
            with io.open(data_path, 'w') as json_file:
                json_file.write(json.dumps({}))

        data: dict
        with open(data_path) as json_file:
            data = json.load(json_file)

        if "opponent history" not in data.keys():
            data["opponent history"] = {}

        opponent_history: dict = data["opponent history"]
        opponent_id = self.opponent_id
        if opponent_id not in opponent_history.keys():
            opponent_history[opponent_id] = {}

        strategy_history: dict = opponent_history[opponent_id]
        strategy_name = self.opening_strategy.__class__.__name__
        if strategy_name not in strategy_history.keys():
            strategy_history[strategy_name] = {}

        result_history = strategy_history[strategy_name]
        if result.name not in result_history.keys():
            result_history[result.name] = 1
        else:
            result_history[result.name] = result_history[result.name] + 1

        with io.open(data_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    async def on_unit_destroyed(self, unit_tag: int):
        strategy_analyser.on_unit_destroyed(unit_tag)

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        await overlord_micro.verify_no_hidden_units(unit)

scout_id: int = 0

def move_scout(bot: BotAI):
    global scout_id
    position_to_scout: Point2

    try:
        scout = bot.units.by_tag(scout_id)
        if scout.is_idle:
            expansions: List[Point2] = bot.expansion_locations_list
            random.shuffle(expansions)
            scout.move(expansions[0].position)
    except KeyError:
        idle_lings = bot.units(UnitTypeId.ZERGLING).idle
        if idle_lings.amount > 0:
            scout_id = idle_lings.first.tag

def build_emergency_workers(bot: BotAI):
    if bot.supply_workers < 4 and bot.can_afford(UnitTypeId.DRONE):
        safe_larva_found = False
        for larva in bot.larva:
            larva_is_safe = True
            for enemy in bot.enemy_units:
                if larva.distance_to(enemy) < 20:
                    larva_is_safe = False
                    break
            if larva_is_safe:
                safe_larva_found = True
                larva(AbilityId.LARVATRAIN_DRONE)
                break
        if not safe_larva_found:
            bot.train(UnitTypeId.DRONE)