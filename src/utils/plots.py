import math

from src.mongo_repository.variations import Variations
import matplotlib.pyplot as plt

from src.utils.utils import clear_folder


async def generate_plots(mongo_client):
    """
    It generates the plots for the variations

    :param mongo_client: Mongo client
    """
    clear_folder('data/plots/classes')
    clear_folder('data/plots/teachers')
    clear_folder('data/plots/subjects')

    db = Variations(mongo_client)

    # Classes plots
    for class_age in range(1, 6):
        await plot_per_class_age(db, class_age)

    await plot_summary(db)
    await plot_summary_per_class_number(db)

    # Professors plots
    await plot_professors_scoreboard(db)


async def plot_professors_scoreboard(db):
    scoreboard = await db.get_professors_scoreboard()

    # Create a barchart
    y_values = [item['variations'] for item in scoreboard]
    plt.bar([item['_id'] for item in scoreboard], y_values)

    set_plot_config("Istogramma prof.", "Prof.", "Ore di assenza dei prof.", rotation=90)

    # Save the plot
    plt.savefig('data/plots/teachers/professors_scoreboard.png', bbox_inches='tight')
    plt.clf()


async def plot_summary_per_class_number(db):
    summary = await db.get_variations_summary()

    # Count the number of classes for each class age
    classes_count = await db.get_classes_count()

    # Create a barchart
    # Number of variations is proportional to the number of classes for that class age
    y_values = [summary[key] / classes_count[key] for key in summary.keys()]
    plt.bar(list(summary.keys()), y_values)

    set_plot_config("Overview proporzionale al numero di sezioni", "Classi", "Ore di assenza dei prof.")

    # Save the plot
    plt.savefig('data/plots/classes/summary_per_class_number.png')
    plt.clf()


async def plot_summary(db):
    summary = await db.get_variations_summary()

    # Create a barchart
    plt.bar(list(summary.keys()), list(summary.values()))

    set_plot_config("Overview classi", "Classi", "Ore di assenza dei prof.")

    # Save the plot
    plt.savefig('data/plots/classes/summary.png')
    plt.clf()


async def plot_per_class_age(db, class_age):
    scoreboard = await db.get_variations_per_class_age(class_age)

    # Create a barchart
    y_values = [item['variations'] for item in scoreboard]
    plt.bar([item['_id'] for item in scoreboard], y_values)

    set_plot_config(f"Classi {class_age}°", "Classi", "Ore di assenza dei prof.")

    # Save the plot
    plt.savefig(f'data/plots/classes/class_{class_age}_scoreboard.png')
    plt.clf()


def set_plot_config(title, x_label, y_label, rotation=None):
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # Set major_locator to integer
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    plt.xticks(rotation=rotation)