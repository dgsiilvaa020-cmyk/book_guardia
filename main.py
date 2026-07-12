import os
import asyncio
import sqlite3
import re
import unicodedata
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ebooklib import epub
from bs4 import BeautifulSoup

from inteligencia_livro import (
    ler_inicio_epub,
    gerar_hashtags,
    analisar_livro
)

from ebooklib import epub
from bs4 import BeautifulSoup


def ler_capitulos_epub(caminho, limite=5):

    livro = epub.read_epub(caminho)

    capitulos = []

    numero = 0

    # pega a ordem real do EPUB
    for item_id, _ in livro.spine:

        item = livro.get_item_with_id(item_id)

        if not item:
            continue

        if item.get_type() != 9:
            continue


        soup = BeautifulSoup(
            item.get_content(),
            "html.parser"
        )

        texto = ""

        for tag in soup.find_all(
            ["h1", "h2", "h3", "p"]
        ):

            conteudo = tag.get_text(
                " ",
                strip=True
            )

            if conteudo:
                texto += conteudo + "\n\n"


        if texto.strip():

            numero += 1

            capitulos.append(
                f"📖 CAPÍTULO {numero}\n\n{texto.strip()}"
            )


        if numero >= limite:
            break


    return "\n\n━━━━━━━━━━━━━━\n\n".join(capitulos)
    

def extrair_lista_capitulos_epub(caminho, limite=15):

    livro = epub.read_epub(caminho)

    capitulos = []

    numero = 0

    for item_id, _ in livro.spine:

        item = livro.get_item_with_id(item_id)

        if not item:
            continue

        if item.get_type() != 9:
            continue

        soup = BeautifulSoup(
            item.get_content(),
            "html.parser"
        )

        texto = ""

        for tag in soup.find_all(
            ["h1", "h2", "h3", "p"]
        ):

            conteudo = tag.get_text(
                " ",
                strip=True
            )

            if conteudo:
                texto += conteudo + "\n\n"


        if texto.strip():

            numero += 1

            capitulos.append(
                {
                    "numero": numero,
                    "texto": texto.strip()
                }
            )


        if numero >= limite:
            break


    return capitulos
    
    
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8672397104]  # coloque seu ID aqui

# Grupo onde os Aliados fazem os pedidos
GRUPO_PEDIDOS = -1003609010797

