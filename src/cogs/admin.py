import datetime

from discord import app_commands
from discord.ext.commands import Cog

from src.loops.new_year.create_variations_channels import create_variations_channels
from src.loops.new_year.notify_roles_upgrade import notify_roles_upgrade
from src.loops.new_year.send_analytics import send_analytics_recap, send_analytics_selection
from src.loops.new_year.send_new_class_selection import send_new_class_selection
from src.loops.new_year.upgrade_roles import upgrade_roles
from src.mongo_db.config_db import ConfigDB
from src.utils.discord_utils import delete_last_message


async def setup(bot):
    await bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="ADMIN ONLY")
    @app_commands.describe(n="Numero di messaggi da cancellare")
    @app_commands.describe(inizia_con="Cancella solo tutti i messaggi dai canali che iniziano con questo testo")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, itr, n: int, inizia_con: str = None):
        await itr.response.send_message(content="Cancellazione messaggi in corso...", ephemeral=True)

        if inizia_con is not None:
            for channel in itr.guild.channels:
                if channel.name.startswith(inizia_con):
                    await channel.purge(limit=n)
        else:
            await itr.channel.purge(limit=n)

        await itr.edit_original_response(content="Messaggi cancellati")

    @app_commands.command(name="new_year", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def new_year(self, itr):
        now = datetime.datetime.now()

        print(f"[{now}] Creating and setting up new classes for the new school year")

        # 1 - Upgrade roles

        current_roles = await upgrade_roles(self.bot)
        if current_roles is None:
            print("Failed to get new year classes, retrying tomorrow")
            await itr.response.send_message(content="Failed to get new year classes, retrying tomorrow", ephemeral=True)
            return

        await notify_roles_upgrade(self.bot)

        print(f"[{now}] Roles upgraded successfully")

        # 2 - Create new classes channels and send selection message

        await delete_last_message(self.bot.select_channel)

        grouped_classes = await send_new_class_selection(self.bot.select_channel, current_roles)

        config_db = ConfigDB(self.bot.mongo_client)
        await config_db.set_classes(grouped_classes)

        await create_variations_channels(self.bot, grouped_classes)
        print(f"[{now}] New classes created and set up successfully")

        # 3 - Send analytics recap and selection

        await delete_last_message(self.bot.analytics_channel)

        await send_analytics_recap(self.bot)

        await send_analytics_selection(self.bot)

        # 4 - Update school year in bot and DB

        await self.bot.upgrade_school_year()

        await itr.response.send_message(content=f"[{now}] School year updated to {self.bot.school_year} successfully", ephemeral=True)
        print(f"[{now}] School year updated to {self.bot.school_year} successfully")
