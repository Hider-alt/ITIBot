from discord import app_commands, Embed, Color
from discord.ext.commands import Cog

from src.commands.analytics import AnalyticsView
from src.commands.loops.check_variations import refresh_variations
from src.commands.roles import add_roles, upgrade_class
from src.utils.plots import generate_plots


async def setup(bot):
    await bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invia_statistiche", description="ADMIN ONLY")
    @app_commands.describe(start_date="Data di inizio delle statistiche")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_analytics(self, itr, start_date: str):
        await itr.response.send_message("Invio analytics in corso...", ephemeral=True)

        await self.bot.analytics_channel.send(
            embed=Embed(
                title="Statistiche",
                description=f"Scegli quali statistiche vedere",
                color=Color.og_blurple()
            ).set_footer(text=f"Dati collezionati dal {start_date}"),
            view=AnalyticsView(itr.client.mongo_client)
        )

    @app_commands.command(name="refresh_variazioni", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def refresh(self, itr):
        await itr.response.send_message("Refresh in corso...", ephemeral=True)

        await refresh_variations(itr.client)

        await itr.edit_original_response(content="Variazioni refreshate")

    @app_commands.command(name="genera_grafici", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_charts(self, itr):
        await itr.response.send_message("Generazione grafici in corso...", ephemeral=True)

        await generate_plots(self.bot.mongo_client)

        await itr.edit_original_response(content="Grafici generati")

    @app_commands.command(name="aggiungi_ruoli", description="ADMIN ONLY")
    @app_commands.describe(lista_classi="Lista delle classi prese dall'orario delle classi (prima pagina)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_roles(self, itr, lista_classi: str):
        await itr.response.send_message("Aggiornamento ruoli in corso...", ephemeral=True)

        await add_roles(itr, lista_classi)

    @app_commands.command(name="upgrade_ruoli", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def upgrade_roles(self, itr):
        await itr.response.send_message(content="Upgrade in corso...", ephemeral=True)

        await upgrade_class(itr)

        await itr.edit_original_response(content="Upgrade completato")

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

