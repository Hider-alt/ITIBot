from datetime import datetime

from src.commands.loops.variations.methods.new_ui import pdf_to_csv as pdf_to_csv_new_ui
from src.commands.loops.variations.methods.new_ui_ocr import pdf_to_csv as pdf_to_csv_ocr
from src.commands.loops.variations.methods.old_ui import pdf_to_csv as pdf_to_csv_old_ui
from src.commands.loops.variations.pdf_downloader import get_variations_links
from src.utils.discord_utils import generate_embeds, merge_embeds, send_embeds
from src.utils.pdf_utils import ConversionException
from src.utils.plots import generate_plots
from src.utils.utils import clear_folder
from src.utils.variations_utils import create_csv_from_pdf, fetch_variations_json, merge_variations, get_new_variations, \
    save_variations


async def run_ocr(bot):
    now = datetime.now().hour

    # Skip if time 0 < now < 7
    if 0 < now < 7:
        return

    clear_folder('data/downloads/')

    links = await get_variations_links()
    print(links)

    # Run OCR only for links that failed to convert
    final_links = []
    for link in links:
        try:
            await create_csv_from_pdf(link, [pdf_to_csv_new_ui, pdf_to_csv_old_ui])
        except ConversionException as e:
            print(f"Error in conversion from PDF to CSV for {link}: {e}")
            final_links.append(link)
            continue

    links = final_links
    if not links:
        print("No new variations")
        return

    new = []
    for link in links:
        print(f"Fetching {link}")

        try:
            csv_conversion = await create_csv_from_pdf(link, [pdf_to_csv_ocr])
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

    await send_embeds(bot, bot.log_channel, merged_embeds, ocr=True)
    await generate_plots(bot.mongo_client)
