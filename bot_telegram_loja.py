#
# --- FICHEIRO: bot_telegram_loja.py (Versão COMPLETA e SEGURA para Online) ---
#
import logging
import os  # <-- A GRANDE MUDANÇA (Passo 1)
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler, 
    PicklePersistence 
)

# --- CONFIGURAÇÃO INICIAL ---

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- O NOSSO STOCK (BASE DE DADOS) ---
PRODUTOS = {
    "camisetas": {
        "cam001": {"nome": "Camiseta Branca Básica", "preco": 50.00, "cor": "branca"},
        "cam002": {"nome": "Camiseta Preta Estampada", "preco": 65.00, "cor": "preta"}
    },
    "calcas": {
        "cal001": {"nome": "Calça Jeans Reta", "preco": 120.00, "tamanho": "M"},
        "cal002": {"nome": "Calça Moletom Cinza", "preco": 90.00, "tamanho": "G"}
    }
}

# --- ESTADOS DA CONVERSA (para o funil de vendas) ---
(ESTADO_INICIO, ESTADO_VENDO_PRODUTOS, 
 ESTADO_CARRINHO, ESTADO_CHECKOUT_NOME, ESTADO_CHECKOUT_MORADA) = range(5)

# --- FUNÇÕES DE AJUDA (Sem alteração) ---

def mostrar_produtos_texto(categoria):
    """Gera o TEXTO que lista os produtos."""
    if categoria not in PRODUTOS:
        return f"Desculpe, categoria '{categoria}' não encontrada."
        
    texto = f"--- MOSTRANDO {categoria.upper()} ---\n\n"
    for codigo, detalhes in PRODUTOS[categoria].items():
        texto += f"Código: {codigo}\n"
        texto += f"  Nome: {detalhes['nome']}\n"
        texto += f"  Preço: R$ {detalhes['preco']:.2f}\n"
        texto += "-------------------\n"
    
    texto += "\nDigite o código do produto (ex: 'cam001') para adicionar."
    return texto

def adicionar_ao_carrinho(carrinho_do_utilizador, codigo):
    """Adiciona um item ao carrinho do utilizador e retorna uma string de confirmação."""
    produto_encontrado = None
    for categoria, produtos_na_categoria in PRODUTOS.items():
        if codigo in produtos_na_categoria:
            produto_encontrado = produtos_na_categoria[codigo]
            break
    
    if not produto_encontrado:
        return f"Desculpe, não encontrei o produto com o código '{codigo}'."

    if codigo in carrinho_do_utilizador:
        carrinho_do_utilizador[codigo]['quantidade'] += 1
    else:
        carrinho_do_utilizador[codigo] = {
            "nome": produto_encontrado["nome"],
            "preco": produto_encontrado["preco"],
            "quantidade": 1
        }
    
    return f"✅ Adicionado '{produto_encontrado['nome']}' ao carrinho."

def mostrar_carrinho_texto(carrinho_do_utilizador):
    """Gera o TEXTO que mostra o carrinho."""
    if not carrinho_do_utilizador:
        return "--- O seu carrinho está vazio. ---"
    
    texto = "--- SEU CARRINHO ATUAL ---\n"
    total = 0.0
    for codigo, item in carrinho_do_utilizador.items():
        subtotal = item['preco'] * item['quantidade']
        texto += f"{item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f}) - Sub: R$ {subtotal:.2f}\n"
        total += subtotal
    texto += "---------------------------------\n"
    texto += f"TOTAL DO PEDIDO: R$ {total:.2f}"
    return texto

# --- TECLADOS (BOTÕES) (Sem alteração) ---
teclado_inicio = [
    ["Ver Camisetas", "Ver Calças"],
    ["Ver Carrinho"]
]
teclado_produtos = [
    ["Voltar às categorias"]
]
teclado_carrinho = [
    ["Finalizar Compra"],
    ["Continuar a comprar"]
]


# --- FUNÇÕES PRINCIPAIS DO BOT (HANDLERS) (Sem alteração) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"Utilizador {user.first_name} iniciou o bot.")
    context.user_data['carrinho'] = {}
    markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
    await update.message.reply_text(
        f"Olá {user.first_name}! Bem-vindo à Loja Virtual. 🤖\n"
        "Eu sou o seu assistente de vendas. Use os botões para navegar.",
        reply_markup=markup
    )
    return ESTADO_INICIO

