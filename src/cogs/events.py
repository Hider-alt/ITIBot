import calendar
from datetime import datetime, timedelta, time

import discord
import pytz
from discord.ext import tasks
from discord.ext.commands import Cog

from src.commands.loops.check_variations import refresh_variations
from src.mongo_repository.variations import Variations
from src.utils.datetime_utils import is_christmas, is_summer


async def setup(bot):
    await bot.add_cog(Events(bot))


class Events(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_variations_loop.start()
        self.check_variations_sent.start()

    @tasks.loop(minutes=15)
    async def check_variations_loop(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        if 0 < now.hour < 6:
            print(f"[{now}] Skipping Variations Check (0 < now hour < 6)")
            return

        if is_christmas(now) or is_summer(now):
            print(f"[{now}] Skipping Variations Check (Festivities)")
            return

        print(f"[{now}] Checking Variations")
        await refresh_variations(self.bot)

    # Check every day at 20:00 if variations have been detected for the next day
    @tasks.loop(time=time(20, 0, 0))
    async def check_variations_sent(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        # Skip if tomorrow is a Sunday (there are no variations on Sundays)
        if now.weekday() + 1 == calendar.SUNDAY:
            print(f"[{now}] Skipping Variations Sent Check (Sunday)")
            return

        # Skip festivities
        if is_christmas(now) or is_summer(now):
            print(f"[{now}] Skipping Variations Sent Check (Festivities)")
            return

        print(f"[{now}] Checking Variations Sent")

        now += timedelta(days=1)

        db = Variations(self.bot.mongo_client)
        tomorrow_var = await db.get_variations_by_date(now.strftime("%d-%m-%Y"))

        if not tomorrow_var:
            embed = discord.Embed(
                title="Sembrano non esserci variazioni per domani...",
                description="Controlla manualmente [nel sito](https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/) per sicurezza!",
                color=discord.Color.red()
            )

            await self.bot.log_channel.send(embed=embed, content="@everyone")
