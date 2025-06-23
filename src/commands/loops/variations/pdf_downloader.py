from asyncio import sleep

import aiohttp
from bs4 import BeautifulSoup


async def get_variations_links() -> list[str]:
    """
    It gets the links of the PDF files from the ITI page

    :return: A list of strings, each string is a link to a PDF file.
    """

    div_id = 'post-612'
    iti_url = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/"

    async with aiohttp.ClientSession() as session:
        async with session.get(iti_url, ssl=False) as response:
            iti_page = await response.text()

    soup = BeautifulSoup(iti_page, 'html.parser')

    # Get <a> elements of the page
    a = soup.find(id=div_id).find_all("div", {"class": "entry-content"})[0].find_all('a')

    # Get PDF links from <a> elements
    links = [link.get('href') for link in a]

    # Filter out links that do not match the conditions
    conditions = [
        lambda link: link.startswith('https://www.ispascalcomandini.it/wp-content/uploads/'),
        lambda link: 'parte2' not in link,
        lambda link: 'aule' not in link
    ]

    return [link for link in links if all(condition(link) for condition in conditions)]


async def download_and_save_PDF(url: str, path: str) -> None:
    """
    It downloads a PDF file from a given URL and saves it to a given path

    :param url: the url of the PDF you want to download
    :param path: The path to the file you want to save the PDF to
    """

    pdf = None
    tries = 0

    while tries < 5:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, ssl=False) as response:
                    pdf = await response.read()
        except aiohttp.ClientError:
            tries += 1
            await sleep(3)
            continue
        else:
            break

    if not pdf:
        raise Exception("Could not download PDF")

    with open(path, 'wb') as f:
        f.write(pdf)
