import calendar
from datetime import datetime, timedelta, time

import discord
import pytz
from discord.ext import tasks
from discord.ext.commands import Cog

from src.commands.loops.check_variations.variations import refresh_variations
from src.mongo_repository.variations_db import VariationsDB
from src.utils.datetime_utils import is_christmas, is_summer


async def setup(bot):
    await bot.add_cog(DailyLoops(bot))


class DailyLoops(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.loops_controller.start()

    @tasks.loop(hours=12)
    async def loops_controller(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        # Stop loops during festivities or summer
        if is_christmas(now) or is_summer(now):
            print(f"Stopping loops for festivities ({now})")

            if self.check_variations.is_running():
                print("Stopping Variations Check")
                self.check_variations.stop()

            if self.check_variations_sent.is_running():
                print("Stopping Variations Sent Check")
                self.check_variations_sent.stop()

        elif not self.check_variations.is_running():
            print(f"Starting Variations Check ({now})")
            self.check_variations.start()

        elif not self.check_variations_sent.is_running():
            print(f"Starting Variations Sent Check ({now})")
            self.check_variations_sent.start()

    @tasks.loop(minutes=15)
    async def check_variations(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        if 0 < now.hour < 6:
            print(f"[{now}] Skipping Variations Check (0 < now hour < 6)")
            return

        print(f"[{now}] Checking Variations")
        await refresh_variations(self.bot)

    # Check every day at 20:00 if check_variations have been detected for the next day
    @tasks.loop(time=time(20))
    async def check_variations_sent(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))
        tomorrow = now + timedelta(days=1)

        # Skip if tomorrow is a Sunday (there are no check_variations on Sundays)
        if tomorrow.weekday() == calendar.SUNDAY:
            print(f"[{now}] Skipping Variations Sent Check (Sunday)")
            return

        print(f"[{now}] Checking Variations Sent")

        db = VariationsDB(self.bot.mongo_client)
        tomorrow_var = await db.get_variations_by_date(tomorrow.strftime("%d-%m-%Y"))

        if not tomorrow_var:
            embed = discord.Embed(
                title="Sembrano non esserci variazioni per domani...",
                description="Controlla manualmente [nel sito](https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/) per sicurezza!",
                color=discord.Color.red()
            )

            await self.bot.log_channel.send(embed=embed, content="@everyone")

    @loops_controller.before_loop
    async def before_loops_controller(self):
        await self.bot.wait_until_ready()
