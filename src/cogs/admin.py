from discord import app_commands, Embed, Color
from discord.ext.commands import Cog

from src.commands.analytics import AnalyticsView
from src.commands.loops.check_teachers import refresh_variations
from src.commands.create_roles import add_roles


async def setup(bot):
    await bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invia_statistiche", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_analytics(self, itr):
        await itr.response.send_message("Invio analytics in corso...", ephemeral=True)

        await self.bot.analytics_channel.send(
            embed=Embed(
                title="Statistiche",
                description=f"Scegli quali statistiche vedere",
                color=Color.og_blurple()
            ).set_footer(text="Dati collezionati dal 04/03/2023"),
            view=AnalyticsView(itr.client.mongo_client)
        )

    @app_commands.command(name="refresh_variazioni", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def refresh(self, itr):
        await itr.response.send_message("Refresh in corso...", ephemeral=True)

        await refresh_variations(itr.client)

        await itr.edit_original_response(content="Variazioni refreshate")

    @app_commands.command(name="aggiungi_ruoli", description="ADMIN ONLY")
    @app_commands.describe(lista_classi="Lista delle classi prese dall'orario delle classi (prima pagina)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_roles(self, itr, lista_classi: str):
        await itr.response.send_message("Aggiornamento ruoli in corso...", ephemeral=True)

        await add_roles(itr, lista_classi)

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