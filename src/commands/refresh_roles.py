import json
import re
from itertools import groupby

from discord import Color, Embed, ui, SelectOption, Interaction, utils, Role


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
        roles = [role for role in interaction.user.roles if re.match(r'\d[A-Z]', role.name)]
        if len(roles) > 0:
            await interaction.user.remove_roles(*roles, reason="User selected a new class")

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

    await send_select_role_message(itr.client)


async def send_select_role_message(client):
    # Send a message with the list of classes
    roles = client.school_guild.roles
    classes: list[Role] = [role.name for role in roles if re.match(r'\d[A-Z]', role.name)]

    # Group classes by first digit using groupby
    classes: list[list[str]] = [list(group) for _, group in groupby(classes, lambda x: x[0])]

    # Save classes to config.json
    with open("data/config.json", "r") as f:
        config = json.load(f)

    config['classes'] = classes

    with open("data/config.json", "w") as f:
        json.dump(config, f)

    embed = Embed(
        title="Seleziona la tua classe",
        color=Color.green()
    )

    await client.select_channel.send(embed=embed, view=SelectRoleView(classes))



