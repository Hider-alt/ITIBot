from datetime import datetime

from src.mongo_repository.variations import Variations
import matplotlib.pyplot as plt

from src.utils.utils import clear_folder


weekdays = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


async def generate_plots(mongo_client):
    """
    It generates the plots for the variations

    :param mongo_client: Mongo client
    """
    clear_folder('data/plots/classes')
    clear_folder('data/plots/datetime')
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

    # Datetime plots
    await plot_variations_per_month(db)
    await plot_variations_per_weekday(db)
    await plot_variations_per_hour(db)


async def plot_variations_per_hour(db):
    variations_per_hour = await db.get_hourly_stats()

    # Create a barchart
    plt.bar(variations_per_hour.keys(), variations_per_hour.values())

    set_plot_config("Variazioni per ora", "Ore", "Numero di sostituzioni")

    # Save the plot
    plt.savefig('data/plots/datetime/hourly.png')
    plt.clf()


async def plot_variations_per_weekday(db):
    variations_per_weekday = await db.get_weekday_stats()

    # Convert the keys to weekdays
    x_values = [weekdays[key - 1] for key in variations_per_weekday.keys()]
    y_values = [variations_per_weekday[key] for key in variations_per_weekday.keys()]

    # Move the first element to the end (Sunday is after Saturday)
    x_values.append(x_values.pop(0))
    y_values.append(y_values.pop(0))

    # Create a barchart
    plt.bar(x_values, y_values)

    set_plot_config("Variazioni per giorno settimanale", "Giorni settimanali", "Numero di sostituzioni")

    # Save the plot
    plt.savefig('data/plots/datetime/weekly.png')
    plt.clf()


async def plot_variations_per_month(db):
    variations_per_month = await db.get_yearly_stats()

    # Convert the keys to months
    x_values = [months[key - 1] for key in variations_per_month.keys()]
    y_values = [variations_per_month[key] for key in variations_per_month.keys()]

    # Create a barchart
    plt.bar(x_values, y_values)

    set_plot_config("Variazioni per mese", "Mesi", "Numero di sostituzioni", rotation=90)

    # Save the plot
    plt.savefig('data/plots/datetime/monthly.png', bbox_inches='tight')
    plt.clf()


async def plot_professors_scoreboard(db):
    scoreboard = await db.get_professors_scoreboard()

    # Create a barchart
    y_values = [item['variations'] for item in scoreboard[:20]]
    plt.bar([item['_id'] for item in scoreboard[:20]], y_values)

    set_plot_config("Top 20 prof più assenti", "Prof.", "Ore di assenza dei prof.", rotation=90)

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

    set_plot_config("Overview proporzionale al numero di sezioni", "Classi", "Ore di assenza dei prof. per sezione")

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

    # Set generation date in top-right corner of the plot
    plt.text(0.99, 0.985, f"Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes, fontsize=8)

    plt.xticks(rotation=rotation)