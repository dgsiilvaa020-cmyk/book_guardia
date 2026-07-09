from ebooklib import epub
from bs4 import BeautifulSoup
from langdetect import detect

def criar_memoria_temporaria():

    return {

        "generos": {},

        "evidencias": {},

        "capitulos_lidos": 0,

        "frases_encontradas": []

    }
    

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

def ler_livro_completo(caminho):

    livro = epub.read_epub(caminho)

    capitulos = []


    for item in livro.get_items():

        if item.get_type() == 9:

            soup = BeautifulSoup(
                item.get_content(),
                "html.parser"
            )


            texto = soup.get_text(
                " ",
                strip=True
            )


            if texto:

                capitulos.append(texto)


    return capitulos

def analisar_contexto(texto, memoria):

    texto = texto.lower()


    regras = {


        "#harémreverso":[

            "reverse harem",
            "harém reverso",
            "why choose",
            "vários homens",
            "mais de um companheiro"

        ],


        "#darkromance":[

            "dark romance",
            "homem possessivo",
            "relacionamento obsessivo",
            "amor sombrio"

        ],


        "#fantasia":[

            "mundo mágico",
            "reino mágico",
            "criaturas sobrenaturais",
            "poderes mágicos",
            "feitiços"

        ],


        "#lobisomem":[

            "se transformou em lobo",
            "forma de lobo",
            "lua cheia",
            "matilha de lobos"

        ],


        "#mafia":[

            "chefe da máfia",
            "organização criminosa",
            "família mafiosa",
            "submundo criminoso"

        ]

    }



    for genero, frases in regras.items():


        for frase in frases:


            if frase in texto:


                memoria["generos"][genero] = (
                    memoria["generos"].get(genero, 0) + 1
                )


                if genero not in memoria["evidencias"]:

                    memoria["evidencias"][genero] = []


                memoria["evidencias"][genero].append(frase)
                
                memoria["frases_encontradas"].append(frase)

def analisar_livro_com_memoria(caminho):
    

    memoria = {

    "generos": {},

    "evidencias": {},

    "capitulos_lidos": 0,

    "frases_encontradas": [],

    "personagens": set(),

    "criaturas": set(),

    "locais": set(),

    "relacionamentos": [],

    "objetos_magicos": set(),

    "eventos": []

}


    capitulos = ler_livro_completo(caminho)


    for capitulo in capitulos:

        memoria["capitulos_lidos"] += 1

        analisar_contexto(
            capitulo,
            memoria
        )


    hashtags = sorted(
        memoria["generos"],
        key=memoria["generos"].get,
        reverse=True
    )


    resultado = hashtags[:3]


    memoria.clear()


    return resultado

def gerar_hashtags(texto):

    texto = texto.lower()

    banco = {

        "#darkromance":[
            "dark romance",
            "relacao obsessiva",
            "amor sombrio",
            "homem possessivo",
            "homem perigoso",
            "ele nao consegue deixa la ir",
            "obsessao por ela",
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
            "cartel",
            "família mafiosa",
            "império da máfia",
            "chefe da máfia",
            "líder da máfia",
            "submundo criminoso",
            "organização criminosa",
            "cartel de drogas",
            "família italiana",
            "clã mafioso",
            "bratva russa",
            "rei da máfia",
            "don da máfia"
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
            "fantasy",
            "mundo magico",
            "magia",
            "reino mágico",
            "reino encantado",
            "criaturas sobrenaturais",
            "poderes magicos",
            "feiticos",
            "profecia antiga",
            "guerra entre reinos"
        ],

        "#romantasia":[
            "romantasia"
        ],

        "#harémreverso":[
            "reverse harem",
            "reverseharem",
            "harém reverso",
            "why choose"
        ],

        "#bdsm":[
            "bdsm"
        ],

        "#vampiro":[
            "vampiro",
            "vampire",
            "mordida no pescoco",
            "sede de sangue",
            "imortal da noite"
        ],

        "#lobisomem":[
            "lobisomem",
            "werewolf",
            "homem lobo",
            "transformacao em lobo",
            "lua cheia"
        ],

        "#bruxas":[
            "bruxa",
            "witch"
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

        "#gravidez":[
            "gravidez", 
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
            "soulmates",
            "companheira destinada"
        ]
    }

    encontrados = []


    for hashtag, frases in banco.items():

        pontos = 0

        for frase in frases:

            if frase in texto:
                pontos += 1


        if pontos >= 1:
            encontrados.append(
                (hashtag, pontos)
            )


        encontrados.sort(
        key=lambda x:x[1],
        reverse=True
    )


    hashtags = [
        tag[0]
        for tag in encontrados[:3]
    ]


    # GARANTIA: sempre ter hashtag
    if not hashtags:

        hashtags = [
            "#romance"
        ]


    return hashtags


def garantir_hashtag(lista):

    lista_final = []

    for tag in lista:

        if not tag.startswith("#"):
            tag = "#" + tag

        lista_final.append(tag)

    if not lista_final:
        lista_final.append("#romance")

    return lista_final[:3]

def analisar_livro(caminho):

    hashtags = analisar_livro_com_memoria(caminho)

    if not hashtags:

        texto = ler_inicio_epub(caminho)

        hashtags = gerar_hashtags(texto)

    hashtags = garantir_hashtag(hashtags)

    return {

        "hashtags": hashtags

    }
