from ebooklib import epub
from bs4 import BeautifulSoup
from langdetect import detect


def ler_epub(caminho):

    livro = epub.read_epub(caminho)

    texto = ""

    capitulos = 0


    for item in livro.get_items():

        if item.get_type() == 9:

            html = item.get_content()

            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            texto += soup.get_text(
                " ",
                strip=True
            )


            capitulos += 1


            # não lê o livro inteiro
            if capitulos >= 10:
                break


    return texto



def descobrir_idioma(texto):

    try:

        idioma = detect(texto)

        if idioma == "en":
            return "EN"

        return "PT"

    except:

        return "PT"
