from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

saving_money = False

async def try_build_tech(bot: BotAI, building_id: UnitTypeId, count = 1):
    global saving_money
    if not saving_money:
        if bot.structures(building_id).amount + bot.already_pending(building_id) < count:
            if bot.can_afford(building_id):
                await bot.build(building_id, near=bot.townhalls.closest_to(bot.start_location).position.towards(
                    bot.game_info.map_center, 7))
            else:
                saving_money = True

async def try_queue_research(bot: BotAI, structure_id: UnitTypeId, upgrade_id: UpgradeId):
    global saving_money
    if not saving_money:
        if upgrade_id not in bot.state.upgrades and not bot.already_pending_upgrade(upgrade_id):
            idle_structures = bot.structures(structure_id).idle
            if idle_structures.amount > 0:
                if bot.can_afford(upgrade_id):
                    idle_structures.first.research(upgrade_id)
                else:
                    saving_money = True

def is_lair_tech_unlocked(bot: BotAI):
    return bot.structures(UnitTypeId.LAIR).ready.amount + bot.structures(
        UnitTypeId.HIVE).ready.amount > 0

def is_hive_tech_unlocked(bot: BotAI):
    return bot.structures(UnitTypeId.HIVE).ready.amount > 0

async def tech_lair(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.LAIR).amount > 0:
        return

    if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
        starting_base = bot.townhalls.closest_to(bot.start_location)
        if starting_base.is_idle:
            if bot.can_afford(UnitTypeId.LAIR):
                starting_base.train(UnitTypeId.LAIR)
            else:
                saving_money = True
    else:
        await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)

async def tech_hive(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.HIVE).amount > 0:
        return

    lairs = bot.structures(UnitTypeId.LAIR)
    if lairs.amount > 0:
        if lairs.ready.amount > 0:
            if bot.structures(UnitTypeId.INFESTATIONPIT).amount > 0:
                lair = lairs.first
                if lair.is_idle:
                    if bot.can_afford(UnitTypeId.HIVE):
                        lair.train(UnitTypeId.HIVE)
                    else:
                        saving_money = True
            else:
                await try_build_tech(bot, UnitTypeId.INFESTATIONPIT)
    else:
        await tech_lair(bot)

async def tech_melee(bot: BotAI):
    if UpgradeId.ZERGMELEEWEAPONSLEVEL3 not in bot.state.upgrades:
        if UpgradeId.ZERGMELEEWEAPONSLEVEL2 not in bot.state.upgrades:
            if UpgradeId.ZERGMELEEWEAPONSLEVEL1 not in bot.state.upgrades:
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL1)
            else:
                if is_lair_tech_unlocked(bot):
                    await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL2)
        else:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL3)

async def tech_ground_armor(bot: BotAI):
    if UpgradeId.ZERGGROUNDARMORSLEVEL3 not in bot.state.upgrades:
        if UpgradeId.ZERGGROUNDARMORSLEVEL2 not in bot.state.upgrades:
            if UpgradeId.ZERGGROUNDARMORSLEVEL1 not in bot.state.upgrades:
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL1)
            else:
                if is_lair_tech_unlocked(bot):
                    await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL2)
        else:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL3)

async def tech_zerglings(bot: BotAI, adrenal_glands = False):
    if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
        await try_queue_research(bot, UnitTypeId.SPAWNINGPOOL, UpgradeId.ZERGLINGMOVEMENTSPEED)
        if adrenal_glands:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.SPAWNINGPOOL, UpgradeId.ZERGLINGATTACKSPEED)
            else:
                await tech_hive(bot)
    else:
        await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)

async def tech_banelings(bot: BotAI):
    if bot.structures(UnitTypeId.BANELINGNEST).amount > 0:
        if is_lair_tech_unlocked(bot):
            await try_queue_research(bot, UnitTypeId.BANELINGNEST, UpgradeId.CENTRIFICALHOOKS)
        else:
            await tech_lair(bot)
    else:
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            await try_build_tech(bot, UnitTypeId.BANELINGNEST)
        else:
            await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)

async def tech_roaches(bot: BotAI, tunneling_claws = False):
    if bot.structures(UnitTypeId.ROACHWARREN).amount > 0:
        if is_lair_tech_unlocked(bot):
            await try_queue_research(bot, UnitTypeId.ROACHWARREN, UpgradeId.GLIALRECONSTITUTION)
            if tunneling_claws:
                await try_queue_research(bot, UnitTypeId.ROACHWARREN, UpgradeId.TUNNELINGCLAWS)
                await try_queue_research(bot, UnitTypeId.HATCHERY, UpgradeId.BURROW)
        else:
            await tech_lair(bot)
    else:
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            await try_build_tech(bot, UnitTypeId.ROACHWARREN)
        else:
            await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)

async def tech_spire(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.SPIRE).amount + bot.structures(UnitTypeId.GREATERSPIRE).amount < 1:
        if is_lair_tech_unlocked(bot):
            await try_build_tech(bot, UnitTypeId.SPIRE)
        else:
            await tech_lair(bot)


async def tech_broodlords(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.GREATERSPIRE).amount > 0:
        return

    spires = bot.structures(UnitTypeId.SPIRE)
    if spires.amount > 0:
        if is_hive_tech_unlocked(bot):
            idle_spires = spires.ready.idle
            if idle_spires.amount > 0:
                if bot.can_afford(UnitTypeId.GREATERSPIRE):
                    idle_spires.first.train(UnitTypeId.GREATERSPIRE)
                else:
                    saving_money = True
        else:
            await tech_hive(bot)
    else:
        if is_lair_tech_unlocked(bot):
            await try_build_tech(bot, UnitTypeId.SPIRE)
        else:
            await tech_lair(bot)

async def tech_ultralisks(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.ULTRALISKCAVERN).amount > 0:
        await try_queue_research(bot, UnitTypeId.ULTRALISKCAVERN, UpgradeId.CHITINOUSPLATING)
    else:
        if is_hive_tech_unlocked(bot):
            if bot.can_afford(UnitTypeId.ULTRALISKCAVERN):
                await try_build_tech(bot, UnitTypeId.ULTRALISKCAVERN)
            else:
                saving_money = True
        else:
            await tech_hive(bot)
