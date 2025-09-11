from abc import abstractmethod, ABC

from src.models.variation import Variation
from src.utils.pdf_utils import rotate_pdf
from src.utils.utils import to_thread


class PDFParser(ABC):
    """
    An abstract base class for parsing PDF files to extract variations.
    """

    async def __call__(self, pdf: bytes) -> list[Variation] | None:
        """
        Allows the parser to be called as a function.

        :param pdf: The PDF file as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """
        return await self._try_all_rotation_parsing(pdf)

    @abstractmethod
    @to_thread
    def _parse(self, pdf: bytes) -> list[Variation] | None:
        """
        Parses the PDF and returns a list of variations.

        :param pdf: The PDF file as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """
        pass

    async def _try_all_rotation_parsing(self, pdf: bytes) -> list[Variation] | None:
        """
        Parses the PDF by trying all possible rotations (0, 90, 180, 270 degrees).

        :param pdf: The PDF file as bytes.
        :return: A list of Variation objects or None if parsing fails.
        """

        for rotation in range(0, 360, 90):
            try:
                rotated_pdf = rotate_pdf(pdf, rotation_degrees=rotation)

                variations = await self._parse(rotated_pdf)
                if variations:
                    return variations
            except Exception as e:
                print(f"Error during parsing with rotation {rotation}: {e}")

        return None
