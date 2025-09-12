from discord import TextChannel, Embed, Color

from src.loops.new_year.ui.select_class_view import SelectClassView


async def send_new_class_selection(channel: TextChannel, classes: set[str]) -> list[list[str]]:
    """
    Sends new message to the channel to select new classes and deletes the old one.

    :param channel: The channel where the message will be sent.
    :param classes: Set of class names to be grouped and displayed.
    :return: List of lists, where each sublist contains classes that share the same first digit.
    """

    # Send new message to select new classes
    grouped_classes = group_classes_by_first_digit(classes)

    await send_select_role_message(channel, grouped_classes)

    return grouped_classes


def group_classes_by_first_digit(classes: set[str]) -> list[list[str]]:
    """
    Groups classes by their first digit (each list sorted alphabetically).

    :param classes: Set of class names.
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

    # Sort groups by the first digit
    grouped_classes = dict(sorted(grouped_classes.items(), key=lambda item: item[0]))

    return list(grouped_classes.values())


async def send_select_role_message(channel, classes: list[list[str]]):
    embed = Embed(
        title="Seleziona la tua classe",
        description="Se hai già un ruolo di una classe, selezionando un'altra classe ti verrà rimosso il vecchio ruolo",
        color=Color.og_blurple()
    )

    await channel.send(embed=embed, view=SelectClassView(classes))
