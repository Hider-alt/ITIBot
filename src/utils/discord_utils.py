import datetime

from discord import Embed, Color, utils
from discord.utils import format_dt

from src.utils.datetime_utils import is_tomorrow


def generate_missing_embed(teacher):
    """
    It generates an embed with the missing teacher.

    :param teacher: The missing teacher
    :return: An embed about the missing teacher
    """
    # Check if the missing date is tomorrow
    date = datetime.datetime.strptime(teacher['date'], '%d-%m-%Y')
    if is_tomorrow(date):
        title = f":tada: Domani {teacher['teacher']} sarà assente!"
    else:
        title = f":tada: {teacher['teacher']} il {format_dt(date, 'D')} sarà assente!"

    # Generate description
    description = f"**Ora**: {teacher['hour']}\n" \
                  f"**Aula**: {teacher['classroom']}\n" \
                  f"**Sostituto/a**: {teacher['substitute_1']}\n"

    if teacher['substitute_2'] != "-":
        description += f"**Sostituto/a 2**: {teacher['substitute_2']}\n"

    description += f"**Annotazioni**: {teacher['notes']}"

    # Generate embed
    embed = Embed(title=title, description=description, color=Color.green())

    return embed


def generate_returned_embed(teacher):
    """
    It generates an embed with the returned teacher.

    :param teacher: The returned teacher
    :return: An embed about the returned teacher
    """
    # Check if the missing date is tomorrow
    date = datetime.datetime.strptime(teacher['date'], '%d-%m-%Y')
    if is_tomorrow(date):
        description = f"Il prof. {teacher['teacher']} che domani doveva mancare, ci sarà!"
    else:
        description = f"Il prof. {teacher['teacher']} che il {format_dt(date, 'D')} sarebbe dovuto mancare, ci sarà!"

    # Generate embed
    embed = Embed(title=":frowning2: Brutte notizie!", description=description, color=Color.red())

    return embed


def generate_embeds(teachers: list[dict], missing: bool = True) -> dict[dict[list[Embed]]]:
    """
    It generates an embed with the missing teachers.

    :param missing: If True, it generates the embeds for the missing teachers, otherwise for the returned teachers
    :param teachers: The teachers to generate the embeds for
    :return: A dictionary with the embeds variations grouped by class and date (Example can be found in examples/missing_teachers_embeds.json)
    """
    embeds = {}

    for teacher in teachers:
        if teacher['date'] not in embeds.keys():
            embeds[teacher['date']] = {}

        if teacher['class'] not in embeds[teacher['date']].keys():
            embeds[teacher['date']][teacher['class']] = []

        if missing:
            embeds[teacher['date']][teacher['class']].append(generate_missing_embed(teacher))
        else:
            embeds[teacher['date']][teacher['class']].append(generate_returned_embed(teacher))

    return embeds


async def send_embeds(guild, channel, embeds_dict: dict[dict[list[Embed]]]) -> None:
    """
    It sends the embeds to the channel.

    :param channel: The channel to send the embeds to
    :param guild: The guild to get the roles from
    :param embeds_dict: The embeds to send (Structured as in generate_embeds)
    :return: None
    """
    for classes in embeds_dict.values():
        for class_name, class_variations in classes.items():
            class_role = utils.get(guild.roles, name=class_name)
            await channel.send(
                content=f"{class_role.mention}",
                embeds=class_variations
            )
