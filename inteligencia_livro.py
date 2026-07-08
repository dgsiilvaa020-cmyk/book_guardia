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

    tags = []

    categorias = {

    "#romance": [
        "romance",
        "amor",
        "apaixon",
        "love"
    ],

    "#darkromance": [
        "dark romance",
        "dark",
        "obsessão",
        "obsession"
    ],

    "#fantasia": [
        "fantasia",
        "fantasy",
        "magic",
        "magia",
        "dragão",
        "dragon",
        "reino"
    ],

    "#romantasia": [
        "fae",
        "fadas",
        "elfo",
        "elf",
        "magia",
        "reino mágico"
    ],

    "#mafia": [
        "máfia",
        "mafia",
        "mafioso",
        "bratva",
        "camorra",
        "cosa nostra"
    ],

    "#lobisomem": [
        "lobisomem",
        "werewolf",
        "alpha",
        "beta",
        "mate",
        "alcateia"
    ],

    "#vampiro": [
        "vampiro",
        "vampire",
        "imortal",
        "blood"
    ],

    "#bruxas": [
        "bruxa",
        "witch",
        "feiticeira",
        "coven"
    ],

    "#realeza": [
        "rei",
        "rainha",
        "princesa",
        "príncipe",
        "castle",
        "coroa"
    ],

    "#bilionario": [
        "bilionário",
        "billionaire",
        "ceo",
        "empresário"
    ],

    "#faculdade": [
        "college",
        "campus",
        "universidade",
        "faculdade",
        "professor",
        "dormitório"
    ],

    "#harémreverso": [
        "reverse harem",
        "why choose"
    ]
}

    TROPES = {

    "#enemiestolovers": [
        "enemy",
        "enemy to lovers",
        "inimigos"
    ],

    "#friendstolovers": [
        "friends to lovers",
        "melhores amigos"
    ],

    "#slowburn": [
        "slow burn"
    ],

    "#arrangedmarriage": [
        "casamento arranjado",
        "arranged marriage"
    ],

    "#marriageofconvenience": [
        "casamento por contrato",
        "marriage of convenience"
    ],

    "#fatedmates": [
        "mate",
        "destinados",
        "alma gêmea"
    ],

    "#reverseharem": [
        "reverse harem",
        "why choose"
    ]
}

    TEMAS = {

    "#gravidezinesperada": [
        "gravidez",
        "pregnant",
        "unexpected pregnancy"
    ],

    "#bebê": [
        "bebê",
        "baby"
    ],

    "#vingança": [
        "vingança",
        "revenge"
    ],

    "#obsessão": [
        "obsessão",
        "obsession"
    ],

    "#MMRomance":[
        "mm romance",
        "male/male",
        "his boyfriend",
        "boyfriend",
        "he kissed him",
        "two men"
    ],

    "#FFRomance":[
        "ff romance",
        "female/female",
        "girlfriend",
        "she kissed her",
        "two women"
    ],

    "#magia": [
        "magia",
        "magic"
    ],

    "#dragões": [
        "dragão",
        "dragon"
    ],

    "#família": [
        "family",
        "família"
    ]
}

    for categoria, palavras in categorias.items():

        for palavra in palavras:

            if palavra in texto:
                tags.append("#" + categoria)
                break


    return tags[:3]



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
