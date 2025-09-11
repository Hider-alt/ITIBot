from discord import Embed

from src.utils.discord_utils import notify_owner, get_or_fetch_channel, get_or_fetch_role


async def send_grouped_embeds(bot, grouped_embeds: dict[str, list[Embed]]) -> None:
    """
    It sends the embeds to the respective class channels.

    :param bot: Discord bot
    :param grouped_embeds: The embeds to send (Structured as in create_variations_embeds())
    :return: None
    """

    guild = bot.guild

    for class_name, embeds in grouped_embeds.items():
        class_role = await get_or_fetch_role(guild, class_name)
        if not class_role:
            await notify_owner(bot, f"Role {class_name} not found")
            continue

        # Find the channel for the class
        channel_name = f'variazioni-{class_name.lower()}'

        # Try using cache first, then fetch if not found
        class_channel = await get_or_fetch_channel(guild, channel_name)

        if not class_channel:
            await notify_owner(bot, f"Channel {channel_name} not found for class {class_name}")
            continue

        # Send the message in the class channel
        msg = await class_channel.send(content=class_role.mention, embeds=embeds)
        await msg.add_reaction("\U0001f389")
        await msg.add_reaction("\U0001f62d")

        # Send a message in the global channel (without mentions)
        await bot.log_channel.send(content=f"Classe: **{class_name}**", embeds=embeds)
