import calendar
from datetime import datetime, timedelta, time

import discord
import pytz
from discord.ext import tasks
from discord.ext.commands import Cog

from src.api.iti.variations import VariationsAPI
from src.loops.check_variations.classify_variations import classify_variations
from src.loops.check_variations.create_embeds import create_variations_embeds
from src.loops.check_variations.group_variations import group_variations_by_class
from src.loops.check_variations.send_embeds import send_grouped_embeds
from src.mongo_db.variations_db import VariationsDB
from src.utils.datetime_utils import is_christmas, is_school_over


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
        if is_christmas(now) or is_school_over(now):
            print(f"Stopping daily loops for festivities ({now})")

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
        """ Check for new variations, notify users and save them to the database. """

        now = datetime.now(pytz.timezone('Europe/Rome'))

        if 0 < now.hour < 6:
            print(f"[{now}] Skipping Variations Check (0 < now hour < 6)")
            return

        print(f"[{now}] Checking Variations")

        variations_db = VariationsDB(self.bot.mongo_client, self.bot.school_year)

        links = await VariationsAPI.get_variations_links()
        variations = await VariationsAPI.get_variations(*links)

        await classify_variations(self.bot, variations)
        if not variations:
            print(f"[{now}] No new variations")
            return

        grouped_variations: dict[str, list] = group_variations_by_class(variations)

        # Create embeds for each class
        grouped_embeds = {}
        for class_name, class_vars in grouped_variations.items():
            grouped_embeds[class_name] = create_variations_embeds(*class_vars)

        await send_grouped_embeds(self.bot, grouped_embeds)

        await variations_db.save_variations(variations)

        print(f"[{now}] Variations Check complete, {len(variations)} variations processed")

    # Check every day at 20:00 if variations have been detected for the next day
    @tasks.loop(time=time(20))
    async def check_variations_sent(self):
        now = datetime.now(pytz.timezone('Europe/Rome'))
        tomorrow = now + timedelta(days=1)

        # Skip if tomorrow is a Sunday (there are no variations on Sundays)
        if tomorrow.weekday() == calendar.SUNDAY:
            print(f"[{now}] Skipping Variations Sent Check (Sunday)")
            return

        print(f"[{now}] Checking Variations Sent")

        db = VariationsDB(self.bot.mongo_client, self.bot.school_year)
        tomorrow_var = await db.get_variations_by_date(tomorrow.date())

        # If variations exist for tomorrow, do nothing
        if tomorrow_var:
            return

        # If we are here, there are no variations for tomorrow, so we check if there's any link in ITI page
        if await VariationsAPI.get_variations_links():
            embed = discord.Embed(
                title="Sembrano non esserci variazioni per domani...",
                description="Controlla manualmente [nel sito](https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/) per sicurezza!",
                color=discord.Color.red()
            )

            await self.bot.log_channel.send(embed=embed, content="@everyone")

    @loops_controller.before_loop
    async def before_loops_controller(self):
        await self.bot.wait_until_ready()
