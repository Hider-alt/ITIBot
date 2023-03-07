import os

import discord
from discord import ui, ButtonStyle, Embed, Color, SelectOption

from src.mongo_repository.variations import Variations


weekdays = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


class AnalyticsView(ui.View):
    def __init__(self, mongo_client):
        super().__init__(timeout=None)
        self.mongo_client = mongo_client
        self.db = Variations(mongo_client)

        self.add_item(ClassesScoreboard())
        self.add_item(ProfessorsScoreboard())
        self.add_item(DatetimeStats())


class DatetimeStats(ui.Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Statistiche temporali", custom_id="datetime_stats")

    async def callback(self, interaction):
        yearly_stats = await self.view.db.get_yearly_stats()
        weekday_stats = await self.view.db.get_weekday_stats()
        hourly_stats = await self.view.db.get_hourly_stats()

        await interaction.response.send_message(
            embed=Embed(
                title="Statistiche temporali",
                description=f"Mese con più sostituzioni: **{months[max(yearly_stats, key=yearly_stats.get) - 1]}**\n"
                            f"Giorno settimanale con più sostituzioni: **{weekdays[max(weekday_stats, key=weekday_stats.get) - 1]}**\n"
                            f"Ora con più sostituzioni: **{max(hourly_stats, key=hourly_stats.get)}^**",
                color=Color.gold()
            ),
            ephemeral=True
        )

        options = [
            SelectOption(label="Mensili", value="monthly"),
            SelectOption(label="Giorni settimanali", value="weekly"),
            SelectOption(label="Orarie", value="hourly"),
            SelectOption(label="Tutti i grafici", value="all")
        ]

        await interaction.followup.send(
            embed=Embed(
                title="Statistiche temporali",
                description="Seleziona uno o più grafici da vedere",
                color=Color.gold()
            ),
            view=SelectPlotView(options, "data/plots/datetime/"),
            ephemeral=True
        )


class ProfessorsScoreboard(ui.Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Classifica prof.", custom_id="professors_scoreboard")

    async def callback(self, interaction):
        scoreboard = await self.view.db.get_professors_scoreboard()

        await interaction.response.send_message(
            embed=Embed(
                title="Top 10 prof. con più sostituzioni",
                description="\n".join([f"{index + 1}. **{item['_id']}** - {item['variations']} ore di assenza" for index, item in enumerate(scoreboard[:10])]),
                color=Color.gold()
            ),
            file=discord.File("data/plots/teachers/professors_scoreboard.png"),  # Remove if other plots are added
            ephemeral=True
        )

        # Uncomment this if other plots are added
        # options = [SelectOption(label="Classifica prof", value="professors_scoreboard")]
        #
        # await interaction.followup.send(
        #     embed=Embed(
        #         title="Classifica prof.",
        #         description="Seleziona uno o più grafici da vedere",
        #         color=Color.gold()
        #     ),
        #     view=SelectPlotView(options, "data/plots/teachers"),
        #     ephemeral=True
        # )


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

        options = [SelectOption(label="Overview classi", value="summary")] + \
                  [SelectOption(label="Overview classi proporzionale al numero di sezioni", value="summary_per_class_number")] + \
                  [SelectOption(label=f"Classi {class_age}°", value=f"class_{class_age}_scoreboard") for class_age in range(1, 6)] + \
                  [SelectOption(label="Tutti i grafici", value="all")]

        await interaction.followup.send(
            embed=Embed(
                title="Classifica classi",
                description="Seleziona uno o più grafici da vedere",
                color=Color.gold()
            ),
            view=SelectPlotView(options, "data/plots/classes"),
            ephemeral=True
        )


class SelectPlotView(ui.View):
    def __init__(self, options, path_to_plot):
        super().__init__()
        self.add_item(SelectPlot(options, path_to_plot))


class SelectPlot(ui.Select):
    def __init__(self, options, path_to_plot):
        super().__init__(max_values=len(options), placeholder="Seleziona uno o più grafici da vedere", options=options)
        self.path_to_plot = path_to_plot

    async def callback(self, interaction):
        await interaction.response.defer()

        files = []

        if "all" in self.values:
            # Add all .png from path_to_plot
            for file in os.listdir(self.path_to_plot):
                if file.endswith(".png"):
                    files.append(discord.File(os.path.join(self.path_to_plot, file)))

            await interaction.edit_original_response(embed=None, attachments=files, view=None)
            return

        for value in self.values:
            files.append(discord.File(os.path.join(self.path_to_plot, f"{value}.png")))

        await interaction.edit_original_response(embed=None, attachments=files, view=None)