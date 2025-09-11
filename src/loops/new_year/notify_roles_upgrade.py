from discord import Embed, Color


async def notify_roles_upgrade(bot):
    embed = Embed(
        title="I ruoli di tutti i membri sono stati upgradati",
        description=f"Se hai cambiato sezione rispetto all'anno precedente o sei stato bocciato, puoi selezionare la tua "
                    f"classe attuale nel canale {bot.select_channel.mention}",
        color=Color.green()
    ).set_footer(text=f"Nel canale #statistiche è stato inviato un recap delle statistiche dell'anno scorso")

    await bot.announce_channel.send(embed=embed, content="@everyone")
