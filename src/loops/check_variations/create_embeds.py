from discord import Embed, Color
from discord.utils import format_dt

from src.models.variation import Variation


def create_variations_embeds(*variations: Variation) -> list[Embed]:
    """
    It takes a list of Variation objects and returns a list of Embed objects

    :param variations: A list of Variation objects
    :return: A list of Embed objects.
    """

    embeds = []

    for variation in variations:
        embed = None
        match variation.type:
            case "new":
                embed = create_new_embed(variation)
            case "removed":
                embed = create_removed_embed(variation)
            case "edited":
                embed = create_edited_embed(variation)
            case _:
                continue

        if embed and variation.ocr:
            embed.set_footer(
                text="Variazione rilevata tramite OCR, potrebbe contenere errori, quindi controlla manualmente nel sito per sicurezza!")

        if embed:
            embeds.append(embed)

    return embeds


def create_new_embed(variation: Variation) -> Embed:
    """
    It creates an embed for a new variation

    :param variation: The Variation object to create the embed for
    :return: An Embed object.
    """

    title = f":tada: Nuova variazione del {format_dt(variation.date, 'D')}"
    color = Color.green()
    description = f":teacher: **Docente assente: {variation.teacher}**\n" \
                  f"\t• **Ora:** {variation.hour}^\n" \
                  f"\t• **Aula:** {variation.classroom}\n" \
                  f"\t• **Sostituto:** {variation.substitute_1}\n" + \
                  (f"\t• **Note:** {variation.notes}\n" if variation.notes else '')
    embed = Embed(title=title, description=description, color=color)

    return embed


def create_removed_embed(variation: Variation) -> Embed:
    """
    It creates an embed for a removed variation

    :param variation: The Variation object to create the embed for
    :return: An Embed object.
    """

    title = f":frowning2: È stata rimossa la variazione del {format_dt(variation.date, 'D')}"
    color = Color.red()
    description = f":teacher: **Docente rientrato: {variation.teacher}**\n" \
                  f"\t• **Ora:** {variation.hour}^\n"

    embed = Embed(title=title, description=description, color=color)

    return embed


def create_edited_embed(variation: Variation) -> Embed:
    """
    It creates an embed for an edited variation

    :param variation: The Variation object to create the embed for
    :return: An Embed object.
    """

    title = f":pencil2: È stata modificata una variazione del {format_dt(variation.date, 'D')}"
    color = Color.orange()

    description = f"Sono stati modificati i seguenti campi per l'assenza di **{variation.teacher}** alla **{variation.hour}^** ora:\n"
    embed = Embed(title=title, description=description, color=color)

    for change in variation.edited_fields:
        match change:
            case "classroom":
                embed.add_field(name="Aula", value=variation.classroom, inline=False)
            case "substitute_1":
                embed.add_field(name="Sostituto", value=variation.substitute_1, inline=False)
            case "substitute_2":
                embed.add_field(name="Secondo Sostituto", value=variation.substitute_2, inline=False)
            case "notes":
                embed.add_field(name="Note", value=variation.notes, inline=False)
            case _:
                continue

    return embed
