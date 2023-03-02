from src.utils.discord_utils import generate_embeds, send_embeds, merge_embeds
from src.utils.utils import clear_folder
from src.utils.pdf_utils import get_variations_links
from src.utils.variations_utils import create_csv_by_pdf, update_teachers_json, refresh_json, compare_variations

base_path = "data/downloads/"


async def refresh_variations(bot):
    clear_folder(base_path)
    refresh_json('data/new.json', 'data/old.json')

    links = await get_variations_links()
    for link in links:
        print(link)
        csv_path = await create_csv_by_pdf(link)
        await update_teachers_json(csv_path)

    missing_teachers, returned_teachers = compare_variations('data/new.json', 'data/old.json')
    missing_embeds = generate_embeds(missing_teachers)
    returned_embeds = generate_embeds(returned_teachers, missing=False)

    merged_embeds = merge_embeds(missing_embeds, returned_embeds)
    if not merged_embeds:
        print("No changes")

    await send_embeds(bot, bot.log_channel, merged_embeds)
