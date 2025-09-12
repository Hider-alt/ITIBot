import datetime

from discord.ext import tasks
from discord.ext.commands import Cog

from src.loops.new_year.create_variations_channels import create_variations_channels
from src.loops.new_year.notify_roles_upgrade import notify_roles_upgrade
from src.loops.new_year.send_analytics import send_analytics_recap, send_analytics_selection
from src.loops.new_year.send_new_class_selection import send_new_class_selection
from src.loops.new_year.upgrade_roles import upgrade_roles
from src.mongo_db.config_db import ConfigDB
from src.utils.discord_utils import delete_last_message


async def setup(bot):
    await bot.add_cog(YearlyLoops(bot))


class YearlyLoops(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.new_year_date = datetime.datetime(datetime.datetime.now().year, 9, 10, 23, 59, 59)
        self.new_year.start()

    # Run every year on 12/09
    @tasks.loop(hours=24)
    async def new_year(self):
        now = datetime.datetime.now()

        if now > self.new_year_date:
            self.new_year_date = self.new_year_date.replace(year=now.year + 1)

        if now.date() != self.new_year_date.date():
            return

        print(f"[{now}] Creating and setting up new classes for the new school year")

        # 1 - Upgrade roles

        current_roles: set[str] = await upgrade_roles(self.bot)
        if current_roles is None:
            print("Failed to get new year classes, retrying tomorrow")

            self.new_year_date = self.new_year_date + datetime.timedelta(days=1)  # Try again tomorrow
            return

        await notify_roles_upgrade(self.bot)

        print(f"[{now}] Roles upgraded successfully")

        # 2 - Create new classes channels and send selection message

        await delete_last_message(self.bot.select_channel)

        grouped_classes = await send_new_class_selection(self.bot.select_channel, current_roles)

        config_db = ConfigDB(self.bot.mongo_client)
        await config_db.set_classes(grouped_classes)

        await create_variations_channels(self.bot, grouped_classes)
        print(f"[{now}] New classes created and set up successfully")

        # 3 - Send analytics recap and selection

        await delete_last_message(self.bot.analytics_channel)

        await send_analytics_recap(self.bot)

        await send_analytics_selection(self.bot)

        # 4 - Update school year in bot and DB

        await self.bot.upgrade_school_year()

        print(f"[{now}] School year updated to {self.bot.school_year} successfully")

    @new_year.before_loop
    async def before_new_year(self):
        await self.bot.wait_until_ready()
