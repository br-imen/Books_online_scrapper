import os
import requests
from bs4 import BeautifulSoup
import csv
import urllib.request
import pathlib
import ssl
import sys


"""
https://books.toscrape.com/index.html

    L'objectif c'est scraper tout le site books to scrape, la logique c'est accéder à chaque categorie 
    et dans chaque categorie j'accéde à tous les livres de chaque pages et je commence par le 1er livre de la catégorie,
    j'extrait ses données demandée et 
    je les collecte dans un dictionnaire
    de livre  et je l'ajoute dans une liste dédié de la catégorie, 
    et puis je passe au livre suivant et ainsi de suite jusqu'à la fin des pages de la catégorie.. 
    à la fin je charge la liste avec 
    des dictionnaires des livres d'une seule catégorie dans un fichier csv au nom de la catégorie 
    et l'image de chaque livre de la catégorie dans un dossier image et je passe à la catégorie suivante et ainsi de suite 
    jusqu'à la fin des catégories
    à la fin on a chargé tout les données on aura dans le dossier media: un dossier csv qui contient les fichier csv 
    et un dossier image contient les images.
"""

"""
    an absolute path for the local of user
"""
# To create an absolute path
ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))


# Main
def main():
    """
    il faut saisir l'argument qui est le lien du site qu'on va scraper,
    on va verifier s'il a bien saisie le lien et qu'un seul argument
    """
    # Get the url of website
    if len(sys.argv) == 1:
        sys.exit("Please enter the website's url to scrap")
    elif len(sys.argv) > 2:
        sys.exit("Too many arguments")
    else:
        """
        si c'est bon
        avec la fonction create_media_folder() : on va créer un folder media pour chargement des données.
        on va verifier si le site est valide, si invalide on va exit.
        si c'est ok, on va procéder à l'extraction des données:
        1) extraire tout les urls des catégories dans une liste list_url_categories
        2) looper cette liste des urls, donc on accéde à chaque categorie de la liste:
            3) on crée une liste data_books pour append aprés les dictionnaires des livres de cette categorie
            4) une liste des urls pages  list_url_pages pour parcourir tout les pages de la catégorie
            5) looper sur cette liste des urls pages pour accéder chaque page de la catégorie, dans chaque page:
                6) on aura une liste urls_books de la page actuelle de la loop
                7) on loop sur la liste des urls_books d'une page, pour accéder aux livres, dans le livre actuelle:
                    8) on crée un dictionnaire de livre ou on transfert les données demandées qu'on a extrait.
                    9) on append ce dictionnaire dans la liste data_books of categorie.
                10) load_books qui prends deux paramétres : la liste data_books et le nom de la catégorie
        """

        create_media_folder()
        url_page = sys.argv[1]
        r = requests.get(url_page)
        if r:
            # List of url all categories
            list_url_categories = get_url_categories(url_page)

            # loop over list of urls_categories
            for url_category in list_url_categories:
                """for every category, we make a list data_books of dictionaries of all books dict_books in that category"""
                data_books = []

                # list of url all pages for just one category to loop over
                list_url_pages = get_url_pages(url_category)

                # loop over  list of url pages list_url_pages of one category
                for page in list_url_pages:
                    """in every page, we get a list of url all books url_books for that page to loop over"""
                    urls_books = extract_url_books(page)

                    # loop over list urls_books to extract data and put it in a dict_book and append it in the list data_books
                    for url_book in urls_books:
                        dict_book = extract_book(url_book)
                        data_books.append(dict_book)

                # this to name the file.csv by category.
                category = data_books[0]["category"]

                # load data and image
                load_books_from_category(data_books, category)
        else:
            sys.exit("Sorry invalid url")


def create_media_folder():
    """
    create_media_folder() pour créer media folder avec deux dossiers image and csv
    """
    media_path = f"{ABSOLUTE_PATH}/media"
    image_path = f"{media_path}/image"
    csv_path = f"{media_path}/csv"
    if not os.path.exists(media_path):
        os.makedirs(media_path)
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)


# Get a list of url all categories:
def get_url_categories(url_page):
    """
    cette fonction get_url_categories prend comme un parametre le url du site à scraper.
    pour extraire les urls des categories sur home page du site, on utilise librairie beautiful soup qui va trouver les urls selon des tags 
    et les attributes de html du site.
    à la fin cette fonction elle retourne une liste url_categories
    """
    url_categories = []
    r = requests.get(url_page)
    if r:
        response = r.text
        soup = BeautifulSoup(response, "html.parser")
        parent = soup.find("ul", {"class": "nav nav-list"}).find("ul").find_all("a")
        for child in parent:
            href = "https://books.toscrape.com/" + child["href"]
            url_categories.append(href)

    return url_categories


# Get a list of urls all pages:
def get_url_pages(url):
    """
    ici une fonction qui va prendre l'url d'une categorie et retourne une liste de tous les urls des pages d'une categorie.
    on crée une liste qui contient le 1er page de la catégorie et dans une loop infinie:
        on cherche class: next en bas de la page 
        si il y a une erreur d'attribute error ça veut dire qu'il n' y a pas next
        donc c'est la fin des pages on s'arrete la et la fonction retourne une liste des urls des toutes les pages d'une 
        seule catégorie
    """
    list_url_pages = [url]
    while True:
        r = requests.get(url)
        if r:
            response = r.text
            soup = BeautifulSoup(response, "html.parser")
            try:
                next = soup.find("li", {"class": "next"}).find("a")["href"]
                url_splited_page = url.rsplit("/", 1)
                url_next_page = url_splited_page[0] + "/" + next
                list_url_pages.append(url_next_page)
                url = url_next_page
                pass
            except AttributeError:
                break
    return list_url_pages


