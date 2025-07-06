from src.api.iti.variations import VariationsAPI
from src.commands.analytics.plots import generate_plots
from src.commands.loops.check_variations.methods.new_ui import pdf_to_csv as new_ui
from src.commands.loops.check_variations.methods.new_ui_ocr import pdf_to_csv as new_ui_ocr
from src.commands.loops.check_variations.methods.old_ui import pdf_to_csv as old_ui
from src.utils.discord_utils import generate_embeds, send_embeds, merge_embeds
from src.utils.os_utils import clear_folder
from src.utils.pdf_utils import ConversionException
from src.utils.variations_utils import create_csv_from_pdf, fetch_variations_json, get_new_variations, merge_variations, \
    save_variations


async def refresh_variations(bot):
    """
    It checks for new check_variations and sends them to the log channel

    :param bot: Discord bot
    """

    clear_folder('data/downloads/')

    links = await VariationsAPI.get_variations_links()
    print(links)

    new = []
    for link in links:
        print(f"Fetching {link}")

        try:
            csv_conversion = await create_csv_from_pdf(link, [new_ui, old_ui, new_ui_ocr])
        except ConversionException as e:
            print(f"Error in conversion from PDF to CSV for {link}: {e}")
            continue

        new.append(await fetch_variations_json(csv_conversion))

    new = merge_variations(new)
    missing_teachers, returned_teachers = await get_new_variations(bot.mongo_client, new)

    await save_variations(bot.mongo_client, new)

    missing_embeds = generate_embeds(missing_teachers)
    returned_embeds = generate_embeds(returned_teachers, missing=False)

    merged_embeds = merge_embeds(missing_embeds, returned_embeds)
    if not merged_embeds:
        print("No changes")
        return

    await send_embeds(bot, bot.log_channel, merged_embeds)
    await generate_plots(bot.mongo_client)
