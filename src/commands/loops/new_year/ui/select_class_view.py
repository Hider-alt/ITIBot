import re

from discord import ui, SelectOption, Interaction, utils, Embed, Color


class SelectClassView(ui.View):
    def __init__(self, classes: list[list[str]]):
        super().__init__(timeout=None)

        # Add a dropdown for each class list
        for class_list in classes:
            self.add_item(SelectClass(class_list))


class SelectClass(ui.Select):
    def __init__(self, classes: list[str]):
        super().__init__()
        self.max_values = 1
        self.custom_id = f"select_class_{classes[0][0]}"
        self.placeholder = f"Classe {classes[0][0]}"
        self.options = [SelectOption(label=class_name) for class_name in classes]

    async def callback(self, itr: Interaction):
        """Handles the selection of a class from the dropdown."""

        selected_class = self.values[0]
        user_roles = self.__get_user_roles(itr.user)

        action = self.__get_user_action(selected_class, user_roles)

        if action == "remove":
            ok = await self.__remove_role(itr, selected_class)
        else:
            ok = await self.__add_role(itr, selected_class)

        if not ok:
            await itr.response.send_message(            # noqa
                embed=Embed(
                    title="Qualcosa è andato storto",
                    description=f"Il ruolo `{selected_class}` non esiste. Segnala il problema a {itr.client.owner.mention}",
                    color=Color.red()
                ),
                ephemeral=True
            )
            return

    @staticmethod
    def __get_user_roles(user):
        """
        Returns a list of roles that match the pattern \d[A-Z]+ for the given user.
        """

        return [role for role in user.roles if re.match(r'\d[A-Z]+', role.name)]

    @staticmethod
    def __get_user_action(selected_class: str, user_roles: list) -> str:
        """
        Determines whether to add or remove a class based on the user's current roles.

        :param selected_class: User selected class name in the dropdown.
        :param user_roles: List of classes the user currently has.
        :return: "remove" if the selected class is already in user roles, otherwise "add".
        """

        roles_names = [role.name for role in user_roles]

        return "remove" if selected_class in roles_names else "add"

    @staticmethod
    async def __remove_role(itr: Interaction, selected_class: str) -> bool:
        """
        Removes the selected class from the user and sends a confirmation message.

        :param itr: The interaction object.
        :param selected_class: The class to remove.

        :return: True if the role was successfully removed, False otherwise.
        """

        role = utils.get(itr.guild.roles, name=selected_class)

        if not role:
            return False

        await itr.user.remove_roles(role, reason="User removed this role")
        await itr.response.send_message(            # noqa
            embed=Embed(
                title="Ruolo rimosso",
                color=Color.red()
            ),
            ephemeral=True
        )

        return True

    @staticmethod
    async def __add_role(itr: Interaction, selected_class: str) -> bool:
        """
        Adds the selected class to the user and sends a confirmation message.

        :param itr: The interaction object.
        :param selected_class: The class to add.

        :return: True if the role was successfully added, False otherwise.
        """

        role = utils.get(itr.guild.roles, name=selected_class)

        if not role:
            return False

        await itr.user.add_roles(role, reason="User selected a new class")
        await itr.response.send_message(                # noqa
            embed=Embed(
                title="Ruolo aggiunto",
                color=Color.og_blurple()
            ),
            ephemeral=True
        )

        return True
