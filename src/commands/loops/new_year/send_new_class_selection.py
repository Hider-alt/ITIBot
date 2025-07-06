from discord import TextChannel, Embed, Color

from src.commands.loops.new_year.ui.select_class_view import SelectClassView
from src.utils.discord_utils import delete_last_message


async def send_new_class_selection(channel: TextChannel, classes: list[str]) -> list[list[str]]:
    """
    Sends new message to the channel to select new classes and deletes the old one.

    :param channel: The channel where the message will be sent.
    :param classes: List of class names to be grouped and displayed.
    :return: List of lists, where each sublist contains classes that share the same first digit.
    """

    await delete_last_message(channel)

    # Send new message to select new classes
    grouped_classes = group_classes_by_first_digit(classes)

    await send_select_role_message(channel, grouped_classes)

    return grouped_classes


def group_classes_by_first_digit(classes: list[str]) -> list[list[str]]:
    """
    Groups classes by their first digit (each list sorted alphabetically).

    :param classes: List of class names.
    :return: List of lists, where each sublist contains classes that share the same first digit.
    """

    grouped_classes = {}

    for class_name in classes:
        if not class_name:
            continue
        first_digit = class_name[0]
        if first_digit not in grouped_classes:
            grouped_classes[first_digit] = []
        grouped_classes[first_digit].append(class_name)

    # Sort each group alphabetically
    for key in grouped_classes:
        grouped_classes[key].sort()

    return list(grouped_classes.values())


async def send_select_role_message(channel, classes: list[list[str]]):
    embed = Embed(
        title="Seleziona la tua classe",
        color=Color.green()
    )

    await channel.send(embed=embed, view=SelectClassView(classes))
