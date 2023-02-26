import datetime
import json
import os

import pandas as pd

from src.utils.datetime_utils import parse_italian_date
from src.utils.pdf_utils import save_PDF, fix_pdf, pdf_to_csv

base_path = "data/downloads/"


async def create_csv_by_pdf(link):
    # Get last part of link
    filename = link.split('/')[-1][:-4].lower()
    filename = filename[len('variazioni-orario-'):(filename.index(datetime.datetime.strftime(datetime.datetime.now(), '%Y')) + 4)]  # 4 -> Year digits

    # Compose paths
    pdf_path = base_path + filename + ".pdf"
    fixed_path = base_path + filename + "_fixed.pdf"
    csv_path = base_path + filename + ".csv"

    # Download PDF & fix it
    await save_PDF(link, pdf_path)
    fix_pdf(pdf_path, fixed_path, rotation_degrees=90, delete_original=False)

    # Convert PDF to CSV
    ok = pdf_to_csv(fixed_path, csv_path)
    if not ok:
        # Retry with a different rotation
        fix_pdf(pdf_path, fixed_path)
        ok = pdf_to_csv(fixed_path, csv_path)
        if not ok:
            raise Exception("Error while converting PDF to CSV")

    return csv_path


def update_teachers_json(csv_path):
    date = parse_italian_date(csv_path[:-4])
    csv = pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='windows-1252')

    # Replace NaN with empty string
    csv = csv.fillna('')

    variations: dict = create_variations_dict(csv, date)

    with open('data/new.json', 'r') as f:
        # Adds the new variations to the json file

        current_variations = json.load(f)
        current_variations.update(variations)

    with open('data/new.json', 'w') as f:
        json.dump(current_variations, f, indent=4)


def create_variations_dict(df, date: datetime) -> dict:
    """
    It creates a dictionary (json) with the list of variations (csv).

    :param df: The dataframe containing the variations
    :param date: The date of the variations
    :return: The dictionary with the variations by date
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


def get_classes(variations: list) -> list:
    """
    It gets the classes from the variations dictionary.

    :param variations: The variations dictionary
    :return: A list of classes
    """

    classes = []

    for variation in variations:
        if variation['class'] not in classes:
            classes.append(variation['class'])

    return classes


def refresh_json(new_path, old_path):
    with open(new_path, 'r') as f:
        new = json.load(f)

    with open(old_path, 'w') as f:
        json.dump(new, f, indent=4)

    os.remove(new_path)
    with open(new_path, 'w+') as f:
        json.dump({}, f, indent=4)


def compare_variations(new_path: str, old_path: str) -> tuple[list, list]:
    """
    It compares the old and the new variations json files and returns the differences.

    :param old_path: The path to the old variations JSON file
    :param new_path: The path to the just downloaded variations JSON file
    :return: The first list contains all teachers that are missing, the second list contains all teachers that are not missing anymore.
    """
    with open(old_path, 'r') as f:
        old = json.load(f)

    with open(new_path, 'r') as f:
        new = json.load(f)

    if old == new:
        return [], []

    teachers_missing = []
    teachers_returned = []

    for date, variations in new.items():
        if date not in old.keys():
            # Add all variations
            teachers_missing.extend(variations)
        else:
            for variation in variations:
                if variation not in old[date]:
                    # Add variation
                    teachers_missing.append(variation)

    for date, variations in old.items():
        if date not in new.keys():
            continue
        else:
            for variation in variations:
                if variation not in new[date]:
                    # Remove variation
                    teachers_returned.append(variation)

    return teachers_missing, teachers_returned

