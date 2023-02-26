import re

from discord import app_commands, Color
from discord.ext.commands import Cog
from src.commands.loops.check_teachers import check_variations


async def setup(bot):
    await bot.add_cog(Admin(bot))


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="refresh_variazioni", description="ADMIN ONLY")
    @app_commands.checks.has_permissions(administrator=True)
    async def refresh(self, itr):
        await itr.response.send_message("Refresh in corso...", ephemeral=True)
        await itr.response.defer()

        await check_variations(itr.client)

        await itr.edit_original_response(content="Variazioni refreshate")

    @app_commands.command(name="aggiungi_ruoli", description="ADMIN ONLY")
    @app_commands.describe(lista_classi="Lista delle classi prese dall'orario delle classi (prima pagina)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_roles(self, itr, lista_classi: str):
        await itr.response.send_message("Aggiornamento ruoli in corso...", ephemeral=True)

        # Get the list of roles in the server
        roles = itr.client.school_guild.roles

        # Example: "Year 1 Group 1A Group 1B" -> ["1A", "1B"]
        classes = re.findall(r'\d[A-Z]', lista_classi)

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