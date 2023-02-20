import datetime
import json
import os
#import tabula
import camelot

import pandas as pd

from src.utils.datetime_utils import parse_italian_date
from src.utils.pandas_utils import reformat_csv
from src.utils.pdf_utils import save_PDF, fix_pdf, pages_to_csv

base_path = "data/downloads/"


async def create_csv_by_pdf(link):
    # Get last part of link
    filename = link.split('/')[-1][:-4].lower()
    filename = filename[len('variazioni-orario-'):(filename.index(datetime.datetime.strftime(datetime.datetime.now(), '%Y')) + 4)]  # 4 -> Year digits

    # Compose paths
    pdf_path = base_path + filename + ".pdf"
    fixed_folder = base_path + filename
    csv_path = base_path + filename + "_csv"

    # Download PDF
    await save_PDF(link, pdf_path)
    fix_pdf(pdf_path, fixed_folder, remove_original=False)

    # Convert PDFs to CSV
    pages_to_csv(fixed_folder, csv_path)
    #os.remove(rotated_path)

    # Open csv file
    csv = pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='windows-1252')

    # Remove empty columns
    csv = csv.dropna(axis='columns', how='all')
    print(csv)

    # Rename headers, because sometimes they aren't split correctly
    csv.columns = ['Ora', 'Classe', 'Doc.Assente', 'Sostituto 1', 'Sostituto 2', 'Pagam.', 'Note']
    # Remove useless columns
    #df = csv.drop(columns=['Ora', 'Pagam.', 'Firma'])
    df = csv

    # Add column after 'Classe' column named 'Aula', with value the 'Classe' one but only thing after ( and before ). Example: 5H(L5) -> L5
    df.insert(2, 'Aula', df['Classe'].str.split(r'\((.*?)\)', expand=True)[1].values)

    # Remove parenthesis from 'Classe' column. Example: 5H(L5) -> 5H
    df['Classe'] = df['Classe'].str.replace(r'\(.*?\)', '')

    # Rename second column
    #df.rename(columns={df.columns[0]: "Ora"}, inplace=True)

    # Create new csv file (reformatted)
    #reformat_csv(base_path + filename + "_edited.csv", df)

    # Save new csv file
    df.to_csv(base_path + filename + "_edited.csv", index=False, encoding='windows-1252')

    # Remove old csv file
    os.remove(csv_path)
    os.rename(base_path + filename + "_edited.csv", csv_path)

    return csv_path


def update_teachers_json(csv_path):
    date = parse_italian_date(csv_path[:-4])
    csv = pd.read_csv(csv_path, converters={i: str for i in range(0, 7)}, encoding='windows-1252')

    variations = create_variations_dict(csv, date)

    with open('data/new.json', 'w') as f:
        current_variations = json.load(f)
        current_variations.update(variations)
        json.dump(current_variations, f, indent=4)


def create_variations_dict(df, date: datetime) -> dict:
    """
    It creates a dictionary with the list of variations.

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
            "substitute_1": row['Sostituto 1'],
            "substitute_2": row['Sostituto 2'],
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


def clear_json(path):
    with open(path, 'w') as f:
        json.dump({}, f, indent=4)


def compare_json(old_path: str, new_path: str) -> tuple[list, list]:
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
                else:
                    # Teacher is not missing anymore
                    teachers_returned.append(variation)

    return teachers_missing, teachers_returned