# Grupo onde os Guardiões publicam os livros
GRUPO_ACERVO = -1004348688790

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("pedidos.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE pedidos
        ADD COLUMN msg_registrada_id INTEGER
    """)
    conn.commit()
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nome TEXT,
    username TEXT,
    pedido TEXT,
    status TEXT,
    grupo_msg_id INTEGER,
    msg_registrada_id INTEGER,
    arquivo_id TEXT,
    arquivo_tipo TEXT,
    figurinha_id TEXT,
    chave_livro TEXT,
    capa_id TEXT,
    capa_tipo TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS config (
    chave TEXT,
    valor TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS entregues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave_livro TEXT UNIQUE,
    nome_livro TEXT,
    pedido_id INTEGER,
    arquivo_id TEXT,
    data_registro TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

pedido_selecionado = {}

# Cada administrador terá vários pacotes
pacotes_pendentes = {}

livros_analise = {}

livros_capitulos = {}

paginas_capitulos = {}

modo_edicao = {}

hashtags_selecionadas = {}

hashtags_disponiveis = {

    "📚 Fantasia": [
        "#fantasia",
        "#magia",
        "#dragao",
        "#vampiro",
        "#lobisomem",
        "#bruxa",
        "#feericos",
        "#realeza",
        "#profecia",
        "#poderes"
    ],

    "🖤 Dark Romance": [
        "#darkromance",
        "#obsessivo",
        "#possessivo",
        "#vinganca",
        "#sequestro",
        "#morallygrey",
        "#enemiestolovers",
        "#slowburn"
    ],

    "🔫 Máfia": [
        "#mafia",
        "#bratva",
        "#camorra",
        "#cartel",
        "#mafioso",
        "#crime",
        "#dondamafia",
        "#submundo"
    ],

    "💕 Romance": [
        "#romance",
        "#casamentoforcado",
        "#grumpyxsunshine",
        "#friendsTolovers",
        "#enemiestolovers",
        "#fakeDating",
        "#secondChance"
    ],

    "🏰 Realeza": [
        "#realeza",
        "#principe",
        "#princesa",
        "#rei",
        "#rainha",
        "#castelo"
    ],

    "😈 Sobrenatural": [
        "#anjo",
        "#demonio",
        "#necromante",
        "#imortal",
        "#sobrenatural"
    ],

    "🎓 Academia": [
        "#academia",
        "#universidade",
        "#faculdade",
        "#college",
        "#campus",
        "#academy"
    ],

    "❤️‍🔥 Harém": [
        "#haremreverso",
        "#whychoose",
        "#reverseharem",
        "#multipleloveinterest"
    ]
}

hashtags_selecionadas = {}

CATEGORIAS_HASHTAGS = [

    "🧙 Fantasia",
    "🩸 Dark Romance",
    "🔫 Máfia",
    "❤️ Romance",

    "👑 Realeza",
    "🐺 Sobrenatural",
    "🎓 Academia",
    "💼 Bilionário",

    "💍 Casamento",
    "👶 Gravidez",
    "🔥 Hot",
    "🕵️ Suspense",

    "😈 Demônios",
    "👼 Anjos",
    "🧛 Vampiros",
    "🐉 Dragões"

]

def autorizado(user_id: int):
    return user_id in ADMINS


def pegar_config(chave):
    cursor.execute(
        "SELECT valor FROM config WHERE chave = ? ORDER BY rowid DESC LIMIT 1",
        (chave,)
    )
    resultado = cursor.fetchone()
    return resultado[0] if resultado else ""


def salvar_config(chave, valor):
    cursor.execute("SELECT rowid FROM config WHERE chave = ?", (chave,))
    existe = cursor.fetchone()

    if existe:
        cursor.execute(
            "UPDATE config SET valor = ? WHERE chave = ?",
            (valor, chave)
        )
    else:
        cursor.execute(
            "INSERT INTO config (chave, valor) VALUES (?, ?)",
            (chave, valor)
        )

    conn.commit()


configs_padrao = {
    "msg_pedido": "📚 Missão registrada, guardião 🎯\nA Guardiã dos Livros já está consultando o acervo.",

    "msg_concluida": "✅ Missão concluída, aliado 🎯\nSeu e-book já está nas Prateleiras da Guardiã. Confira no acervo.",

    "msg_arquivo": "🎯 Missão concluída pela Guardiã dos Livros!\n\n📚 Pedido de: {nome}\n📌 Missão #{numero_missao}",

    "msg_nao_encontrei": "🔍 Guardião, essa missão ainda não foi encontrada no acervo.\nEla ficará guardada nas Missões Não Encontradas.",

    "msg_ja_postado": "📚 Guardião, essa missão já foi concluída anteriormente.\nDá uma olhada no nosso acervo.",

    # NOVAS CONFIGURAÇÕES
    "usar_sinopse": "1",
    "usar_hashtags": "1"
}

for chave, valor in configs_padrao.items():
    if not pegar_config(chave):
        salvar_config(chave, valor)


def remover_acentos(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def extrair_nome_livro(texto):
    linhas = texto.splitlines()

    palavras = [
        "livro",
        "nome do livro",
        "titulo",
        "título",
        "nome"
    ]

    for linha in linhas:
        linha_original = linha.strip()
        linha_limpa = remover_acentos(linha_original.lower())

        if ":" not in linha_original:
            continue

        campo, valor = linha_original.split(":", 1)
        campo = remover_acentos(campo.lower())

        if any(palavra in campo for palavra in palavras):
            valor = valor.strip()
            if valor:
                return valor

    return "Livro não informado"
    

def extrair_autor(texto):
    linhas = texto.splitlines()

    palavras = [
        "autor",
        "autora",
        "autor(a)",
        "escritor",
        "escritora",
        "nome do autor",
        "nome da autora"
    ]

    for linha in linhas:
        linha_original = linha.strip()
        linha_limpa = remover_acentos(linha_original.lower())

        if ":" not in linha_original:
            continue

        campo, valor = linha_original.split(":", 1)
        campo = remover_acentos(campo.lower())

        if any(palavra in campo for palavra in palavras):
            valor = valor.strip()
            if valor:
                return valor

    return "Autor não informado"

def extrair_metadados_epub(caminho):
    try:
        livro = epub.read_epub(caminho)

        titulo = "Livro não informado"
        autor = "Autor não informado"

        # Título
        titulos = livro.get_metadata("DC", "title")
        if titulos:
            titulo = titulos[0][0].strip()

        # Autor
        autores = livro.get_metadata("DC", "creator")
        if autores:
            autor = autores[0][0].strip()

        return titulo, autor

    except Exception as e:
        print("Erro lendo metadados EPUB:", e)
        return "Livro não informado", "Autor não informado"

def extrair_dados_livro_epub(caminho):

    print("ENTROU NA FUNÇÃO")

    try:

        print("Abrindo EPUB...")

        livro = epub.read_epub(caminho)

        print("EPUB aberto!")

        texto_inicio = ler_capitulos_epub(caminho, limite=5)

        import re

        import re

        import re

        serie = None
        numero_serie = None

        padroes = [
            r"série\s+(.+?)\s+livro\s+(\d+)",
            r"saga\s+(.+?)\s+livro\s+(\d+)",
            r"series\s+(.+?)\s+book\s+(\d+)",
            r"book\s+(\d+)\s+of\s+the\s+(.+)"
        ]

        for padrao in padroes:

            resultado = re.search(
                padrao,
                texto_inicio,
                flags=re.I
            )

            if resultado:

                if len(resultado.groups()) == 2:

                    if resultado.group(1).isdigit():

                        numero_serie = resultado.group(1)
                        serie = resultado.group(2)

                    else:

                        serie = resultado.group(1)
                        numero_serie = resultado.group(2)

                break
        

        print("========== INÍCIO ==========")
        print(texto_inicio[:1000])
        print("============================")

        titulo = None
        autor = None

        # tenta metadados internos
        titulos = livro.get_metadata("DC", "title")
        autores = livro.get_metadata("DC", "creator")

        serie = None
        numero_serie = None

        # Metadados do Calibre
        series = livro.get_metadata("OPF", "calibre:series")
        series_index = livro.get_metadata("OPF", "calibre:series_index")

        if series:
            serie = series[0][0]

        if series_index:
            numero_serie = str(series_index[0][0])

        if titulos:
            titulo = titulos[0][0]

        if autores:
            autor = autores[0][0]


        # se vier nome da logo ou tradução, limpa
        if titulo:
            palavras_bloqueadas = [
                "traduzido",
                "tradução",
                "j coruja",
                "almascriptum",
                "lumos",
                "translate"
            ]

            titulo_limpo = titulo.lower()

            for palavra in palavras_bloqueadas:
                titulo_limpo = titulo_limpo.replace(palavra, "")

            titulo = titulo_limpo.strip()


        return {
            "nome_livro": titulo or "Livro não identificado",
            "autor": autor or "Autor não identificado",
            "serie": serie,
            "numero_serie": numero_serie
        }


    except Exception as e:
        print("Erro EPUB:", e)

        return {
            "nome_livro": "Livro não identificado",
            "autor": "Autor não identificado",
            "serie": None,
            "numero_serie": None
        }

def criar_chave_livro(texto):
    nome = extrair_nome_livro(texto)
    nome = remover_acentos(nome.lower())
    nome = re.sub(r"[^a-z0-9]+", " ", nome)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome


def formatar_mensagem_config(chave, **dados):
    texto = pegar_config(chave)
    try:
        return texto.format(**dados)
    except Exception:
        return texto


def parece_ficha(texto: str):
    texto = texto.lower()
    return (
        "#pedido" in texto
        or "livro:" in texto
        or "nome:" in texto
        or "autora:" in texto
        or "autor:" in texto
        or "formato:" in texto
    )


def numero_visual(pedido_id, status):
    cursor.execute("""
    SELECT id FROM pedidos
    WHERE status = ?
    ORDER BY id ASC
    """, (status,))

    ids = [linha[0] for linha in cursor.fetchall()]

    if pedido_id in ids:
        return ids.index(pedido_id) + 1

    return pedido_id


def contadores_texto():
    cursor.execute("SELECT COUNT(*) FROM entregues")
    total_acervo = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    total_missoes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'nao_encontrado'")
    total_nao_encontradas = cursor.fetchone()[0]

    return (
        "📊 Contadores do Acervo\n\n"
        f"📚 Acervo: {total_acervo}\n"
        f"🎯 Missões registradas: {total_missoes}\n"
        f"🔍 Missões não encontradas: {total_nao_encontradas}"
    )


def menu_pv():
    kb = InlineKeyboardBuilder()

    kb.button(text="🎯 Missões registradas", callback_data="missoes")
    kb.button(text="🔍 Missões Não Encontradas", callback_data="missoes_nao_encontradas")
    kb.button(text="📊 Contadores", callback_data="contadores")
    kb.button(text="✏️ Personalizar Mensagens", callback_data="personalizar")
    kb.button(text="🧠 Arquivo Inteligente", callback_data="arquivo_inteligente")

    kb.button(
        text="⚙️ Configurações",
        callback_data="configuracoes"
    )

    kb.button(text="🧹 Limpar missões concluídas", callback_data="limpar")

    kb.adjust(1)

    return kb.as_markup()


def menu_personalizar():
    kb = InlineKeyboardBuilder()
    kb.button(text="📚 Mensagem da missão", callback_data="editar_msg_pedido")
    kb.button(text="🎯 Mensagem do arquivo", callback_data="editar_msg_arquivo")
    kb.button(text="✅ Mensagem concluída", callback_data="editar_msg_concluida")
    kb.button(text="🔎 Mensagem: não encontrei", callback_data="editar_msg_nao_encontrei")
    kb.button(text="🖼️ Figurinha: não encontrei", callback_data="editar_sticker_nao_encontrei")
    kb.button(text="⬅️ Voltar", callback_data="voltar_menu")
    kb.adjust(1)
    return kb.as_markup()


def menu_arquivo_inteligente():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Mensagem: já está no acervo", callback_data="editar_msg_ja_postado")
    kb.button(text="📊 Ver contadores", callback_data="contadores")
    kb.button(text="⬅️ Voltar", callback_data="voltar_menu")
    kb.adjust(1)
    return kb.as_markup()


def menu_configuracoes():

    sinopse = pegar_config("usar_sinopse")
    hashtags = pegar_config("usar_hashtags")

    kb = InlineKeyboardBuilder()

    kb.button(
        text=f"{'✅' if sinopse=='1' else '❌'} Sinopse",
        callback_data="toggle_sinopse"
    )

    kb.button(
        text=f"{'✅' if hashtags=='1' else '❌'} Hashtags",
        callback_data="toggle_hashtags"
    )

    kb.button(
        text="⬅️ Voltar",
        callback_data="voltar_menu"
    )

    kb.adjust(1)

    return kb.as_markup()


def menu_capitulos(capitulos):

    kb = InlineKeyboardBuilder()


    for capitulo in capitulos:

        resumo = capitulo["texto"][:40]

        kb.button(
            text=f"📖 Cap {capitulo['numero']}\n{resumo}...",
            callback_data=f"abrir_capitulo_{capitulo['numero']}"
        )


    kb.button(
        text="⬅️ Voltar",
        callback_data="fechar_capitulos"
    )


    kb.adjust(4)

    return kb.as_markup()
    

def menu_confirmar_livro():

    kb = InlineKeyboardBuilder()

    kb.button(
        text="📖 Ver capítulos",
        callback_data="ver_capitulos"
    )

    kb.button(
        text="🏷️ Escolher Hashtags",
        callback_data="escolher_hashtags"
    )

    kb.button(
        text="✏️ Inserir Sinopse",
        callback_data="editar_sinopse"
    )

    kb.button(
        text="✅ Confirmar Livro",
        callback_data="confirmar_livro"
    )

    kb.adjust(1)

    return kb.as_markup()


def menu_categorias_hashtags():

    kb = InlineKeyboardBuilder()

    for categoria in hashtags_disponiveis.keys():

        kb.button(
            text=categoria,
            callback_data=f"categoria_{categoria}"
        )

    kb.button(
        text="✅ Concluir",
        callback_data="hashtags_finalizar"
    )

    kb.button(
        text="⬅️ Voltar",
        callback_data="voltar_confirmacao"
    )

    kb.adjust(4)

    return kb.as_markup()
    

def menu_pagina_capitulo(numero, total):

    kb = InlineKeyboardBuilder()

    if numero > 1:
        kb.button(
            text="⬅️ Voltar",
            callback_data=f"pagina_cap_{numero-1}"
        )

    kb.button(
        text="➡️ Próxima",
        callback_data=f"pagina_cap_{numero+1}"
    )

    kb.button(
        text="🏠 Capítulos",
        callback_data="voltar_lista_capitulos"
    )

    kb.adjust(2)

    return kb.as_markup()
    

def menu_categorias_hashtags():

    kb = InlineKeyboardBuilder()

    for categoria in CATEGORIAS_HASHTAGS:

        kb.button(
            text=categoria,
            callback_data=f"categoria_{categoria}"
        )

    kb.button(
        text="⬅️ Voltar",
        callback_data="voltar_confirmacao"
    )

    kb.adjust(4)

    return kb.as_markup()

def menu_hashtags_categoria(categoria):

    kb = InlineKeyboardBuilder()

    for hashtag in hashtags_disponiveis[categoria]:

        kb.button(
            text=hashtag,
            callback_data=f"tag_{hashtag}"
        )

    kb.button(
        text="⬅️ Voltar",
        callback_data="voltar_categorias"
    )

    kb.adjust(4)

    return kb.as_markup()
    

def menu_pedidos(pedidos):
    kb = InlineKeyboardBuilder()

    for indice, pedido in enumerate(pedidos, start=1):
        pedido_id, nome = pedido
        kb.button(
            text=f"🎯 Missão {indice} - {nome}",
            callback_data=f"selecionar_{pedido_id}"
        )

    kb.adjust(1)
    return kb.as_markup()


def menu_missao_acoes(pedido_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔎 Não encontrei o livro", callback_data=f"nao_encontrei_{pedido_id}")
    kb.button(text="❌ Cancelar envio", callback_data=f"cancelar_envio_{pedido_id}")
    kb.button(text="✅ Finalizar missão", callback_data=f"finalizar_{pedido_id}")
    kb.button(text="⬅️ Voltar às missões", callback_data="missoes")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(Command("start"))
async def start(message: Message):
    if message.chat.type != "private":
        return

    if not autorizado(message.from_user.id):
        await message.answer("⛔ Apenas guardiões autorizados podem usar este bot.")
        return

    await message.answer(
        "📚 Bem-vinda, Guardiã dos Livros.\n\n"
        "Escolha uma opção:",
        reply_markup=menu_pv()
    )

@dp.callback_query(F.data.startswith("tag_"))
async def escolher_hashtag(callback: CallbackQuery):

    admin = callback.from_user.id

    hashtag = callback.data.replace("tag_", "")

    hashtags_selecionadas.setdefault(admin, [])

    if hashtag in hashtags_selecionadas[admin]:

        await callback.answer(
            "Essa hashtag já foi escolhida.",
            show_alert=True
        )
        return

    if len(hashtags_selecionadas[admin]) >= 5:

        await callback.answer(
            "Você pode escolher no máximo 5 hashtags.",
            show_alert=True
        )
        return

    hashtags_selecionadas[admin].append(hashtag)

    await callback.answer(f"{hashtag} adicionada ✅")
    

@dp.callback_query(F.data == "hashtags_finalizar")
async def finalizar_hashtags(callback: CallbackQuery):

    admin = callback.from_user.id

    if admin not in pacotes_pendentes:
        await callback.answer()
        return

    pacote = pacotes_pendentes[admin][-1]

    pacote["hashtags"] = hashtags_selecionadas.get(admin, [])

    hashtags_selecionadas.pop(admin, None)

    await callback.answer()

    await callback.message.edit_text(
        "✅ Hashtags salvas!\n\nAgora confirme o livro.",
        reply_markup=menu_confirmar_livro()
    )

@dp.callback_query(F.data == "escolher_hashtags")
async def abrir_menu_hashtags(callback: CallbackQuery):

    hashtags_selecionadas[callback.from_user.id] = []

    await callback.answer()

    await callback.message.edit_text(
        "🏷️ Escolha uma categoria:",
        reply_markup=menu_categorias_hashtags()
    )
    

@dp.callback_query(F.data.startswith("categoria_"))
async def abrir_categoria(callback: CallbackQuery):

    categoria = callback.data.replace("categoria_", "")

    await callback.answer()

    await callback.message.edit_text(
        f"🏷️ {categoria}\n\nEscolha até 5 hashtags:",
        reply_markup=menu_hashtags_categoria(categoria)
    )

@dp.callback_query(F.data == "voltar_categorias")
async def voltar_categorias(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "🏷️ Escolha uma categoria:",
        reply_markup=menu_categorias_hashtags()
    )
    

@dp.callback_query(F.data == "ver_inicio_livro")
async def ver_inicio_livro(callback: CallbackQuery):

    admin = callback.from_user.id

    if admin not in livros_analise:
        await callback.answer(
            "Nenhum EPUB encontrado.",
            show_alert=True
        )
        return


    caminho = livros_analise[admin]


    capitulos = extrair_lista_capitulos_epub(
        caminho,
        limite=15
    )


    livros_capitulos[admin] = capitulos


    await callback.answer()


    await callback.message.edit_text(
        "📖 Escolha o capítulo que deseja visualizar:",
        reply_markup=menu_capitulos(capitulos)
    )

@dp.callback_query(F.data == "ver_capitulos")
async def ver_capitulos(callback: CallbackQuery):

    admin = callback.from_user.id

    paginas_capitulos.pop(admin, None)

    capitulos = livros_capitulos.get(admin)

    if not capitulos:
        await callback.answer(
            "Capítulos não encontrados.",
            show_alert=True
        )
        return


    await callback.answer()


    await callback.message.edit_text(
        "📖 Escolha o capítulo:",
        reply_markup=menu_capitulos(capitulos)
    )

@dp.message(Command("menu"))
async def menu(message: Message):
    if message.chat.type != "private":
        return

    if not autorizado(message.from_user.id):
        return

    await message.answer(
        "📚 Menu principal:",
        reply_markup=menu_pv()
    )

@dp.callback_query(F.data == "configuracoes")
async def configuracoes(callback: CallbackQuery):

    if not autorizado(callback.from_user.id):
        return

    await callback.answer()

    await callback.message.answer(
        "⚙️ Configurações",
        reply_markup=menu_configuracoes()
    )


@dp.callback_query(F.data == "toggle_sinopse")
async def toggle_sinopse(callback: CallbackQuery):

    valor = pegar_config("usar_sinopse")

    if valor == "1":
        salvar_config("usar_sinopse", "0")
    else:
        salvar_config("usar_sinopse", "1")

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=menu_configuracoes()
    )
    

@dp.callback_query(F.data == "voltar_lista_capitulos")
async def voltar_lista_capitulos(callback: CallbackQuery):

    admin = callback.from_user.id

    capitulos = livros_capitulos.get(admin)

    if not capitulos:
        await callback.answer()
        return


    await callback.answer()


    await callback.message.edit_text(
        "📖 Escolha um capítulo:",
        reply_markup=menu_capitulos(capitulos)
    )

@dp.callback_query(F.data == "toggle_hashtags")
async def toggle_hashtags(callback: CallbackQuery):

    valor = pegar_config("usar_hashtags")

    if valor == "1":
        salvar_config("usar_hashtags", "0")
    else:
        salvar_config("usar_hashtags", "1")

    await callback.answer()

    await callback.message.edit_reply_markup(
        reply_markup=menu_configuracoes()
    )


@dp.message(F.chat.type == "private", F.text)
async def receber_texto_personalizado(message: Message):
    if not autorizado(message.from_user.id):
        return

    chave = modo_edicao.get(message.from_user.id)

    if not chave:
        return

    if chave == "sticker_nao_encontrei":
        await message.answer("⚠️ Envie uma figurinha, não uma mensagem de texto.")
        return

    if chave == "sinopse_manual":

        pacote = pacotes_pendentes[message.from_user.id][-1]

        pacote["sinopse"] = message.text
        pacote["origem_sinopse"] = "manual"

        modo_edicao.pop(
            message.from_user.id,
            None
        )

        await message.answer(
            "✅ Sinopse personalizada salva!",
            reply_markup=menu_confirmar_livro()
        )

        return


    salvar_config(chave, message.text)

    modo_edicao.pop(
        message.from_user.id,
        None
    )

    nova = pegar_config(chave)

    await message.answer(
        "✅ Mensagem personalizada salva com sucesso!\n\n"
        "📌 Nova mensagem salva:\n\n"
        f"{nova}",
        reply_markup=menu_pv()
    )
    

@dp.message(F.chat.id == GRUPO_PEDIDOS, F.text)
async def registrar_pedido(message: Message):
    texto = message.text

    if not parece_ficha(texto):
        return

    user = message.from_user
    nome = user.full_name
    username = user.username or "sem username"

    chave_livro = criar_chave_livro(texto)
    nome_livro = extrair_nome_livro(texto)

    cursor.execute("""
    SELECT id FROM entregues
    WHERE chave_livro = ?
    """, (chave_livro,))
    ja_entregue = cursor.fetchone()

    if ja_entregue:
        await message.reply(
            formatar_mensagem_config(
                "msg_ja_postado",
                nome=nome,
                nome_livro=nome_livro
            )
        )
        return

    cursor.execute("""
    INSERT INTO pedidos
    (user_id, nome, username, pedido, status, grupo_msg_id, chave_livro)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        nome,
        username,
        texto,
        "pendente",
        message.message_id,
        chave_livro
    ))
    conn.commit()

    msg = await message.reply(pegar_config("msg_pedido"))

    cursor.execute("""
    UPDATE pedidos
    SET msg_registrada_id = ?
    WHERE grupo_msg_id = ?
    """, (
        msg.message_id,
        message.message_id
    ))
    conn.commit()


