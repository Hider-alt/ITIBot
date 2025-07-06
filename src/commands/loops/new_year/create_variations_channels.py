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
    Delete all channels that start with "variazioni-orario-".
    """

    for channel in await bot.school_guild.fetch_channels():
        if channel.name.startswith("variazioni-orario-"):
            print(f"Deleting channel {channel.name}")
            await channel.delete(reason="Starting a new year, deleting old variations channels")


async def create_categories(bot, years: range) -> None:
    """
    Create categories for each year.

    :param bot: The bot instance.
    :param years: The range of years to create categories for (e.g. range(1, 6) for 5 years).
    """

    for year in years:
        category_name = f"{year}°"

        # Check if the category already exists
        if not any(category.name == category_name for category in bot.school_guild.categories):
            await bot.school_guild.create_category(name=category_name, reason="Creating categories for variations channels")


async def create_channels(bot, grouped_classes: list[list[str]]) -> None:
    """
    Create channels for each class in the grouped classes.

    :param bot: The bot instance.
    :param grouped_classes: The classes grouped by year (e.g. [['1A', '1B'], ['2A', '2B'], ...]).
    """

    every_perms = bot.school_guild.default_role.permissions
    every_perms.view_channel = False

    role_perms = bot.school_guild.default_role.permissions
    role_perms.send_messages = False
    role_perms.read_messages = True
    role_perms.read_message_history = True

    bot_perms = bot.school_guild.me.permissions
    bot_perms.send_messages = True
    bot_perms.add_reactions = True

    for class_list in grouped_classes:
        category_name = f"{class_list[0][0]}°"
        category = next((cat for cat in bot.school_guild.categories if cat.name == category_name), None)

        if category is None:
            print("Error: Category not found for class list:", class_list)
            continue

        for class_name in class_list:
            channel_name = f"variazioni-orario-{class_name}"
            if any(channel.name == channel_name for channel in category.text_channels):
                continue

            class_role = next((role for role in bot.school_guild.roles if role.name == class_name), None)
            if class_role is None:
                print(f"Error: Role not found for class {class_name}")
                continue

            await bot.school_guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites={
                    bot.school_guild.default_role: every_perms,
                    class_role: role_perms,
                    bot.school_guild.me: bot_perms
                }
            )
