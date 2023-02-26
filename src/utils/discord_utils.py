import datetime
from itertools import groupby

from discord import Embed, Color, utils
from discord.utils import format_dt


def generate_embed(variations: list[dict], missing: bool = True) -> list[Embed]:
    """
    It generates a list of embeds with the missing/returned teachers.

    :param variations: The teachers to generate the embeds for
    :param missing: Whether the teachers are missing or returned
    :return: A list of embeds
    """
    # Create embed grouped by date
    embeds = []

    date_group = sorted(variations, key=lambda x: x['date'])
    for date, variations in groupby(date_group, key=lambda x: x['date']):
        date = datetime.datetime.strptime(date, '%d-%m-%Y')

        title = f":tada: Nuove variazioni per {format_dt(date, 'D')}:" if missing else f":frowning2: Variazioni rimosse per il {format_dt(date, 'D')}:"

        embed = Embed(title=title, color=Color.green() if missing else Color.red())

        embed.add_field(name="\u200b", value="**Ora**")
        embed.add_field(name="\u200b", value="**Docente assente**")
        embed.add_field(name="\u200b", value="**Note**")
        for teacher in variations:
            embed.add_field(name=teacher['hour'], value=f"({teacher['classroom']})")
            embed.add_field(name=teacher['teacher'], value="\u200b")
            embed.add_field(name=teacher['notes'], value=f"(Sostituto: {teacher['substitute_1']})" if teacher['substitute_1'] != "-" else "\u200b")

        embeds.append(embed)

    return embeds


def generate_embeds(variations: list[dict], missing: bool = True) -> dict[list[Embed]]:
    """
    It generates an embed with the missing/returned teachers.

    :param missing: If True, it generates the embeds for the missing teachers, otherwise for the returned teachers
    :param variations: The teachers to generate the embeds for
    :return: A dictionary with the embeds variations grouped by class (Example can be found in examples/missing_teachers_embeds.json)
    """

    # Group variations by class
    variations = sorted(variations, key=lambda x: x['class'])
    variations = groupby(variations, key=lambda x: x['class'])

    # Generate embeds
    if missing:
        return {class_name: generate_embed(teachers) for class_name, teachers in variations}
    else:
        return {class_name: generate_embed(teachers, missing=False) for class_name, teachers in variations}


def merge_embeds(*embeds: dict[list[Embed]]) -> dict[list[Embed]]:
    """
    It merges the embeds of the same class.

    :param embeds: The embeds to merge
    :return: A dictionary with the merged embeds
    """
    merged_embeds = {}
    for embed in embeds:
        for class_name, class_embeds in embed.items():
            if class_name not in merged_embeds:
                merged_embeds[class_name] = class_embeds
            else:
                merged_embeds[class_name].extend(class_embeds)

    return merged_embeds


async def send_embeds(bot, channel, embeds_dict: dict[[list[Embed]]]) -> None:
    """
    It sends the embeds to a specific channel.

    :param bot: Discord bot
    :param channel: The channel to send the embeds to
    :param embeds_dict: The embeds to send (Structured as in generate_embeds())
    :return: None
    """
    guild = bot.school_guild

    owner = bot.get_user(guild.owner_id)
    if owner is None:
        owner = await bot.fetch_user(guild.owner_id)

    for class_name, embeds in embeds_dict.items():
        role = utils.get(guild.roles, name=class_name)

        embeds = [embed.set_footer(icon_url=owner.avatar.url, text=owner.display_name) for embed in embeds]
        m = await channel.send(content=role.mention, embeds=embeds)
        await m.add_reaction("\U0001f389")
        await m.add_reaction("\U0001f62d")
