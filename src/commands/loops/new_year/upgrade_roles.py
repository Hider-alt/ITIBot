import re

from discord import Role, utils, Color

from src.api.iti.classes import ClassesAPI


async def upgrade_roles(bot) -> list[str]:
    current_roles: list[Role] = await bot.school_guild.roles

    # Remove "Diplomato" role
    current_roles = [role for role in current_roles if role.name != "Diplomato"]

    new_year_classes = await ClassesAPI.get_classes()

    new_roles = set(new_year_classes).difference(set(current_roles))
    await create_roles(bot, new_roles)

    await upgrade_users_roles(bot)

    remove_roles = set(current_roles).difference(set(new_year_classes))
    await delete_roles(remove_roles)

    return list(new_roles)


async def create_roles(bot, roles):
    for role_name in roles:
        try:
            await bot.school_guild.create_role(name=role_name, mentionable=False, hoist=True, colour=Color.random(), reason="New year roles creation")
        except Exception as e:
            print(f"Failed to create role {role_name}: {e}")


async def delete_roles(roles):
    for role in roles:
        try:
            await role.delete(reason="Class no longer exists")
        except Exception as e:
            print(f"Failed to delete role {role.name}: {e}")


async def upgrade_users_roles(bot):
    for member in bot.school_guild.members:
        # Check if member has any role with this regex pattern: \d[A-Z]+
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
