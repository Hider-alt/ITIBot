import json

from discord import app_commands, Embed, Color
from discord.app_commands import Range
from discord.ext.commands import Cog


async def setup(bot):
    await bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ruota_pdf", description="Cambia il numero di gradi per cui i pdf devono essere ruotati")
    @app_commands.describe(degrees="Il numero di gradi per cui i pdf dovranno essere ruotati")
    @app_commands.checks.has_permissions(administrator=True)
    async def rotate(self, itr, degrees: Range[int, -359, 359]):
        """
        Change the number of degrees that a PDF file has to be rotated.
        """
        with open("data/config.json", "r") as f:
            config = json.load(f)

        config["rotation_angle"] = degrees

        with open("data/config.json", "w") as f:
            json.dump(config, f)

        await itr.response.send_message(embed=Embed(
            title=f"Cambiato il numero di gradi per cui i PDF verranno girati a {degrees} gradi",
            color=Color.green()
        ))
