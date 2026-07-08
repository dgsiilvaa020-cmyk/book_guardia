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

def criar_hashtags(texto, idioma):

    texto = texto.lower()


    if idioma == "PT":

        banco = {

            "#mafia": [
                "máfia",
                "mafioso",
                "cartel"
            ],

            "#dark": [
                "dark romance",
                "vingança",
                "obsessão"
            ],

            "#fantasia": [
                "magia",
                "dragão",
                "reino",
                "feitiço"
            ],

            "#romantasia": [
                "magia",
                "romance",
                "princesa"
            ],

            "#realeza": [
                "rei",
                "rainha",
                "principe",
                "princesa"
            ]

        }


    else:

        banco = {

            "#mafia": [
                "mafia",
                "gangster",
                "cartel"
            ],

            "#darkromance": [
                "dark romance",
                "revenge",
                "obsession"
            ],

            "#fantasy": [
                "magic",
                "dragon",
                "kingdom"
            ],

            "#romantasy": [
                "magic",
                "romance",
                "princess"
            ]

        }


    resultado = []


    for tag, palavras in banco.items():

        for palavra in palavras:

            if palavra in texto:

                resultado.append(tag)
                break


    return resultado[:3]

def analisar_livro(caminho):

    texto = ler_epub(caminho)

    idioma = descobrir_idioma(texto)

    hashtags = criar_hashtags(
        texto,
        idioma
    )


    return {
        "idioma": idioma,
        "hashtags": hashtags
    }
