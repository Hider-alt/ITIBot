import math

from src.mongo_repository.variations import Variations
import matplotlib.pyplot as plt

from src.utils.utils import clear_folder


async def generate_plots(mongo_client):
    """
    It generates the plots for the variations

    :param mongo_client: Mongo client
    """
    clear_folder('data/plots/')
    db = Variations(mongo_client)

    for class_age in range(1, 6):
        await plot_per_class_age(db, class_age)

    await plot_summary(db)
    await plot_summary_per_class_number(db)


async def plot_summary_per_class_number(db):
    summary = await db.get_variations_summary()

    # Count the number of classes for each class age
    classes_count = await db.get_classes_count()

    # Create a barchart
    # Number of variations is proportional to the number of classes for that class age
    y_values = [summary[key] / classes_count[key] for key in summary.keys()]
    plt.bar(list(summary.keys()), y_values)

    set_plot_config("Overview proporzionale al numero di classi per ciascun anno", "Classi", "Ore di assenza dei prof.", y_values)

    # Save the plot
    plt.savefig('data/plots/summary_per_class_number.png')
    plt.clf()


async def plot_summary(db):
    summary = await db.get_variations_summary()

    # Create a barchart
    plt.bar(list(summary.keys()), list(summary.values()))

    set_plot_config("Overview classi", "Classi", "Ore di assenza dei prof.", list(summary.values()))

    # Save the plot
    plt.savefig('data/plots/summary.png')
    plt.clf()


async def plot_per_class_age(db, class_age):
    scoreboard = await db.get_variations_per_class_age(class_age)

    # Create a barchart
    y_values = [item['variations'] for item in scoreboard]
    plt.bar([item['_id'] for item in scoreboard], y_values)

    set_plot_config(f"Classi {class_age}°", "Classi", "Ore di assenza dei prof.", y_values)

    # Save the plot
    plt.savefig(f'data/plots/class_{class_age}_scoreboard.png')
    plt.clf()


def set_plot_config(title, x_label, y_label, y_values):
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # Set MultipleLocator
    num_ticks = 10
    multiple_locator = 5 * math.ceil(max(y_values) / (num_ticks - 1) / 5)  # Round to the nearest multiple of 5
    if multiple_locator in [0, 5]:
        multiple_locator = 1
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(multiple_locator))
