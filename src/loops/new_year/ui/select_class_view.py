import datetime
import re

from discord import ui, SelectOption, Interaction, utils, Embed, Color, Role, Member


class SelectClassView(ui.View):
    def __init__(self, classes: list[list[str]]):
        super().__init__(timeout=None)

        # Add a dropdown for each class list
        for class_list in classes:
            self.add_item(SelectClass(class_list))

    async def set_classes(self, classes: list[list[str]]) -> None:
        """Sets the classes for the view."""

        self.clear_items()

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

        # Check if it's summer
        now = datetime.datetime.now()
        if 6 <= now.month < 9:
            await itr.response.send_message(            # noqa
                embed=Embed(
                    title="Al momento non puoi cambiare ruolo",
                    description="I ruoli di tutti i membri verranno upgradati automaticamente a settembre e solo successivamente sarà possibile cambiarli manualmente.",
                    color=Color.red()
                ),
                ephemeral=True
            )
            return

        selected_class = self.values[0]
        user_roles = self.__get_user_roles(itr.user)

        await self.__remove_roles(itr.user, user_roles)
        ok = await self.__add_role(itr, selected_class)

        if not ok:
            await itr.response.send_message(            # noqa
                embed=Embed(
                    title="Errore...",
                    description=f"Il ruolo `{selected_class}` non esiste. Segnala il problema a {itr.client.owner.mention}",
                    color=Color.red()
                ),
                ephemeral=True
            )
            return

        await itr.response.send_message(                # noqa
            embed=Embed(
                title="Ruolo aggiunto",
                description=f"Quando ci sarà una variazione orario per questa classe, verrai taggato e vedrai il dettaglio della variazione nel canale #variazioni-{selected_class.lower()}",
                color=Color.green()
            ),
            ephemeral=True
        )

        # Clear selected values
        await itr.message.edit()

    @staticmethod
    def __get_user_roles(user) -> list[Role]:
        """
        Returns a list of roles that match the pattern \\d[A-Z]+ for the given user.
        """

        return [role for role in user.roles if re.match(r'\d[A-Z]+', role.name)]

    @staticmethod
    async def __remove_roles(user: Member, roles: list[Role]) -> None:
        """
        Removes all the roles from the user.

        :param user: The user to remove the roles from.
        :param roles: The roles to remove.
        """

        for role in roles:
            await user.remove_roles(role, reason="User selected a new class")

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
        return True
