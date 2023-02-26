import datetime
from itertools import groupby

from discord import Embed, Color, utils
from discord.utils import format_dt

from src.utils.datetime_utils import is_before_tomorrow


def generate_embed(variations: list[dict[dict]], missing: bool = True) -> list[Embed]:
    """
    It generates an embed with the missing teachers.

    :param missing: If the teachers are missing or returned
    :param variations: The missing teachers
    :return: A list of embeds
    """
    # Create an embed for each date of the missing teachers
    embeds = []

    date_group = sorted(variations, key=lambda x: x['date'])
    for date, variations in groupby(date_group, key=lambda x: x['date']):
        date = datetime.datetime.strptime(date, '%d-%m-%Y')
        if is_before_tomorrow(date):
            title = ":tada: Domani mancheranno i seguenti prof:" if missing else ":frowning2: Le seguenti variazioni orario di domani, sono state cancellate:"
        else:
            title = f":tada: I seguenti prof. mancheranno {format_dt(date, 'D')}:" if missing else f":frowning2: Le seguenti variazioni orario di {format_dt(date, 'D')}, sono state cancellate:"

        embed = Embed(title=title, color=Color.green() if missing else Color.red())
        embed.add_field(name="\u200b", value="**Ora**")
        embed.add_field(name="\u200b", value="**Docente assente**")
        embed.add_field(name="\u200b", value="**Note**")
        for teacher in variations:
            embed.add_field(name=teacher['hour'], value="\u200b")
            embed.add_field(name=teacher['teacher'], value="\u200b")
            embed.add_field(name=teacher['notes'], value="\u200b")

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
        return {class_name: [generate_embed(teachers)] for class_name, teachers in variations}
    else:
        return {class_name: [generate_embed(teachers, missing=False)] for class_name, teachers in variations}


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


    for class_name, list_embeds in embeds_dict.items():
        role = utils.get(guild.roles, name=class_name)
        for embeds in list_embeds:
            embed = [embed.set_footer(icon_url=owner.avatar.url, text=owner.display_name) for embed in embeds]
            m = await channel.send(content=role.mention, embeds=embed)
            await m.add_reaction("\U0001f389")
            await m.add_reaction("\U0001f62d")
