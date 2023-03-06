from src.utils.discord_utils import generate_embeds, send_embeds, merge_embeds
from src.utils.pdf_utils import get_variations_links
from src.utils.plots import generate_plots
from src.utils.utils import clear_folder
from src.utils.variations_utils import create_csv_by_pdf, fetch_variations_json, get_new_variations, merge_variations, \
    save_variations


async def refresh_variations(bot):
    """
    It checks for new variations and sends them to the log channel

    :param bot: Discord bot
    """
    clear_folder('data/downloads/')
    links = await get_variations_links()

    new = []
    for link in links:
        print(f"Fetching {link}")
        csv_path = await create_csv_by_pdf(link)
        new.append(await fetch_variations_json(csv_path))

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