# Get a list of urls products of one page:
def extract_url_books(url):
    """
    cette fonction prends un parametre url d'une seule page et retourne une liste des livres de cette page
    à l'aide de beautifulsoup on va chercher l'url de chaque livre en selectionant tous les div et on loope sur chacun 
    pour trouver le href de livre et retourne la liste de touts les urls des livres
    """
    r = requests.get(url)
    list_books = []
    if r:
        response = r.text
        soup = BeautifulSoup(response, "html.parser")
        products = soup.find_all("div", attrs={"class": "image_container"})
        for div in products:
            href = div.find("a")["href"]
            new_href = href.replace("../../..", "https://books.toscrape.com/catalogue")
            list_books.append(new_href)
    return list_books


# Scrap one product, all data of one book in dict
def extract_book(url_book):
    """
    EXTRACT & TRANSFORM
    cette function elle va prendre un url d'un livre et elle va retourner un dictionnaire des données demandées.
    on extrait les données demandées à l'aide de beautifulsoupe, en selectionnant des attributs,
    des tags de html précis ou on trouve la donnée, si elle n'existe pas, on la laisse vide.
    puis on ajoute la donnée comme valeur de son key name dans le dictionnaire.
    """
    r = requests.get(url_book)
    if r:
        response = r.text
        soup = BeautifulSoup(response, "html.parser")
        dict_book = {}

        # Url
        dict_book["product_page_url"] = url_book

        # title
        try:
            dict_book["title"] = soup.h1.string.strip()
        except AttributeError as e:
            print("Title", e)
            dict_book["title"] = ""

        # Upc
        try:
            upc = soup.table.find("th", string="UPC").find_next_sibling("td").string
            dict_book["universal_product_code(upc)"] = upc
        except AttributeError as e:
            print("upc", e)
            dict_book["universal_product_code(upc)"] = ""

        # Price including tax
        try:
            price_include_tax = (
                soup.table.find("th", string="Price (incl. tax)")
                .find_next_sibling("td")
                .string
            )
            dict_book["price_including_tax"] = price_include_tax
        except AttributeError as e:
            print("price inc", e)
            dict_book["price_including_tax"] = ""

        # Price excluding tax
        try:
            price_exclude_tax = (
                soup.table.find("th", string="Price (excl. tax)")
                .find_next_sibling("td")
                .string
            )
            dict_book["price_excluding_tax"] = price_exclude_tax
        except AttributeError as e:
            print("price ex", e)
            dict_book["price_excluding_tax"] = ""

        # Number available
        try:
            availabity = (
                soup.table.find("th", string="Availability")
                .find_next_sibling("td")
                .string
            )
            number_availability = ""
            for char in availabity:
                if char.isdigit():
                    number_availability += char
            dict_book["number_available"] = int(number_availability)
        except AttributeError as e:
            print("availability", e)
            dict_book["number_available"] = ""

        # Description
        try:
            product_description = (
                soup.find("div", {"id": "product_description"})
                .find_next_sibling("p")
                .string
            )
            dict_book["product_description"] = product_description
        except AttributeError as e:
            print("description", e)
            dict_book["product_description"] = ""

        # Url image
        try:
            image = soup.find("img")["src"]
            dict_book["image_url"] = image
        except AttributeError as e:
            print("url image", e)
            dict_book["image_url"] = ""

        # Star rating
        try:
            rating = soup.find("p", {"class": "instock availability"}).find_next("p")[
                "class"
            ]
            star = rating[1].lower()
            numbers = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            dict_book["review_rating"] = numbers[star]
        except AttributeError as e:
            print("rating", e)
            dict_book["review_rating"] = ""

        # Category
        try:
            category = soup.find("li").find_next("li").find_next("li").text.strip()
            dict_book["category"] = category
        except AttributeError as e:
            print("category", e)
            dict_book["category"] = ""

    return dict_book


# Load data of products of one category in one file.csv:
def load_books_from_category(list, category):
    """
    LOAD
    cette fonction permet le chargement des données dans le dossier media, elle prends deux parametres, une liste des dictionnaires
    de tous les livres d'une seule categorie.
    on nomme le fichier csv avec la variable category.
    on va ouvrir un fichier csv avec un path pour le dossier csv, fieldnames pour header ce sont les keys de dictionnaire,
    on prépare csv.dictwriter, on écrit le header et puis on va ecrire chaque ligne  en loupant la list, on writerow(element)
    et aprés on utilise la function load_image pour charger l'image dans le dossier image.
    """

    with open(f"{ABSOLUTE_PATH}/media/csv/{category}.csv", "w", newline="") as csvfile:
        fieldnames = []
        for key in list[0]:
            fieldnames.append(key)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for element in list:
            writer.writerow(element)
            load_image(element, category)
    return


# Load image:
def load_image(element, category):
    """
    LOAD
    cette function prend l'element un dictionnaire d'un livre, et le nom de category.
    avec urllib pour load l'image dans le path et on utilise ssl pour contourner le probléme de certificat. 
    """
    url_image = element["image_url"].replace("../..", "https://books.toscrape.com")
    url_book = element["product_page_url"].rsplit("/", 2)
    name_book = url_book[1]
    image_extension = pathlib.Path(url_image).suffix
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        urllib.request.urlretrieve(
            url_image,
            f"{ABSOLUTE_PATH}/media/image/{category}_{name_book}{image_extension}",
        )
    except ValueError as e:
        print(e, name_book)

    return


if __name__ == "__main__":
    main()
