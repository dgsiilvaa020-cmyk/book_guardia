from ebooklib import epub
from bs4 import BeautifulSoup
from langdetect import detect


def ler_inicio_epub(caminho):

    livro = epub.read_epub(caminho)

    textos = []

    for item in livro.get_items():

        if item.get_type() == 9:  # documento HTML

            soup = BeautifulSoup(
                item.get_content(),
                "html.parser"
            )

            texto = soup.get_text(" ", strip=True)

            if texto:
                textos.append(texto)


    texto_final = "\n".join(textos)

    # pega somente o começo
    inicio = texto_final[:15000]

    return inicio

def gerar_hashtags(texto):

    texto = texto.lower()

    banco = {

        "#darkromance":[
            "dark romance",
            "dark",
            "obsessão",
            "obsession"
        ],

        "#mafia":[
            "máfia",
            "mafia",
            "mafioso",
            "bratva",
            "camorra",
            "cartel"
        ],

        "#harémreverso":[
            "reverse harem",
            "harém reverso",
            "why choose"
        ],

        "#bdsm":[
            "bdsm"
        ],

        "#romance":[
            "romance",
            "amor",
            "love"
        ],

        "#fantasia":[
            "fantasia",
            "fantasy"
        ],

        "#romantasia":[
            "romantasia"
        ],

        "#vampiro":[
            "vampiro",
            "vampire"
        ],

        "#lobisomem":[
            "lobisomem",
            "werewolf"
        ],

        "#bruxas":[
            "bruxa",
            "witch"
        ],

        "#realeza":[
            "rei",
            "rainha",
            "princesa",
            "príncipe"
        ],

        "#bilionario":[
            "bilionário",
            "billionaire",
            "ceo"
        ],

        "#faculdade":[
            "college",
            "campus",
            "universidade",
            "faculdade"
        ],

        "#MMRomance":[
            "mm romance",
            "male/male"
        ],

        "#FFRomance":[
            "ff romance",
            "female/female"
        ],

        "#gravidezinesperada":[
            "gravidez inesperada",
            "unexpected pregnancy"
        ],

        "#bebê":[
            "bebê",
            "baby"
        ],

        "#enemiestolovers":[
            "enemies to lovers"
        ],

        "#friendstolovers":[
            "friends to lovers"
        ],

        "#slowburn":[
            "slow burn"
        ],

        "#arrangedmarriage":[
            "arranged marriage"
        ],

        "#marriageofconvenience":[
            "marriage of convenience"
        ],

        "#fatedmates":[
            "fated mates",
            "soulmates"
        ]
    }

    encontrados = []

    for hashtag, palavras in banco.items():

        for palavra in palavras:

            if palavra in texto:

                encontrados.append(hashtag)

                break

    return encontrados[:3]

def descobrir_idioma(texto):

    try:

        idioma = detect(texto)

        if idioma == "en":
            return "EN"

        return "PT"

    except:

        return "PT"
        

    for tag, palavras in banco.items():

        for palavra in palavras:

            if palavra in texto:

                resultado.append(tag)
                break


    return resultado[:3]

def analisar_livro(caminho):

    texto = ler_inicio_epub(caminho)

    idioma = descobrir_idioma(texto)

    hashtags = gerar_hashtags(texto)


    return {
        "idioma": idioma,
        "hashtags": hashtags
    }
