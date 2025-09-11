import datetime

from discord import Role, utils, File, Embed, Color

from src.commands.analytics.plots import generate_plots
from src.mongo_db.variations_db import VariationsDB


async def send_analytics_selection(bot):
    now = datetime.datetime.now()

    await bot.analytics_channel.send(
        embed=Embed(
            title="Statistiche",
            description=f"Scegli quali statistiche vedere",
            color=Color.og_blurple()
        ).set_footer(text=f"Dati collezionati dal {now.strftime('%d/%m/%Y')}"),
        view=bot.analytics_view
    )


async def send_analytics_recap(bot):
    """ Send an analytics recap to the analytics channel. """

    plots: list[File] = await generate_plots(bot)

    winner = await get_winner_class(bot)
    await bot.analytics_channel.send(content=f"# Statistiche {bot.school_year - 1}/{bot.school_year}\n"
                                             f"### 🏆 Classe con più sostituzioni: {winner.mention if winner else ''}\n")

    # Send the files in groups of 10
    chunk_size = 10
    for i in range(0, len(plots), chunk_size):
        await bot.analytics_channel.send(files=plots[i:i + chunk_size])


async def get_winner_class(bot) -> Role | None:
    var_db = VariationsDB(bot.mongo_client, bot.school_year)
    leaderboard = await var_db.get_classes_leaderboard()

    winner = leaderboard[0]['_id'] if leaderboard else None
    if not winner:
        return None

    return utils.get(bot.guild.roles, name=winner)
