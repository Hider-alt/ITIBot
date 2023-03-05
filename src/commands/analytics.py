import discord
from discord import ui, ButtonStyle, Embed, Color, SelectOption

from src.mongo_repository.variations import Variations


class AnalyticsView(ui.View):
    def __init__(self, mongo_client):
        super().__init__(timeout=None)
        self.mongo_client = mongo_client
        self.db = Variations(mongo_client)

        self.add_item(ClassesScoreboard())


class ClassesScoreboard(ui.Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Classifica classi", custom_id="classes_scoreboard")

    async def callback(self, interaction):
        scoreboard = await self.view.db.get_classes_scoreboard()

        await interaction.response.send_message(
            embed=Embed(
                title="Top 10 classi con più prof. assenti",
                description="\n".join([f"{index + 1}. **{item['_id']}** - {item['variations']} sostituzioni" for index, item in enumerate(scoreboard[:10])]),
                color=Color.gold()
            ),
            ephemeral=True
        )

        await interaction.followup.send(
            embed=Embed(
                title="Classifica classi",
                description="Seleziona uno o più grafici da vedere",
                color=Color.gold()
            ),
            view=SelectPlotView(),
            ephemeral=True
        )


class SelectPlotView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPlot())

class SelectPlot(ui.Select):
    def __init__(self):
        super().__init__()
        self.max_values = 7
        self.custom_id = f"select_plot"
        self.placeholder = f"Seleziona uno o più grafici da vedere"
        self.options = [SelectOption(label="Overview classi", value="overall")] + \
                       [SelectOption(label="Overview classi proporzionale al numero di classi", value="overall_proportional")] + \
                       [SelectOption(label=f"Classi {class_age}°", value=str(class_age)) for class_age in range(1, 6)] + \
                       [SelectOption(label="Tutti i grafici", value="all")]

    async def callback(self, interaction):
        await interaction.response.defer()

        files = []

        if "all" in self.values:
            files = [discord.File(f"data/plots/class_{class_name}_scoreboard.png") for class_name in range(1, 6)]
            files.append(discord.File("data/plots/summary.png"))

            await interaction.edit_original_response(embed=None, attachments=files, view=None)
            return

        if "overall" in self.values:
            files.append(discord.File("data/plots/summary.png"))

        if "overall_proportional" in self.values:
            files.append(discord.File("data/plots/summary_per_class_number.png"))

        for class_name in range(1, 6):
            if str(class_name) in self.values:
                files.append(discord.File(f"data/plots/class_{class_name}_scoreboard.png"))

        await interaction.edit_original_response(embed=None, attachments=files, view=None)