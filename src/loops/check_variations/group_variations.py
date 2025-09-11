from src.models.variation import Variation


def group_variations_by_class(variations: list[Variation]) -> dict[str, list]:
    """
    Groups variations by their class name.

    :param variations: A list of Variation objects.
    :return: A dictionary where keys are class names and values are lists of Variation objects.
    """
    grouped = {}

    for var in variations:
        class_name = var.class_name

        if class_name not in grouped:
            grouped[class_name] = []

        grouped[class_name].append(var)

    return grouped
