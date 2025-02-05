import datetime
import re

from src.commands.loops.variations.pdf_downloader import save_PDF
from src.mongo_repository.variations import Variations
from src.utils.datetime_utils import parse_italian_date
from src.utils.pdf_utils import rotate_pdf, ConversionException
from src.utils.utils import read_csv_pandas


async def create_csv_from_pdf(link, methods: list) -> str:
    """
    It takes a link to a PDF file, downloads it, fixes it, converts it to a CSV file, and saves it to a given path

    :param link: The link to the PDF file
    :param methods: The methods to convert the PDF to CSV
    :return: Returns the path to the CSV file
    """

    downloads_path = "data/downloads/"

    # Find <day (int)>-<month (str)> in the filename (with regex), then save <weekday>-<day>-<month>-<year>
    filename = link.split('/')[-1][:-4].lower()
    date = re.search(r'\d+-\w+', filename).group(0)
    date = parse_italian_date(date)
    filename = datetime.datetime.strftime(date, '%d-%m-%Y')

    # Compose paths
    pdf_path = downloads_path + filename + ".pdf"
    rotated_path = downloads_path + filename + "_rotated.pdf"
    csv_path = downloads_path + filename + ".csv"

    # Download PDF & fix it
    await save_PDF(link, pdf_path)

    # Convert PDF to CSV
    for i, method in enumerate(methods):
        ok = False

        # Try with different rotation, incrementing by 90)
        for j in range(0, 360, 90):
            print(f"Trying method {i} with rotation {j}")
            rotate_pdf(pdf_path, rotated_path, rotation_degrees=j, delete_original=False)

            ok = await method(rotated_path, csv_path, delete_original=False)

            if ok:
                break

        if ok:
            break
    else:
        raise ConversionException("Error while converting PDF to CSV")

    return csv_path


async def fetch_variations_json(csv_path) -> dict:
    """
    It updates the teachers in the database with the variations from the given CSV file.

    :param csv_path: The path to the CSV file
    """

    date = datetime.datetime.strptime(csv_path.split('/')[-1][:-4], '%d-%m-%Y')
    csv = await read_csv_pandas(csv_path)

    # Replace NaN with empty string
    csv = csv.fillna('')

    return create_variations_dict(csv, date)


def create_variations_dict(df, date: datetime) -> dict:
    """
    It creates a dictionary with the variations from the given CSV file.

    :param df: The CSV file
    :param date: The date of the variations
    """

    date = datetime.datetime.strftime(date, '%d-%m-%Y')
    daily_variations = {date: []}

    for index, row in df.iterrows():
        daily_variations[date].append({
            "date": date,
            "teacher": row['Doc.Assente'],
            "hour": row['Ora'],
            "class": row['Classe'],
            "classroom": row['Aula'],
            "substitute_1": row['Sost.1'],
            "substitute_2": row['Sost.2'],
            "notes": row['Note']
        })

    return daily_variations


def merge_variations(variations: list[dict]) -> dict:
    """
    It merges the variations from different days into a single dictionary.

    :param variations: The list of variations to merge
    :return: The merged dictionary
    """

    merged = {}

    for variation in variations:
        for date, teachers in variation.items():
            if date not in merged.keys():
                merged[date] = teachers
            else:
                merged[date].extend(teachers)

    return merged


async def get_new_variations(mongo_client, new: dict) -> tuple[list, list]:
    """
    It compares the old and the new variations and returns the differences.

    :param new: The variations fetched from the PDF files
    :param mongo_client: The MongoDB client

    :return: The first list contains all teachers that are missing, the second list contains all teachers that are not missing anymore.
    """
    db = Variations(mongo_client)

    teachers_missing = []
    teachers_returned = []

    dates = list(new.keys())

    for date, variations in new.items():
        old = await db.get_variations_by_date(date)
        if not old:
            # Add all variations
            teachers_missing.extend(variations)
        else:
            for variation in variations:
                if variation not in old:
                    # Add variation
                    teachers_missing.append(variation)

    for date in dates:
        old = await db.get_variations_by_date(date)
        for variation in old:
            if variation not in new[date]:
                # Remove variation
                teachers_returned.append(variation)

    return teachers_missing, teachers_returned


async def save_variations(mongo_client, variations: dict):
    """
    It saves the variations to the database.

    :param variations: The variations to save
    :param mongo_client: The MongoDB client
    """

    db = Variations(mongo_client)
    await db.save_variations(variations)
