import gc
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
from paddleocr import TableRecognitionPipelineV2

from src.api.iti.variations_parsers._parser_ import PDFParser
from src.models.variation import Variation
from src.utils.os_utils import clear_folder
from src.utils.pdf_utils import save_pdf
from src.utils.utils import to_thread


class OCRParser(PDFParser):
    _pipeline = None

    def __init__(self):
        super().__init__()
        self.__required_headers = {'Ora', 'Classe', 'Aula', 'Docente assente', 'Sostituto 1', 'Sostituto 2', 'Note'}

    @staticmethod
    def _get_pipeline():
        if OCRParser._pipeline is None:
            try:
                OCRParser._pipeline = TableRecognitionPipelineV2(
                    text_detection_model_name="PP-OCRv5_server_det",
                    text_recognition_model_name="PP-OCRv5_server_rec",
                    text_detection_model_dir="assets/ocr-models/det/",
                    text_recognition_model_dir="assets/ocr-models/rec/",
                    use_doc_orientation_classify=True,
                    use_doc_unwarping=False
                )
            except Exception as e:
                print(f"Error initializing OCR pipeline: {e}")
                traceback.print_exc()
                raise e
        return OCRParser._pipeline

    async def _try_all_rotation_parsing(self, pdf: bytes) -> list[Variation] | None:
        return await self._parse(pdf)

    @to_thread
    def _parse(self, pdf: bytes) -> list[Variation] | None:
        now = datetime.now()
        pdf_path = f'assets/tmp-ocr/{now.timestamp()}.pdf'

        save_pdf(pdf, pdf_path)

        xlsx_files = self._convert_pdf_to_xlsx(pdf_path)

        df = self.__get_dataframe_from_xlsx(*xlsx_files)

        if not self.__check_headers(df):
            clear_folder('assets/tmp-ocr')
            return None

        variations = self.__parse_dataframe(df)

        clear_folder('assets/tmp-ocr')

        gc.collect()
        return variations

    def _convert_pdf_to_xlsx(self, pdf_path: str) -> tuple[str, ...]:
        """
        Converts a PDF file into one or more XLSX files using OCR.

        :param pdf_path: Path to the PDF file to be converted.
        :return: A tuple containing the paths to the generated XLSX files (one for each page).
        """

        def get_file_name(path: str) -> str:
            """
            Extracts the file name from the given path.
            """
            return Path(path).stem

        prediction = self._get_pipeline().predict(input=pdf_path)

        xlsx_files = []
        for i, page in enumerate(prediction):
            xlsx_path = f'assets/tmp-ocr/{get_file_name(pdf_path)}_page_{i + 1}.xlsx'
            page.save_to_xlsx(xlsx_path)

            xlsx_files.append(xlsx_path)

        return tuple(xlsx_files)

    @staticmethod
    def __get_dataframe_from_xlsx(*xlsx_files: str):
        """
        Reads the content of one or more XLSX files and returns a DataFrame.

        :param xlsx_files: Paths to the XLSX files.
        :return: A DataFrame containing the data from the XLSX files.
        """

        dataframes = [pd.read_excel(file) for file in xlsx_files]
        return pd.concat(dataframes, ignore_index=True)

    def __check_headers(self, df: pd.DataFrame) -> bool:
        """
        Checks if the DataFrame contains the required headers.

        :param df: The DataFrame to check.
        :return: True if the DataFrame contains all required headers, False otherwise.
        """

        headers = set(df.columns)
        return self.__required_headers.issubset(headers)

    @staticmethod
    def __parse_dataframe(df: pd.DataFrame) -> list[Variation]:
        """
        Parses the DataFrame and converts it into a list of Variation objects.

        :param df: The DataFrame to parse.
        :return: A list of Variation objects.
        """

        def fix_teacher_name(name: str) -> str:
            fixed = (name.split('-')[0]
                     .replace('_', ' ')
                     .replace('一', '')
                     .replace('.', '')
                     .replace("=", '')
                     .replace("…", '').strip())

            if name == 'nan':
                return '-'

            return fixed if fixed else '-'

        variations = []
        for _, row in df.iterrows():
            try:
                hour = int(str(row['Ora']))
            except ValueError:
                continue

            variation = Variation(
                hour=hour,
                class_name=str(row['Classe']),
                classroom=str(row['Aula']),
                teacher=fix_teacher_name(str(row['Docente assente'])),
                substitute_1=fix_teacher_name(str(row['Sostituto 1'])),
                substitute_2=fix_teacher_name(str(row['Sostituto 2'])),
                notes=str(row['Note']),
                ocr=True
            )

            variations.append(variation)

        return variations
