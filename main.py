import asyncio
import json
import logging
import os
import sys

import motor.motor_asyncio as motor
from discord import Intents, Object, LoginFailure, Activity, ActivityType
from discord.ext.commands import Bot
from dotenv import load_dotenv

from src.commands.analytics.analytics import AnalyticsView
from src.commands.analytics.plots import generate_plots
from src.commands.roles import SelectRoleView

load_dotenv()


class ITIBot(Bot):
    """Subclassing Discord bot class"""

    def __init__(self, **options):
        super().__init__(**options)
        prod = os.environ.get('PROD', 'False').lower() == 'true'

        self.guild = Object(id=int(os.environ['GUILD_ID'] if prod else os.environ['GUILD_ID_TEST']))

        self.school_guild = None
        self.log_channel = int(os.environ['LOG_CHANNEL'] if prod else os.environ['LOG_CHANNEL_TEST'])
        self.select_channel = int(os.environ['SELECT_CHANNEL'] if prod else os.environ['SELECT_CHANNEL_TEST'])
        self.analytics_channel = int(os.environ['ANALYTICS_CHANNEL'] if prod else os.environ['ANALYTICS_CHANNEL_TEST'])

        self.mongo_client = None

    async def setup_hook(self):
        # Fetch channels
        self.school_guild = await self.fetch_guild(self.guild.id)
        self.log_channel = await self.fetch_channel(self.log_channel)
        self.select_channel = await self.fetch_channel(self.select_channel)
        self.analytics_channel = await self.fetch_channel(self.analytics_channel)

        # Load cogs
        for file in os.listdir("src//cogs"):
            if file.endswith(".py"):
                await self.load_extension('src.cogs.' + file[:-3])

        # Connect to MongoDB
        self.mongo_client = motor.AsyncIOMotorClient(os.environ['MONGO_URL'])

        # Load persistent roles and analytics
        with open("data/config.json", "r") as f:
            config = json.load(f)

        self.add_view(SelectRoleView(config["classes"]))
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

        await generate_plots(self.mongo_client)


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