async def estado_inicio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text
    if texto == "Ver Camisetas":
        markup = ReplyKeyboardMarkup(teclado_produtos, resize_keyboard=True)
        texto_produtos = mostrar_produtos_texto("camisetas")
        await update.message.reply_text(texto_produtos, reply_markup=markup)
        return ESTADO_VENDO_PRODUTOS 
    elif texto == "Ver Calças":
        markup = ReplyKeyboardMarkup(teclado_produtos, resize_keyboard=True)
        texto_produtos = mostrar_produtos_texto("calcas")
        await update.message.reply_text(texto_produtos, reply_markup=markup)
        return ESTADO_VENDO_PRODUTOS
    elif texto == "Ver Carrinho":
        markup = ReplyKeyboardMarkup(teclado_carrinho, resize_keyboard=True)
        carrinho_atual = context.user_data.get('carrinho', {})
        texto_carrinho = mostrar_carrinho_texto(carrinho_atual)
        await update.message.reply_text(texto_carrinho, reply_markup=markup)
        return ESTADO_CARRINHO
    else:
        await update.message.reply_text("Não entendi. Por favor, use os botões.")
        return ESTADO_INICIO

async def estado_vendo_produtos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text
    if texto == "Voltar às categorias":
        markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
        await update.message.reply_text("A mostrar categorias...", reply_markup=markup)
        return ESTADO_INICIO 
    
    carrinho_atual = context.user_data.get('carrinho', {})
    confirmacao = adicionar_ao_carrinho(carrinho_atual, texto.lower())
    context.user_data['carrinho'] = carrinho_atual
    await update.message.reply_text(confirmacao)
    return ESTADO_VENDO_PRODUTOS

async def estado_carrinho_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text
    if texto == "Continuar a comprar":
        markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
        await update.message.reply_text("A mostrar categorias...", reply_markup=markup)
        return ESTADO_INICIO
    elif texto == "Finalizar Compra":
        carrinho_atual = context.user_data.get('carrinho', {})
        if not carrinho_atual:
            await update.message.reply_text("O seu carrinho está vazio! Não pode finalizar.")
            markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
            await update.message.reply_text("A mostrar categorias...", reply_markup=markup)
            return ESTADO_INICIO
        await update.message.reply_text(
            "Ótimo! Para finalizar, preciso de alguns dados.\nQual o seu NOME completo?",
            reply_markup=ReplyKeyboardRemove() 
        )
        return ESTADO_CHECKOUT_NOME
    else:
        await update.message.reply_text("Opção inválida. Use os botões.")
        return ESTADO_CARRINHO

async def estado_checkout_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nome = update.message.text
    context.user_data['nome'] = nome 
    await update.message.reply_text(
        f"Obrigado, {nome}.\nAgora, por favor, escreva a sua MORADA de entrega."
    )
    return ESTADO_CHECKOUT_MORADA 

async def estado_checkout_morada(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    morada = update.message.text
    nome = context.user_data.get('nome', 'Cliente')
    carrinho_atual = context.user_data.get('carrinho', {})
    
    texto_resumo = mostrar_carrinho_texto(carrinho_atual)
    texto_final = f"--- PEDIDO CONCLUÍDO! ---\n"
    texto_final += f"Obrigado, {nome}!\n\n"
    texto_final += "Resumo da Compra:\n"
    texto_final += texto_resumo + "\n\n"
    texto_final += f"Morada de Entrega:\n{morada}\n\n"
    texto_final += "(Um assistente humano contactará para o pagamento.)"
    
    await update.message.reply_text(texto_final)
    
    context.user_data.clear()
    
    markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
    await update.message.reply_text(
        "Compra finalizada com sucesso! 👋\nPara iniciar uma nova compra, clique em /start ou use os botões.",
        reply_markup=markup
    )
    return ESTADO_INICIO 

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    markup = ReplyKeyboardMarkup(teclado_inicio, resize_keyboard=True)
    await update.message.reply_text(
        "Ação cancelada. A limpar o seu carrinho e estado. A voltar ao início.",
        reply_markup=markup
    )
    return ESTADO_INICIO


def main() -> None:
    """Inicia o bot."""
    
    # --- !! A GRANDE MUDANÇA (Passo 2) !! ---
    # Agora, lemos o token de uma variável de ambiente segura.
    # O seu token verdadeiro NUNCA deve estar escrito aqui.
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if TOKEN is None:
        print("ERRO CRÍTICO: A variável de ambiente 'TELEGRAM_TOKEN' não foi encontrada.")
        print("O bot não pode iniciar sem o token.")
        return # Para o script imediatamente

    # O resto da configuração...
    persistence = PicklePersistence(filepath="bot_loja_data")

    application = (
        Application.builder()
        .token(TOKEN) # Usa o token seguro
        .persistence(persistence)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ESTADO_INICIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, estado_inicio_handler)
            ],
            ESTADO_VENDO_PRODUTOS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, estado_vendo_produtos_handler)
            ],
            ESTADO_CARRINHO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, estado_carrinho_handler)
            ],
            ESTADO_CHECKOUT_NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, estado_checkout_nome)
            ],
            ESTADO_CHECKOUT_MORADA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, estado_checkout_morada)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        persistent=True,
        name="loja_conversation"
    )

    application.add_handler(conv_handler)

    print("Bot a iniciar... (A 'ouvir' o Telegram)")
    application.run_polling()


if __name__ == "__main__":
    main()