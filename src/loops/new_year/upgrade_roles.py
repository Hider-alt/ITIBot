import re

from discord import Role, utils, Color

from src.api.mim.classes import MIMClasses
from src.utils.discord_utils import notify_owner


async def upgrade_roles(bot) -> set[str] | None:
    """
    It upgrades the roles of the users in the server.

    :param bot: The bot instance
    :return: A list of current roles (classes only) in the guild, or None if there was an error.
    """

    # Keep only roles that match the regex pattern: \d[A-Z]+
    current_roles = await bot.guild.fetch_roles()
    current_roles: set[Role] = set([role for role in current_roles if re.match(r'\d[A-Z]+', role.name)])
    current_roles_names = set(role.name for role in current_roles)

    try:
        new_year_classes = await MIMClasses.get_classes()
    except ValueError:
        await notify_owner(bot, "Failed to get new year classes")
        return None
    else:
        # Notify owner with new classes
        await notify_owner(bot, f"New year classes:\n{group_classes(new_year_classes)}")

    new_roles = new_year_classes.difference(current_roles_names)
    print(f"Creating new roles: {new_roles}")
    await create_roles(bot.guild, new_roles)

    await upgrade_users_roles(bot)

    remove_roles: set[Role] = set(role for role in current_roles if role.name not in new_year_classes)
    print(f"Removing roles: {set(role.name for role in remove_roles)}")
    await delete_roles(remove_roles)

    # return current_roles - removed_roles + new_roles
    return (current_roles_names - set(role.name for role in remove_roles)).union(new_roles)


async def create_roles(guild, roles: set[str]):
    for role_name in roles:
        try:
            await guild.create_role(name=role_name, mentionable=False, hoist=True, colour=Color.random(), reason="New year roles creation")
        except Exception as e:
            print(f"Failed to create role {role_name}: {e}")


async def delete_roles(roles: set[Role]):
    for role in roles:
        try:
            await role.delete(reason="Class no longer exists")
        except Exception as e:
            print(f"Failed to delete role {role}: {e}")


async def upgrade_users_roles(bot):
    async for member in bot.guild.fetch_members(limit=None):
        # Check if member has any role with this regex pattern: \d[A-Z]+, if not, skip
        if not any(re.match(r'\d[A-Z]+', role.name) for role in member.roles):
            continue

        for role in member.roles:
            await upgrade_year(member, role)


async def upgrade_year(member, role: Role):
    """
    Upgrade the year of the user by removing the current role and adding the next one.
    """

    match = re.match(r'(\d)([A-Z]+)', role.name)
    if not match:
        return

    year = int(match.group(1))
    class_name = match.group(2)
    new_year = year + 1

    # Remove current role
    await member.remove_roles(role, reason="Upgrading year")

    # Handle special case for 5th year
    if new_year > 5:
        await add_degree_role(member)
        return

    # Add next year role
    next_year_role_name = f"{year + 1}{class_name}"
    next_year_role = utils.get(member.guild.roles, name=next_year_role_name)

    if next_year_role:
        await member.add_roles(next_year_role, reason="Upgrading year")


async def add_degree_role(member):
    """
    Add the "Diplomato" role to the user.
    """

    degree_role = utils.get(member.guild.roles, name="Diplomato")
    if not degree_role:
        degree_role = await member.guild.create_role(name="Diplomato", mentionable=False, hoist=True, colour=0xFFD700, reason="Role for graduated students")

    await member.add_roles(degree_role, reason="Graduated from ITI Blaise Pascal")


def group_classes(classes: set[str]) -> str:
    """
    It creates a string that groups classes by their first digit and sorts each group alphabetically.

    :param classes: A set of class names (e.g. "1A", "2B", "3C").
    :return: A formatted string with grouped classes.
    """

    grouped = {}
    for cls in classes:
        year = cls[0]
        if year not in grouped:
            grouped[year] = []
        grouped[year].append(cls)

    result = []
    for year in sorted(grouped.keys()):
        sorted_classes = sorted(grouped[year])
        result.append(f"{year}: " + ", ".join(sorted_classes))

    return "\n".join(result)
