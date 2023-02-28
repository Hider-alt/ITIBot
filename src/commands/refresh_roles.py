import json
import re
from itertools import groupby

from discord import Color, Embed, ui, SelectOption, Interaction, utils, Role, PermissionOverwrite


class SelectRoleView(ui.View):
    def __init__(self, classes: list[list[str]]):
        super().__init__(timeout=None)

        for class_list in classes:
            self.add_item(SelectClass(class_list))

class SelectClass(ui.Select):
    def __init__(self, classes: list[str]):
        super().__init__()
        self.max_values = 1
        self.custom_id = f"select_class_{classes[0][0]}"
        self.placeholder = f"Classe {classes[0][0]}"
        self.options = [SelectOption(label=class_name) for class_name in classes]

    async def callback(self, interaction: Interaction):
        # Check if the user has any role that matches the pattern \d[A-Z]
        user_roles = [role for role in interaction.user.roles if re.match(r'\d[A-Z]', role.name)]

        if self.values[0] in [role.name for role in user_roles]:
            await interaction.user.remove_roles(utils.get(interaction.guild.roles, name=self.values[0]), reason="User removed this role")
            await interaction.response.send_message(
                embed=Embed(
                    title="Ruolo rimosso",
                    color=Color.red()
                ),
                ephemeral=True
            )

            await interaction.message.edit()
            return

        if len(user_roles) > 0:
            await interaction.user.remove_roles(*user_roles, reason="User selected a new class")

        # Add the selected role to the user
        await interaction.user.add_roles(utils.get(interaction.guild.roles, name=self.values[0]), reason="User selected a new class")

        await interaction.message.edit()

        await interaction.response.send_message(
            embed=Embed(
                title="Ruolo aggiunto",
                color=Color.og_blurple()
            ),
            ephemeral=True
        )



async def refresh_roles(itr, class_list):
    # Get the list of roles in the server
    roles = itr.client.school_guild.roles

    # Example: "Year 1 Group 1A Group 1B" -> ["1A", "1B"]
    classes = re.findall(r'\d[A-Z]', class_list)

    # Remove roles that are not in the list of classes and respect the pattern \d[A-Z]
    for i, role in enumerate(roles):
        if role.name not in classes and re.match(r'\d[A-Z]', role.name):
            print(f"Deleting role {role.name}")
            await role.delete(reason="Role not in the list of classes")

    roles_names = [role.name for role in roles]

    # Create roles for each class
    for class_name in classes:
        if class_name not in roles_names:
            await itr.client.school_guild.create_role(name=class_name, mentionable=True, colour=Color.random())

    # Send a message with the list of classes
    if len(classes) == 0:
        await itr.edit_original_response(content="Nessuna classe trovata")
    else:
        await itr.edit_original_response(content="Classi rilevate dal testo: " + ", ".join(classes))

    # Group classes by first digit using groupby
    classes = [list(group) for _, group in groupby(classes, lambda x: x[0])]

    # Save classes to config.json
    with open("data/config.json", "r") as f:
        config = json.load(f)

    config['classes'] = classes

    with open("data/config.json", "w") as f:
        json.dump(config, f)

    await send_select_role_message(itr.client, classes)
    await create_channels(itr.client, classes)


async def send_select_role_message(client, classes: list[list[str]]):
    embed = Embed(
        title="Seleziona la tua classe",
        color=Color.green()
    )

    await client.select_channel.send(embed=embed, view=SelectRoleView(classes))


async def create_channels(client, classes: list[list[str]]):
    classes_names = [class_name for class_list in classes for class_name in class_list]

    # Delete all channels that start with "variazioni-orario-" and are not in the list of classes already created
    for channel in await client.school_guild.fetch_channels():
        if channel.name.startswith("variazioni-orario-") and channel.name[:-2] not in classes_names:
            print(f"Deleting channel {channel.name}")
            await channel.delete(reason="Channel already exists")

    # Permissions
    every_perms = PermissionOverwrite()
    every_perms.view_channel = False

    role_perms = PermissionOverwrite()
    role_perms.send_messages = False
    role_perms.read_messages = True
    role_perms.read_message_history = True

    bot_perms = PermissionOverwrite()
    bot_perms.send_messages = True
    bot_perms.add_reactions = True

    # Create channels for each class
    for class_list in classes:
        # Get the category for the class or create it if it doesn't exist
        category = utils.get(client.school_guild.categories, name=class_list[0][0])
        if category is None:
            category = await client.school_guild.create_category(name=class_list[0][0])  # Get the first digit of the class name

        for class_name in class_list:
            channel_name = "variazioni-orario-" + class_name
            if utils.get(category.text_channels, name=channel_name) is not None:  # Check if the channel already exists
                continue

            await client.school_guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites={
                    client.school_guild.default_role: every_perms,
                    utils.get(client.school_guild.roles, name=class_name): role_perms,
                    utils.get(client.school_guild.roles, name="ITI Cesena"): bot_perms
                }
            )
