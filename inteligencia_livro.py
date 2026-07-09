from ebooklib import epub
from bs4 import BeautifulSoup
from langdetect import detect

def criar_memoria_livro():

    return {

        "capitulos_analisados": 0,

        "generos": {},

        "evidencias": {},

        "personagens": {},

        "frases_importantes": []

    }

def adicionar_evidencia(memoria, genero, evidencia, peso):

    if genero not in memoria["generos"]:

        memoria["generos"][genero] = 0


    memoria["generos"][genero] += peso


    if genero not in memoria["evidencias"]:

        memoria["evidencias"][genero] = []


    memoria["evidencias"][genero].append(evidencia)


def analisar_capitulo_memoria(texto, memoria):

    texto = texto.lower()


    memoria["capitulos_analisados"] += 1


    # LOBISOMEM

    if "alfa" in texto:
        adicionar_evidencia(
            memoria,
            "#lobisomem",
            "alfa encontrado",
            5
        )


    if "matilha" in texto:
        adicionar_evidencia(
            memoria,
            "#lobisomem",
            "matilha encontrada",
            10
        )


    if "transformação" in texto or "transformacao" in texto:
        adicionar_evidencia(
            memoria,
            "#lobisomem",
            "transformação encontrada",
            10
        )


    # FANTASIA

    if "magia" in texto:

        adicionar_evidencia(
            memoria,
            "#fantasia",
            "magia encontrada",
            5
        )
    

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
    
    paragrafos = texto.split("\n")

    regras = {


        "#harémreverso":[

            "harém reverso",
            "multiple mates",
            "mais de um companheiro",
            "mais de um parceiro",
            "eles me querem",
            "meus companheiros",
            "companheiros",
            "múltiplos companheiros",

        ],

        "#darkromance":[

            "dark romance",
            "homem possessivo",
            "relacionamento obsessivo",
            "amor sombrio"

        ],

        "#fantasia":[

            "fantasia",
            "fantasy",
            "magia",
            "mágica",
            "magico",
            "mágico",
            "feiticeiro",
            "feiticeira",
            "feitiço",
            "feitiços",
            "bruxa",
            "bruxo",
            "mago",
            "reino",
            "castelo",
            "dragão",
            "dragao",
            "elfo",
            "elfos",
            "fada",
            "fadas",
            "demônio",
            "demonio",
            "anjo",
            "profecia",
            "portal",
            "mundo mágico",
            "criaturas sobrenaturais",
            "poderes mágicos"

        ],

        "#lobisomem":[

            "lobisomem",
            "werewolf",
            "alfa",
            "beta",
            "ômega",
            "omega",
            "mate",
            "companheira destinada",
            "companheiro destinado",
            "matilha",
            "alcateia",
            "transformação",
            "transformacao",
            "forma de lobo",
            "cheiro",
            "feromônio",
            "feromonio",
            "marcação",
            "marcacao",
            "lua cheia"

        ],

        "#mafia":[

            "chefe da máfia",
            "organização criminosa",
            "família mafiosa",
            "submundo criminoso"

        ]

    }

    for paragrafo in paragrafos:

        paragrafo = paragrafo.lower()

        for genero, palavras in regras.items():

            pontos = 0

            for palavra in palavras:

                ocorrencias = paragrafo.count(palavra)

                if ocorrencias > 0:

                    pontos += ocorrencias

                    if genero not in memoria["evidencias"]:
                        memoria["evidencias"][genero] = []

                    memoria["evidencias"][genero].append(
                        f"{palavra} ({ocorrencias}x)"
                    )

                    memoria["frases_encontradas"].append(palavra)

            if pontos > 0:
                memoria["generos"][genero] = (
                    memoria["generos"].get(genero, 0) + pontos
                )

def analisar_livro_com_memoria_nova(caminho):

    memoria = criar_memoria_livro()

    capitulos = ler_livro_completo(caminho)


    for capitulo in capitulos:

        analisar_capitulo_memoria(
            capitulo,
            memoria
        )


    return memoria

def escolher_hashtags_memoria(memoria):

    generos = memoria["generos"]


    ranking = sorted(
        generos.items(),
        key=lambda x:x[1],
        reverse=True
    )


    hashtags = []


    for genero, pontos in ranking:

        if pontos >= 10:

            hashtags.append(genero)


    return hashtags[:3]

def analisar_livro_com_memoria(caminho):

    memoria = criar_memoria_temporaria()

    capitulos = ler_livro_completo(caminho)

    for capitulo in capitulos:

        memoria["capitulos_lidos"] += 1

        analisar_contexto(capitulo, memoria)

    # ===== REGRAS DE CONTEXTO =====

    # Lobisomem
    if (
        memoria["generos"].get("#lobisomem", 0) >= 20
        or (
            "alfa" in " ".join(memoria["frases_encontradas"])
            and "mate" in " ".join(memoria["frases_encontradas"])
            and "matilha" in " ".join(memoria["frases_encontradas"])
        )
    ):
        memoria["generos"]["#lobisomem"] = memoria["generos"].get("#lobisomem", 0) + 50

    # Fantasia
    if (
        memoria["generos"].get("#fantasia", 0) >= 20
        or (
            "magia" in " ".join(memoria["frases_encontradas"])
            and "reino" in " ".join(memoria["frases_encontradas"])
        )
    ):
        memoria["generos"]["#fantasia"] = memoria["generos"].get("#fantasia", 0) + 30

    # Harém reverso
    if (
        memoria["generos"].get("#harémreverso", 0) >= 10
        or (
            "why choose" in " ".join(memoria["frases_encontradas"])
            and "companheiros" in " ".join(memoria["frases_encontradas"])
        )
    ):
        memoria["generos"]["#harémreverso"] = memoria["generos"].get("#harémreverso", 0) + 30

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
            "magia",
            "mágica",
            "magico",
            "mágico",
            "feiticeiro",
            "feiticeira",
            "feitiço",
            "feitiços",
            "bruxa",
            "bruxo",
            "mago",
            "reino",
            "castelo",
            "dragão",
            "dragao",
            "elfo",
            "elfos",
            "fada",
            "fadas",
            "demônio",
            "demonio",
            "anjo",
            "profecia",
            "portal",
            "mundo mágico",
            "criaturas sobrenaturais",
            "poderes mágicos"
        ],

        "#romantasia":[
            "romantasia"
        ],

        "#harémreverso":[
            "harém reverso",
            "multiple mates",
            "mais de um companheiro",
            "mais de um parceiro",
            "eles me querem",
            "meus companheiros",
            "companheiros",
            "múltiplos companheiros",
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
            "alfa",
            "beta",
            "ômega",
            "omega",
            "mate",
            "companheira destinada",
            "companheiro destinado",
            "matilha",
            "alcateia",
            "transformação",
            "transformacao",
            "forma de lobo",
            "cheiro",
            "feromônio",
            "feromonio",
            "marcação",
            "marcacao",
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


        if pontos > 0:

            encontrados.append(
                (hashtag, pontos)
            )


    encontrados.sort(
        key=lambda x:x[1],
        reverse=True
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

    memoria = analisar_livro_com_memoria_nova(caminho)


    hashtags = escolher_hashtags_memoria(
        memoria
    )


    hashtags = garantir_hashtag(
        hashtags
    )


    return {

        "hashtags": hashtags,

        "memoria": memoria

    }
