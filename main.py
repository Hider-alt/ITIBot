import asyncio
import json
import logging
import sys
import os
import motor.motor_asyncio as motor

from dotenv import load_dotenv

from discord import Intents, Object, LoginFailure, Activity, ActivityType
from discord.ext.commands import Bot

from src.commands.analytics import AnalyticsView
from src.commands.refresh_roles import SelectRoleView

load_dotenv()


class MyBot(Bot):
    """Subclassing Discord bot class"""

    def __init__(self, **options):
        super().__init__(**options)
        self.guild = Object(id=1077747577384075354)

        self.school_guild = None
        self.log_channel = 1077747715775139851
        self.select_channel = 1079407521409794178
        self.analytics_channel = 1081715105013715086

        self.mongo_client = None

    async def setup_hook(self):
        # Fetch channels
        self.school_guild = await self.fetch_guild(self.guild.id)
        self.log_channel = await self.fetch_channel(self.log_channel)
        self.select_channel = await self.fetch_channel(self.select_channel)
        self.analytics_channel = await self.fetch_channel(self.analytics_channel)

        # Load persistent roles
        with open("data/config.json", "r") as f:
            config = json.load(f)

        self.add_view(SelectRoleView(config["classes"]))

        # Load cogs
        for file in os.listdir("src//cogs"):
            if file.endswith(".py"):
                await self.load_extension('src.cogs.' + file[:-3])

        # Connect to MongoDB
        self.mongo_client = motor.AsyncIOMotorClient(os.environ['MONGO_URL'])

        # Load persistent analytics
        self.add_view(AnalyticsView(self.mongo_client))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        # Sync Slash Commands with Discord
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

        await self.change_presence(activity=Activity(
            name="www.ispascalcomandini.it",
            type=ActivityType.watching
        ))


async def main():
    async with bot:
        try:
            logging.basicConfig(level=logging.WARNING)
            await bot.start(os.environ['DISCORD'])
        except LoginFailure as e:
            print("\n\nERROR: Discord Token not valid (" + str(e) + ")\n\n")
            sys.exit()


intents = Intents.default()
intents.message_content = True
bot = MyBot(command_prefix='!', description="ITI Blaise Pascal Discord Bot", intents=intents)

asyncio.run(main())
