from datetime import datetime

import pytz
from discord.ext import tasks
from discord.ext.commands import Cog

from src.commands.loops.check_teachers import refresh_variations


async def setup(bot):
    await bot.add_cog(Events(bot))


class Events(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_variations_loop.start()

    @tasks.loop(minutes=15)
    async def check_variations_loop(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        if 0 < now.hour < 6:
            print(f"[{now}] Skipping Variations Check (0 < now hour < 6)")
            return

        print(f"[{now}] Checking Variations")
        #await refresh_variations(self.bot)