@dp.callback_query(F.data == "missoes")
async def missoes(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    cursor.execute("""
    SELECT id, nome
    FROM pedidos
    WHERE status = 'pendente'
    ORDER BY id ASC
    """)
    pedidos = cursor.fetchall()

    if not pedidos:
        await callback.message.answer(
            "✅ Não há missões registradas no momento.",
            reply_markup=menu_pv()
        )
        return

    await callback.message.answer(
        "🎯 Escolha qual missão deseja abrir:",
        reply_markup=menu_pedidos(pedidos)
    )

@dp.callback_query(F.data == "editar_msg_concluida")
async def editar_msg_concluida(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    modo_edicao[callback.from_user.id] = "msg_concluida"

    atual = pegar_config("msg_concluida")

    await callback.message.answer(
        "✅ Envie agora a nova mensagem de pedido concluído.\n\n"
        "Essa mensagem será enviada no grupo de pedidos "
        "respondendo a mensagem da pessoa quando o livro for entregue no acervo.\n\n"
        "Você pode usar:\n"
        "{nome} = nome da pessoa\n"
        "{nome_livro} = nome do livro\n\n"
        f"Mensagem atual:\n\n{atual}"
    )


@dp.callback_query(F.data == "missoes_nao_encontradas")
async def missoes_nao_encontradas(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    cursor.execute("""
    SELECT id, nome
    FROM pedidos
    WHERE status = 'nao_encontrado'
    ORDER BY id ASC
    """)
    pedidos = cursor.fetchall()

    if not pedidos:
        await callback.message.answer(
            "✅ Não há missões não encontradas no momento.",
            reply_markup=menu_pv()
        )
        return

    await callback.message.answer(
        "🔍 Missões guardadas como não encontradas:",
        reply_markup=menu_pedidos(pedidos)
    )


@dp.callback_query(F.data == "editar_sinopse")
async def editar_sinopse(callback: CallbackQuery):

    admin = callback.from_user.id

    if admin not in pacotes_pendentes:
        await callback.answer(
            "Nenhum livro carregado.",
            show_alert=True
        )
        return


    modo_edicao[admin] = "sinopse_manual"

    await callback.answer()

    await callback.message.answer(
        "✏️ Envie agora a sinopse personalizada.\n\n"
        "Ela será colocada junto com a capa do livro."
    )
    
    
@dp.callback_query(F.data == "escolher_hashtags")
async def escolher_hashtags(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "🏷️ Escolha uma categoria:",
        reply_markup=menu_categorias_hashtags()
    )
    

@dp.callback_query(F.data.startswith("selecionar_"))
async def selecionar_pedido(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    pedido_id = int(callback.data.replace("selecionar_", ""))

    cursor.execute("""
    SELECT id, nome, pedido, status
    FROM pedidos
    WHERE id = ? AND status IN ('pendente', 'nao_encontrado')
    """, (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        await callback.message.answer("⚠️ Essa missão não está mais disponível.")
        return

    id_pedido, nome, pedido_texto, status = pedido
    numero = numero_visual(id_pedido, status)

    pedido_selecionado[callback.from_user.id] = pedido_id
    pacotes_pendentes[callback.from_user.id] = []
    
    await callback.message.answer(
        f"🎯 Missão {numero} selecionada.\n\n"
        f"👤 Guardião solicitante: {nome}\n\n"
        f"{pedido_texto}\n\n"
        "Agora envie um ou vários arquivos PDF/EPUB aqui no PV.\n"
        "Quando terminar, envie a figurinha de confirmação.\n\n"
        "A missão só será fechada quando você tocar em ✅ Finalizar missão.",
        reply_markup=menu_missao_acoes(pedido_id)
    )


@dp.message(F.chat.type == "private", F.photo)
async def receber_capa(message: Message):

    if not autorizado(message.from_user.id):
        return

    admin = message.from_user.id

    if admin not in pedido_selecionado:
        await message.answer(
            "Primeiro escolha uma missão."
        )
        return

    # Se ainda não existir a lista de pacotes
    pacotes_pendentes.setdefault(admin, [])

    # Cria um novo pacote
    pacote = {
        "capa": message.photo[-1].file_id,
        "traducao": None,
        "arquivos": [],
        "hashtags": [],
        "sinopse": "",
        "origem_sinopse": "",
        "confirmado": False,
    }

    pacotes_pendentes[admin].append(pacote)

    numero = len(pacotes_pendentes[admin])

    print("NOVA CAPA CRIADA:", pacote)

    kb = InlineKeyboardBuilder()

    kb = InlineKeyboardBuilder()
    kb.button(text="🤖 Tradução Mecânica", callback_data="trad_mecanica")
    kb.button(text="📚 Tradução Oficial", callback_data="trad_oficial")
    kb.button(text="🇺🇸 Inglês", callback_data="trad_ingles")
    kb.button(text="⏭️ Pular tradução", callback_data="trad_pular")
    
    await message.answer(
        f"✅ Capa #{numero} recebida.\n\n"
        "Escolha o tipo da tradução.",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("trad_"))
async def escolher_traducao(callback: CallbackQuery):

    if not autorizado(callback.from_user.id):
        return

    admin = callback.from_user.id

    if admin not in pacotes_pendentes or not pacotes_pendentes[admin]:
        await callback.answer("Nenhuma capa encontrada.", show_alert=True)
        return

    pacote = pacotes_pendentes[admin][-1]


    traducoes = {
        "trad_mecanica": "🤖 Tradução Mecânica",
        "trad_oficial": "📚 Tradução Oficial",
        "trad_ingles": "🇺🇸 Inglês",
        "trad_pular": "⏭️ Sem tradução"
    }


    pacote["traducao"] = traducoes.get(callback.data)


    print("TRADUÇÃO SALVA:", pacote)


    await callback.answer("Tradução escolhida ✅")


    await callback.message.edit_text(
        "✅ Tradução salva!\n\n"
        "Agora envie os arquivos deste livro.\n\n"
        "Quando terminar:\n"
        "📷 envie outra capa\n"
        "ou\n"
        "🏁 finalize com a figurinha."
    )


@dp.message(F.chat.type == "private", F.document)
async def receber_arquivo(message: Message):

    if not autorizado(message.from_user.id):
        return

    admin = message.from_user.id

    if admin not in pacotes_pendentes:
        await message.answer("Primeiro envie uma capa.")
        return

    if not pacotes_pendentes[admin]:
        await message.answer("Primeiro envie uma capa.")
        return

    pacote = pacotes_pendentes[admin][-1]
    
    pacote["arquivos"].append(message.document.file_id)


    nome_arquivo = message.document.file_name.lower()


    if nome_arquivo.endswith(".epub"):

        arquivo = await bot.get_file(
            message.document.file_id
        )


        caminho = f"temp_{admin}.epub"


        await bot.download_file(
            arquivo.file_path,
            caminho
        )

        livros_capitulos[admin] = extrair_lista_capitulos_epub(
            caminho,
            limite=15
        )


        texto = ler_inicio_epub(caminho)

        dados = extrair_dados_livro_epub(caminho)

        print(dados)

        pacote["nome_livro"] = dados["nome_livro"]
        pacote["autor"] = dados["autor"]
        pacote["serie"] = dados["serie"]
        pacote["numero_serie"] = dados["numero_serie"]

        chave_livro = remover_acentos(
            pacote.get("nome_livro", "").lower()
        )

        chave_livro = re.sub(
            r"[^a-z0-9]+",
            " ",
            chave_livro
        ).strip()

        pacote["chave_livro"] = chave_livro

        resultado = analisar_livro(caminho)

        livros_capitulos[admin] = extrair_lista_capitulos_epub(
            caminho,
            limite=15
        )

        livros_analise[admin] = caminho

        pacote["sinopse"] = resultado["sinopse"]
        pacote["origem_sinopse"] = resultado["origem"]

        print("SINOPSE ENCONTRADA:")
        print(resultado["origem"])
        print(resultado["sinopse"][:500])

    total = len(pacote["arquivos"])


    origens = {
        "metadados": "📚 Metadados do EPUB",
        "inicio": "📖 Sinopse encontrada no livro",
        "resumo": "🤖 Resumo criado automaticamente"
    }

    origem = origens.get(
        pacote.get("origem_sinopse", ""),
        pacote.get("origem_sinopse", "Não encontrada")
    )

    texto = (
        "📚 <b>Livro analisado!</b>\n\n"

        f"<b>📖 Título:</b>\n{pacote.get('nome_livro','-')}\n\n"

        f"<b>✍️ Autor:</b>\n{pacote.get('autor','-')}\n\n"

        f"<b>📚 Série:</b>\n{pacote.get('serie') or '—'}\n\n"

       f"<b>📌 Origem da sinopse:</b>\n{origem}\n\n"

        "━━━━━━━━━━━━━━\n"

        "<b>📖 SINOPSE</b>\n\n"

        f"{pacote['sinopse']}\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "Agora escolha as hashtags ou confirme o livro."
    )

    await message.answer(
        texto,
        parse_mode="HTML",
        reply_markup=menu_confirmar_livro()
    )
    
@dp.callback_query(F.data.startswith("abrir_capitulo_"))
async def abrir_capitulo(callback: CallbackQuery):

    admin = callback.from_user.id

    numero = int(
        callback.data.replace(
            "abrir_capitulo_",
            ""
        )
    )

    capitulos = livros_capitulos.get(admin)

    if not capitulos:
        await callback.answer(
            "Capítulo expirado.",
            show_alert=True
        )
        return


    texto = (
        f"📖 CAPÍTULO {numero}\n\n"
        f"{capitulos[numero-1]['texto']}"
    )


    paginas = [
        texto[i:i+3500]
        for i in range(
            0,
            len(texto),
            3500
        )
    ]


    paginas_capitulos[admin] = paginas


    await callback.answer()


    await callback.message.edit_text(
        f"{paginas[0]}\n\n"
        f"Página 1/{len(paginas)}",
        reply_markup=menu_pagina_capitulo(
            1,
            len(paginas)
        )
    )

@dp.callback_query(F.data.startswith("pagina_cap_"))
async def pagina_capitulo(callback: CallbackQuery):

    admin = callback.from_user.id

    pagina = int(
        callback.data.replace(
            "pagina_cap_",
            ""
        )
    )


    paginas = paginas_capitulos.get(admin)


    if not paginas:
        await callback.answer(
            "Página expirada.",
            show_alert=True
        )
        return


    if pagina < 1 or pagina > len(paginas):
        await callback.answer()
        return


    await callback.answer()


    await callback.message.edit_text(
        f"{paginas[pagina-1]}\n\n"
        f"Página {pagina}/{len(paginas)}",
        reply_markup=menu_pagina_capitulo(
            pagina,
            len(paginas)
        )
    )
    

@dp.message(F.chat.type == "private", F.sticker)
async def receber_figurinha(message: Message):
    if not autorizado(message.from_user.id):
        return

    admin_id = message.from_user.id
    chave_edicao = modo_edicao.get(admin_id)

    if chave_edicao == "sticker_nao_encontrei":
        salvar_config("sticker_nao_encontrei", message.sticker.file_id)
        modo_edicao.pop(admin_id, None)

        await message.answer(
            "✅ Figurinha de “não encontrei” salva com sucesso!",
            reply_markup=menu_pv()
        )
        return

    pedido_id = pedido_selecionado.get(admin_id)

    if not pedido_id:
        await message.answer("⚠️ Primeiro escolha uma missão em 🎯 Missões registradas.")
        return

    if admin_id not in pacotes_pendentes:
        await message.answer("⚠️ Nenhum livro preparado.")
        return

    if not pacotes_pendentes[admin_id]:
        await message.answer("⚠️ Nenhum livro preparado.")
        return

    cursor.execute("""
    SELECT id,
           nome,
           pedido,
           grupo_msg_id,
           msg_registrada_id,
           chave_livro,
           status
    FROM pedidos
    WHERE id = ? AND status IN ('pendente', 'nao_encontrado')
    """, (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        await message.answer("⚠️ Missão não encontrada ou já finalizada.")
        return

    id_pedido, nome, pedido_texto, grupo_msg_id, msg_registrada_id, chave_livro, status = pedido
    numero = numero_visual(id_pedido, status)

    legenda = formatar_mensagem_config(
        "msg_arquivo",
        nome=nome,
        id_pedido=id_pedido,
        numero_missao=numero,
        nome_livro=pacotes_pendentes[admin_id][0].get(
            "nome_livro",
            "Livro não informado"
        ),
        autor=pacotes_pendentes[admin_id][0].get(
            "autor",
            "Autor não informado"
        ),
        serie=pacotes_pendentes[admin_id][0].get(
            "serie",
            ""
        ),
        numero_serie=pacotes_pendentes[admin_id][0].get(
            "numero_serie",
            ""
        )
    )
    
    for indice, pacote in enumerate(pacotes_pendentes[admin_id]):

        legenda = formatar_mensagem_config(
            "msg_arquivo",
            nome=nome,
            id_pedido=id_pedido,
            numero_missao=numero,
            nome_livro=pacotes_pendentes[admin_id][0].get(
                "nome_livro",
                "Livro não informado"
            ),
            autor=pacotes_pendentes[admin_id][0].get(
                "autor",
                "Autor não informado"
            ),
            serie=pacotes_pendentes[admin_id][0].get(
                "serie",
                ""
            ),
            numero_serie=pacotes_pendentes[admin_id][0].get(
                "numero_serie",
                ""
            )        
        )

        caption = legenda
        # Apenas a primeira capa recebe a legenda completa
        caption = legenda
            
        if pacote["traducao"]:
            caption += f"\n\n🌐 Tradução: {pacote['traducao']}"
            

        if pacote.get("hashtags"):

            caption += (
                "\n\n🏷️ "
                + " ".join(pacote["hashtags"])
            )

        print("ENVIANDO CAPA:", pacote)

        if (
            pacote.get("sinopse")
            and pegar_config("usar_sinopse") == "1"
        ):

            caption += (
                "\n\n📖 SINOPSE:\n\n"
                + pacote["sinopse"]
            )

        await bot.send_photo(
            chat_id=GRUPO_ACERVO,
            photo=pacote["capa"],
            caption=caption
        )

        for arquivo_id in pacote["arquivos"]:

            await bot.send_document(
                chat_id=GRUPO_ACERVO,
                document=arquivo_id
            )

            cursor.execute("""
            INSERT OR IGNORE INTO entregues
            (chave_livro, nome_livro, pedido_id, arquivo_id)
            VALUES (?, ?, ?, ?)
            """, (
                chave_livro,
                extrair_nome_livro(pedido_texto),
                pedido_id,
                arquivo_id
            ))

    conn.commit()
    

    await bot.send_sticker(
        chat_id=GRUPO_ACERVO,
        sticker=message.sticker.file_id
    )

    cursor.execute("""
    UPDATE pedidos
    SET status = 'pendente', figurinha_id = ?
    WHERE id = ?
    """, (
        message.sticker.file_id,
        pedido_id
    ))

    conn.commit()
    
    mensagem_concluida = formatar_mensagem_config(
        "msg_concluida",
        nome=nome,
        nome_livro=extrair_nome_livro(pedido_texto),
        numero_missao=numero
    )

    if msg_registrada_id:
        try:
            await bot.delete_message(
                chat_id=GRUPO_PEDIDOS,
                message_id=msg_registrada_id
            )
        except:
            pass
    
    await bot.send_message(
        chat_id=GRUPO_PEDIDOS,
        text=mensagem_concluida,
        reply_to_message_id=grupo_msg_id
    )

    
    pacotes_pendentes.pop(admin_id, None)
    
    await message.answer(
        "✅ Arquivo(s) enviados com sucesso!\n\n"
        "🎯 A missão continua aberta.\n"
        "Você pode enviar mais arquivos para essa mesma missão.\n\n"
        "Quando terminar tudo, toque em ✅ Finalizar missão.",
        reply_markup=menu_missao_acoes(pedido_id)
    )


@dp.callback_query(F.data.startswith("cancelar_envio_"))
async def cancelar_envio(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    admin_id = callback.from_user.id
    pedido_id = int(callback.data.replace("cancelar_envio_", ""))

    pacotes_pendentes[admin_id] = []
    pedido_selecionado[admin_id] = pedido_id
    
    await callback.message.answer(
        "❌ Envio cancelado.\n\n"
        "Os arquivos preparados foram descartados.\n"
        "A missão continua aberta.\n\n"
        "Agora envie os arquivos corretos novamente.",
        reply_markup=menu_missao_acoes(pedido_id)
    )


@dp.callback_query(F.data.startswith("nao_encontrei_"))
async def nao_encontrei(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    pedido_id = int(callback.data.replace("nao_encontrei_", ""))

    cursor.execute("""
    SELECT id, nome, pedido, grupo_msg_id
    FROM pedidos
    WHERE id = ? AND status IN ('pendente', 'nao_encontrado')
    """, (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        await callback.message.answer("⚠️ Essa missão não está mais disponível.")
        return

    id_pedido, nome, pedido_texto, grupo_msg_id = pedido

    mensagem = formatar_mensagem_config(
        "msg_nao_encontrei",
        nome=nome,
        id_pedido=id_pedido,
        numero_missao=numero_visual(id_pedido, "pendente"),
        nome_livro=extrair_nome_livro(pedido_texto)
    )

    await bot.send_message(
        chat_id=GRUPO_ACERVO,
        text=mensagem,
    )

    sticker_id = pegar_config("sticker_nao_encontrei")

    if sticker_id:
        await bot.send_sticker(
            chat_id=GRUPO_ACERVO,
            sticker=sticker_id,
        )

    cursor.execute("""
    UPDATE pedidos
    SET status = 'nao_encontrado'
    WHERE id = ?
    """, (pedido_id,))
    conn.commit()

    pedido_selecionado.pop(callback.from_user.id, None)
    pacotes_pendentes.pop(callback.from_user.id, None)

    await callback.message.answer(
        "🔍 Missão enviada para Missões Não Encontradas.\n"
        "Ela saiu da lista principal, mas continua guardada.",
        reply_markup=menu_pv()
    )


@dp.callback_query(F.data.startswith("voltar_pendente_"))
async def voltar_pendente(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    pedido_id = int(callback.data.replace("voltar_pendente_", ""))

    cursor.execute("""
    UPDATE pedidos
    SET status = 'pendente'
    WHERE id = ? AND status = 'nao_encontrado'
    """, (pedido_id,))
    conn.commit()

    await callback.message.answer(
        "🎯 Missão voltou para Missões Registradas.",
        reply_markup=menu_pv()
    )


@dp.callback_query(F.data.startswith("finalizar_"))
async def finalizar_missao(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    admin_id = callback.from_user.id
    pedido_id = int(callback.data.replace("finalizar_", ""))

    cursor.execute("""
    UPDATE pedidos
    SET status = 'concluido'
    WHERE id = ? AND status IN ('pendente', 'nao_encontrado')
    """, (pedido_id,))
    conn.commit()

    pedido_selecionado.pop(admin_id, None)
    pacotes_pendentes.pop(admin_id, None)

    await callback.message.answer(
        "✅ Missão finalizada com sucesso!\n"
        "🎯 Ela saiu das listas de missões abertas.",
        reply_markup=menu_pv()
    )


@dp.callback_query(F.data == "personalizar")
async def personalizar(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    await callback.message.answer(
        "✏️ Escolha qual mensagem deseja personalizar:",
        reply_markup=menu_personalizar()
    )


@dp.callback_query(F.data == "arquivo_inteligente")
async def arquivo_inteligente(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    await callback.message.answer(
        "🧠 Arquivo Inteligente\n\n"
        "Aqui você personaliza a resposta automática para pedidos que já existem no acervo.",
        reply_markup=menu_arquivo_inteligente()
    )


@dp.callback_query(F.data == "contadores")
async def contadores(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    await callback.message.answer(
        contadores_texto(),
        reply_markup=menu_pv()
    )


@dp.callback_query(F.data == "editar_msg_pedido")
async def editar_msg_pedido(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()
    modo_edicao[callback.from_user.id] = "msg_pedido"

    atual = pegar_config("msg_pedido")

    await callback.message.answer(
        "📚 Envie agora a nova mensagem automática da missão.\n\n"
        f"Mensagem atual:\n\n{atual}"
    )


@dp.callback_query(F.data == "editar_msg_arquivo")
async def editar_msg_arquivo(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()
    modo_edicao[callback.from_user.id] = "msg_arquivo"

    atual = pegar_config("msg_arquivo")

    await callback.message.answer(
        "🎯 Envie agora a nova legenda dos arquivos.\n\n"
        "Você pode usar:\n"
        "{nome} = nome da pessoa\n"
        "{id_pedido} = número interno da missão\n"
        "{numero_missao} = número visual organizado\n"
        "{nome_livro} = nome do livro\n"
        "{autor} = nome do autor\n"
        "{serie} = nome da série\n"
        "{numero_serie} = número do livro na série\n\n"
   )


@dp.callback_query(F.data == "editar_msg_nao_encontrei")
async def editar_msg_nao_encontrei(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()
    modo_edicao[callback.from_user.id] = "msg_nao_encontrei"

    atual = pegar_config("msg_nao_encontrei")

    await callback.message.answer(
        "🔎 Envie agora a nova mensagem de “não encontrei o livro”.\n\n"
        "Você pode usar:\n"
        "{nome} = nome da pessoa\n"
        "{id_pedido} = número interno da missão\n"
        "{numero_missao} = número visual organizado\n"
        "{nome_livro} = nome do livro\n\n"
        f"Mensagem atual:\n\n{atual}"
    )


@dp.callback_query(F.data == "editar_msg_ja_postado")
async def editar_msg_ja_postado(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()
    modo_edicao[callback.from_user.id] = "msg_ja_postado"

    atual = pegar_config("msg_ja_postado")

    await callback.message.answer(
        "✅ Envie agora a nova mensagem do Arquivo Inteligente.\n\n"
        "Essa mensagem será enviada quando o livro já existir no acervo.\n\n"
        "Você pode usar:\n"
        "{nome} = nome da pessoa\n"
        "{nome_livro} = nome do livro\n\n"
        f"Mensagem atual:\n\n{atual}"
    )


@dp.callback_query(F.data == "editar_sticker_nao_encontrei")
async def editar_sticker_nao_encontrei(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()
    modo_edicao[callback.from_user.id] = "sticker_nao_encontrei"

    await callback.message.answer(
        "🖼️ Envie agora a figurinha usada em “não encontrei o livro”."
    )


@dp.callback_query(F.data == "voltar_menu")
async def voltar_menu(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    await callback.message.answer(
        "📚 Menu principal:",
        reply_markup=menu_pv()
    )


@dp.callback_query(F.data == "limpar")
async def limpar(callback: CallbackQuery):
    if not autorizado(callback.from_user.id):
        await callback.answer("Sem permissão.", show_alert=True)
        return

    await callback.answer()

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'concluido'")
    total = cursor.fetchone()[0]

    if total == 0:
        await callback.message.answer("✅ Não há missões concluídas para limpar.")
        return

    cursor.execute("DELETE FROM pedidos WHERE status = 'concluido'")
    conn.commit()

    await callback.message.answer(
        f"🧹 {total} missão(ões) concluída(s) foram apagadas.",
        reply_markup=menu_pv()
    )


async def set_commands():
    commands = [
        BotCommand(command="start", description="Abrir painel da Guardiã"),
        BotCommand(command="menu", description="Abrir menu principal"),
    ]
    await bot.set_my_commands(commands)


async def main():
    print("Bot Guardiã dos Livros iniciado...")
    await set_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
