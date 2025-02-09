from datetime import datetime, timedelta, time

import discord
import pytz
from discord.ext import tasks
from discord.ext.commands import Cog

from src.commands.loops.check_variations import refresh_variations
from src.mongo_repository.variations import Variations


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
        await refresh_variations(self.bot)

    # Check every day at 20:00 if variations have been sent today
    @tasks.loop(time=time(20, 0, 0))
    async def check_variations_sent(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))

        # Skip if it's sunday
        if now.weekday() == 6:
            print(f"[{now}] Skipping Variations Sent Check (Sunday)")
            return

        # Skip festivities (from 24/12 to 06/01)
        if (now.month == 12 and now.day >= 24) or (now.month == 1 and now.day <= 6):
            print(f"[{now}] Skipping Variations Sent Check (Festivities)")
            return

        print(f"[{now}] Checking Variations Sent")

        now += timedelta(days=1)

        db = Variations(self.bot.mongo_client)
        tomorrow_var = await db.get_variations_by_date(now.strftime("%d-%m-%Y"))

        if not tomorrow_var:
            embed = discord.Embed(
                title="Sembrano non esserci variazioni per domani...",
                description="Controlla manualmente nel sito per sicurezza!",
                color=discord.Color.red()
            )

            await self.bot.log_channel.send(embed=embed, content="@everyone")
