from src.utils.discord_utils import generate_embeds, send_embeds
from src.utils.os_utils import clear_folder
from src.utils.pdf_utils import get_pdf_links
from src.utils.variations_utils import create_csv_by_pdf, update_teachers_json, clear_json, compare_json

base_path = "data/downloads/"


async def check_variations(bot):
    clear_json('data/new.json')
    clear_folder(base_path)

    links = get_pdf_links()

    for link in links:
        csv_path = await create_csv_by_pdf(link)
        update_teachers_json(csv_path)

    missing_teachers, returned_teachers = compare_json('data/new.json', 'data/old.json')
    missing_embeds = generate_embeds(missing_teachers)
    returned_embeds = generate_embeds(returned_teachers, missing=False)

    await send_embeds(bot.school_guild, bot.log_channel, missing_embeds)
    await send_embeds(bot.school_guild, bot.log_channel, returned_embeds)
