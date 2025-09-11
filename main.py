import asyncio
import logging
import os
import sys

import motor.motor_asyncio as motor
from discord import Intents, Object, LoginFailure, Activity, ActivityType, Guild
from discord.ext.commands import Bot
from dotenv import load_dotenv

from src.commands.analytics.analytics import AnalyticsView
from src.commands.analytics.plots import generate_plots
from src.loops.new_year.ui.select_class_view import SelectClassView
from src.mongo_db.config_db import ConfigDB
from src.mongo_db.variations_db import VariationsDB

load_dotenv()


class ITIBot(Bot):
    """Subclassing Discord bot class"""

    def __init__(self, **options):
        super().__init__(**options)
        prod = os.environ.get('PROD', 'False').lower() == 'true'

        self.guild_id = Object(id=int(os.environ['GUILD_ID'] if prod else os.environ['GUILD_ID_TEST']))

        self.guild = None
        self.me = None
        self.owner = int(os.environ['OWNER_ID'])

        self.announce_channel = int(os.environ['ANNOUNCE_CHANNEL'] if prod else os.environ['ANNOUNCE_CHANNEL_TEST'])
        self.log_channel = int(os.environ['LOG_CHANNEL'] if prod else os.environ['LOG_CHANNEL_TEST'])
        self.select_channel = int(os.environ['SELECT_CHANNEL'] if prod else os.environ['SELECT_CHANNEL_TEST'])
        self.analytics_channel = int(os.environ['ANALYTICS_CHANNEL'] if prod else os.environ['ANALYTICS_CHANNEL_TEST'])
        self.admin_channel = int(os.environ['ADMIN_CHANNEL'] if prod else os.environ['ADMIN_CHANNEL_TEST'])

        self.mongo_client = None
        self.school_year = None

        self.analytics_view = None
        self.select_class_view = None

    async def setup_hook(self):
        print("-- Setting up bot --")

        self.guild: Guild = await self.fetch_guild(self.guild_id.id)
        self.owner = self.get_user(self.owner) or await self.fetch_user(self.owner)
        self.me = await self.guild.fetch_member(self.user.id)

        # Fetch channels
        self.announce_channel = await self.fetch_channel(self.announce_channel)
        self.log_channel = await self.fetch_channel(self.log_channel)
        self.select_channel = await self.fetch_channel(self.select_channel)
        self.analytics_channel = await self.fetch_channel(self.analytics_channel)
        self.admin_channel = await self.fetch_channel(self.admin_channel)

        print("-- Channels fetched --")

        # Load cogs
        for file in os.listdir("src//cogs"):
            if file.endswith(".py"):
                await self.load_extension('src.cogs.' + file[:-3])

        print("-- Cogs loaded --")

        self.mongo_client = motor.AsyncIOMotorClient(os.environ['MONGO_URL'])

        # Load persistent roles and analytics
        config_db = ConfigDB(self.mongo_client)

        self.school_year = await config_db.get_current_school_year()

        self.analytics_view = AnalyticsView(self.mongo_client, self.school_year)
        self.select_class_view = SelectClassView(await config_db.get_classes())

        self.add_view(self.select_class_view)
        self.add_view(self.analytics_view)

        print("-- Setup complete --")

    async def on_ready(self):
        print(f'-- Logged in as {self.user} (ID: {self.user.id}) --')

        # Sync Slash Commands with Discord
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)

        await self.change_presence(activity=Activity(
            name="www.ispascalcomandini.it",
            type=ActivityType.watching
        ))

        await generate_plots(self)

    async def upgrade_school_year(self):
        config_db = ConfigDB(self.mongo_client)

        await config_db.upgrade_school_year()
        self.school_year += 1
        self.analytics_view.update_school_year(self.school_year)

        await self.select_class_view.set_classes(await config_db.get_classes())

        variations_db = VariationsDB(self.mongo_client, self.school_year)
        await variations_db.create_collection()

        await generate_plots(self)


async def main():
    # Discord
    intents = Intents.default()
    intents.message_content = True
    intents.members = True
    bot = ITIBot(command_prefix='!', description="ITI Blaise Pascal Discord Bot", intents=intents)

    async with bot:
        try:
            logging.basicConfig(level=logging.ERROR)
            await bot.start(os.environ['DISCORD'])
        except LoginFailure as e:
            print("\n\nERROR: Discord Token not valid (" + str(e) + ")\n\n")
            sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
