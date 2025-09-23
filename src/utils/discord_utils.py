from discord import TextChannel, utils, Role

fetched_channels = []
fetched_roles = []


async def delete_last_message(channel: TextChannel) -> None:
    """
    Deletes the last message in the channel.

    :param channel: The channel to delete the last message from
    :return: None
    """
    if not channel:
        raise ValueError("Channel cannot be None")

    async for message in channel.history(limit=1):
        await message.delete()


async def notify_owner(bot, message: str) -> None:
    """
    Sends a message to the log channel.

    :param bot: The bot instance
    :param message: The message to send
    :return: None
    """

    await bot.admin_channel.send(content=f"{bot.owner.mention}\n{message}")


async def fetch_channel(guild, channel_name: str):
    global fetched_channels

    print("Fetching channels")
    channels = await guild.fetch_channels()
    fetched_channels = channels

    return utils.get(channels, name=channel_name)


async def fetch_role(guild, role_name: str):
    global fetched_roles

    print("Fetching roles")
    roles = await guild.fetch_roles()
    fetched_roles = roles

    return utils.get(roles, name=role_name)


async def get_or_fetch_channel(guild, channel_name: str):
    channel = utils.get(guild.channels, name=channel_name)

    if not channel:
        channel = utils.get(fetched_channels, name=channel_name)

    if not channel:
        print("Fetching channel: ", channel_name)
        channel = await fetch_channel(guild, channel_name)

    return channel


async def get_or_fetch_role(guild, role_name: str) -> Role:
    role = utils.get(guild.roles, name=role_name)

    if not role:
        role = utils.get(fetched_roles, name=role_name)

    if not role:
        print("Fetching role: ", role_name)
        role = await fetch_role(guild, role_name)

    return role
