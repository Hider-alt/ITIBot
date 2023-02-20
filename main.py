import asyncio
import sys
import os
from dotenv import load_dotenv

from discord import Intents, Object, LoginFailure, Activity, ActivityType
from discord.ext.commands import Bot


load_dotenv()


class MyBot(Bot):
    """Subclassing Discord bot class"""

    def __init__(self, **options):
        super().__init__(**options)
        self.school_guild = None
        self.guild = Object(id=981621881696313354)
        self.log_channel = 981622284471111732

    async def setup_hook(self):
        for file in os.listdir("src//cogs"):
            if file.endswith(".py"):
                await self.load_extension('src.cogs.' + file[:-3])

        self.log_channel = await self.fetch_channel(self.log_channel)
        self.school_guild = await self.fetch_guild(self.guild.id)

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
            await bot.start(os.environ['DISCORD'])
        except LoginFailure as e:
            print("\n\nERROR: Discord Token not valid (" + str(e) + ")\n\n")
            sys.exit()


intents = Intents.default()
intents.message_content = True
bot = MyBot(command_prefix='!', description="ITI Blaise Pascal Discord Bot", intents=intents)

asyncio.run(main())
