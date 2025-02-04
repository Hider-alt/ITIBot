import asyncio
import json
import logging
import os
import sys

import motor.motor_asyncio as motor
from discord import Intents, Object, LoginFailure, Activity, ActivityType
from discord.ext.commands import Bot
from dotenv import load_dotenv
from fastapi import FastAPI
from uvicorn import Config, Server

from src.commands.analytics import AnalyticsView
from src.commands.roles import SelectRoleView
from src.utils.plots import generate_plots

load_dotenv()


# Configure health check on port 8000
app = FastAPI()


@app.get("/")
async def health_check():
    return {"status": "ok"}


async def start_health_check():
    """Start the FastAPI server."""
    config = Config(app=app, host="0.0.0.0", port=8000, log_level="info")
    server = Server(config)

    print("Health check started")
    await server.serve()


class MyBot(Bot):
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

        await generate_plots(self.mongo_client)


async def main():
    # Disable OCR lib logging
    logging.getLogger().setLevel(logging.CRITICAL)

    # Heartbeat
    asyncio.create_task(start_health_check())

    # Discord
    intents = Intents.default()
    intents.message_content = True
    intents.members = True
    bot = MyBot(command_prefix='!', description="ITI Blaise Pascal Discord Bot", intents=intents)

    async with bot:
        try:
            logging.basicConfig(level=logging.WARNING)
            await bot.start(os.environ['DISCORD'])
        except LoginFailure as e:
            print("\n\nERROR: Discord Token not valid (" + str(e) + ")\n\n")
            sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
