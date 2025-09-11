from discord import PermissionOverwrite, utils

from src.utils.discord_utils import get_or_fetch_role


async def create_variations_channels(bot, grouped_classes: list[list[str]]) -> None:
    """
    Create channels for each class in the grouped classes (and categories)

    :param bot: The bot instance.
    :param grouped_classes: The classes grouped by year (e.g. [['1A', '1B'], ['2A', '2B'], ...]).
    """

    await delete_variations_channels(bot)

    await create_categories(bot, range(1, len(grouped_classes) + 1))

    await create_channels(bot, grouped_classes)


async def delete_variations_channels(bot) -> None:
    """
    Delete all channels that start with "variazioni-" and their categories
    """

    categories = set()
    channels = await bot.guild.fetch_channels()
    for channel in channels:
        if channel.name.startswith("variazioni-"):
            class_name = channel.name.replace("variazioni-", "")

            # If no category of categories, starts with the same number of class_name (first char), then fetch category
            if not any([category.name[0] == class_name[0] for category in categories]):
                categories.add(utils.get(channels, id=channel.category_id))

            await channel.delete(reason="Starting a new year, deleting old variations channels")

    # Delete empty categories (that start with a digit)
    for category in categories:
        await category.delete(reason="Starting a new year, deleting empty categories")


async def create_categories(bot, years: range) -> None:
    """
    Create categories for each year.

    :param bot: The bot instance.
    :param years: The range of years to create categories for (e.g. range(1, 6) for 5 years).
    """

    for year in years:
        category_name = f"{year}°"

        # Check if the category already exists
        if not any(category.name == category_name for category in bot.guild.categories):
            await bot.guild.create_category(name=category_name, reason="Creating categories for variations channels")


async def create_channels(bot, grouped_classes: list[list[str]]) -> None:
    """
    Create channels for each class in the grouped classes.

    :param bot: The bot instance.
    :param grouped_classes: The classes grouped by year (e.g. [['1A', '1B'], ['2A', '2B'], ...]).
    """

    every_perms = PermissionOverwrite(view_channel=False)
    role_perms = PermissionOverwrite(send_messages=False, read_messages=True, read_message_history=True)
    bot_perms = PermissionOverwrite(send_messages=True, add_reactions=True)

    for class_list in grouped_classes:
        category_name = f"{class_list[0][0]}°"
        category = next((cat for cat in bot.guild.categories if cat.name == category_name), None)

        if category is None:
            print("Error: Category not found for class list:", class_list)
            continue

        for class_name in class_list:
            channel_name = f"variazioni-{class_name}"
            if any(channel.name == channel_name for channel in category.text_channels):
                continue

            class_role = await get_or_fetch_role(bot.guild, class_name)
            if class_role is None:
                print(f"Error: Role not found for class {class_name}")
                continue

            await bot.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites={
                    bot.guild.default_role: every_perms,
                    class_role: role_perms,
                    bot.me: bot_perms
                }
            )
