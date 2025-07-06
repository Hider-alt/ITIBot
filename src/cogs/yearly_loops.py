import datetime

from discord.ext import tasks
from discord.ext.commands import Cog

from src.commands.loops.new_year.create_variations_channels import create_variations_channels
from src.commands.loops.new_year.send_new_class_selection import send_new_class_selection
from src.commands.loops.new_year.upgrade_roles import upgrade_roles
from src.mongo_repository.config_db import ConfigDB


async def setup(bot):
    await bot.add_cog(DailyLoops(bot))


class DailyLoops(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.new_year_date = datetime.datetime(datetime.datetime.now().year, 9, 12)
        self.new_year.start()

    # Run every year on 12/09
    @tasks.loop(hours=24)
    async def new_year(self):    # TODO: test
        now = datetime.datetime.now()

        if now > self.new_year_date:
            self.new_year_date = datetime.datetime(now.year + 1, 9, 12)

        if now.date() != self.new_year_date.date():
            return

        current_roles: list[str] = await upgrade_roles(self.bot)

        grouped_classes = await send_new_class_selection(self.bot.select_channel, current_roles)

        await create_variations_channels(self.bot, grouped_classes)

        config_db = ConfigDB(self.bot.mongo_client)
        await config_db.set_classes(grouped_classes)
