import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    AIORateLimiter
)
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import random
import re
import asyncio

# Configurações iniciais
load_dotenv()

class SecurityFilter(logging.Filter):
    def filter(self, record):
        sensitive_keywords = ['token', 'senha', 'password']
        msg = record.getMessage().lower()
        return not any(keyword in msg for keyword in sensitive_keywords)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
for handler in logging.root.handlers:
    handler.addFilter(SecurityFilter())

def escape_markdown(text):
    if not text:
        return ""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

# Dados da FURIA com caracteres escapados corretamente
FURIA_DATA = {
    "csgo": [
        {"nome": "yuurih", "funcao": "Rifler", "idade": 25},
        {"nome": "KSCERATO", "funcao": "Rifler (Lurker)", "idade": 25},
        {"nome": "FalleN", "funcao": "In-game leader", "idade": 33},
        {"nome": "molody", "funcao": "AWPer", "idade": 20},
        {"nome": "YEKINDAR", "funcao": "Rifler (Entry Fragger) (Stand-in)", "idade": 25},
        {"nome": "Sidde", "funcao": "Coach", "idade": 28}
    ],
    "valorant": [
        {"nome": "Khalil", "funcao": "", "idade": 20},
        {"nome": "havoc", "funcao": "", "idade": 19},
        {"nome": "heat", "funcao": "", "idade": 22},
        {"nome": "raafa", "funcao": "In-game leader", "idade": 31},
        {"nome": "pryze", "funcao": "", "idade": 26},
        {"nome": "peu", "funcao": "Coach", "idade": 32}
    ],
    "proximos_jogos": {
        "csgo": "Ainda sem data para próxima partida",
        "valorant": "Não há partidas de FURIA Esports Valorant agendadas\\."
    },
    "ultimos_resultados": {
        "csgo": [
            {"adversario": "The MongolZ", "resultado": "0\\-2", "evento": "09/04/2025"},
            {"adversario": "Virtus.pro", "resultado": "0\\-2", "evento": "08/04/2025"}
        ],
        "valorant": [
            {"adversario": "Mibr", "resultado": "1\\-2", "evento": "18/04/2025 - VCT 25 : AMER Stage 1"},
            {"adversario": "Cloud9", "resultado": "0\\-2", "evento": "12/04/2025 - VCT 25 : AMER Stage 1"}
        ]
    },
    "gritos": [
        "FURIA\\! FURIA\\! FURIA\\!",
        "VAMO FURIA CARALHO\\!",
        "É HOJE QUE A FURIA COME\\!",
        "TÁ CHEGANDO A FURIA\\!",
        "FURIA ACIMA DE TUDO\\!"
    ],
    "noticias": [
        "🎙️ molodoy revela surpresa com convite da FURIA e admite: \"Não teve nenhum teste\"",
        "⚖️ Conflitos de interesse no Major de Austin incluem arT e FURIA; entenda",
        "🤼 Presidente relata confusão com time de Neymar após jogo na Kings League",
        "🆕 FURIA confirma adição de YEKINDAR como stand-in"
    ]
}

SAUDACOES = [
    "🐆 Pronto pra acompanhar a pantera?",
    "🔥 Hoje a FURIA vai comer\\! O que você quer saber\\?",
    "⚡ Tá afim de quais informações furiosas hoje\\?",
    "💛🖤 FURIA acima de tudo! Me diga o que precisa!",
    "🎮 E aí, campeão? Vamos falar de esports?",
    "🐆🔥 FURIA mode ON! O que vamos ver hoje?",
    "💥 Preparado para informações explosivas da FURIA?"
]

RESPOSTAS_ALEATORIAS = [
    "🐆 FURIA acima de tudo! Use os botões ou pergunte sobre\\:\\n• CS\\:GO 2\\n• Valorant\\n• Jogos\\n• Resultados\\n• Notícias\\n• Loja",
    "🔥 Hoje a pantera tá faminta\\! Me pergunte algo sobre nossos times\\!",
    "⚡ Não entendi\\.\\.\\. quer tentar de novo\\? Posso te ajudar com\\:\\n- Elenco\\n- Próximos jogos\\n- Resultados\\n- Notícias",
    "💛🖤 Vamo junto\\, furioso\\! Use os botões abaixo ou me pergunte sobre o time\\!"
]

def main_keyboard():
    return [
        [InlineKeyboardButton("🎮 CS:GO 2", callback_data='csgo'),
         InlineKeyboardButton("💥 Valorant", callback_data='valorant')],
        [InlineKeyboardButton("📅 Jogos", callback_data='proximos_jogos'),
         InlineKeyboardButton("🏆 Resultados", callback_data='ultimos_resultados')],
        [InlineKeyboardButton("📰 Notícias", callback_data='noticias'),
         InlineKeyboardButton("🔥 Grito de Guerra", callback_data='grito')],
        [InlineKeyboardButton("🛒 Loja", callback_data='loja'),
         InlineKeyboardButton("📸 Instagram", callback_data='instagram')]
    ]

def with_back_button():
    keyboard = main_keyboard()
    keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data='menu_principal')])
    return keyboard

async def show_main_menu(query):
    await query.edit_message_text(
        text=f"🐆 *{escape_markdown(random.choice(SAUDACOES))}* 🐆\n\n⚡ *O que vamos ver agora\\?*",
        reply_markup=InlineKeyboardMarkup(main_keyboard()),
        parse_mode='MarkdownV2'
    )

def format_csgo_players():
    players = []
    for p in FURIA_DATA['csgo']:
        name = escape_markdown(p['nome'])
        role = f" \n_{escape_markdown(p['funcao'])}_" if p['funcao'] else ""
        players.append(f"➤ *{name}*{role} \\(*{p['idade']} anos*\\)\n")
    return "🎮 *CS\\:GO 2 \\- ELENCO DA FURIA* 🎮\n\n" + "".join(players)

def format_valorant_players():
    players = []
    for p in FURIA_DATA['valorant']:
        name = escape_markdown(p['nome'])
        role = f" \n_{escape_markdown(p['funcao'])}_" if p['funcao'] else ""
        players.append(f"➤ *{name}*{role} \\(*{p['idade']} anos*\\)\n")
    return "💥 *VALORANT \\- ELENCO DA FURIA* 💥\n\n" + "".join(players)

def format_next_matches():
    csgo_msg = f"🎮 *CS\\:GO 2*\n\n{FURIA_DATA['proximos_jogos']['csgo']}"
    valorant_msg = f"\n\n💥 *VALORANT*\n\n{FURIA_DATA['proximos_jogos']['valorant']}"
    return "📅 *PRÓXIMOS JOGOS* 📅\n\n" + csgo_msg + valorant_msg

def format_results(game_type='csgo'):
    results = []
    for r in FURIA_DATA['ultimos_resultados'][game_type]:
        opponent = escape_markdown(r['adversario'])
        event = escape_markdown(r['evento'])
        score = r['resultado']
        outcome = '✅ *VITÓRIA*' if score.startswith('2') or (score.startswith('1') and game_type == 'valorant') else '❌ *DERROTA*'
        
        if game_type == 'csgo':
            result_text = f"➤ {outcome}\nvs {opponent} {score}\n"
            result_text += f"\\({event}\\)"
        else:
            result_text = f"➤ {outcome}\nFURIA {score} vs {opponent}\n"
            result_text += f"\\({event}\\)"
        
        results.append(result_text)
    
    title = "🎮 *CS\\:GO 2*" if game_type == 'csgo' else "💥 *VALORANT*"
    return f"🏆 *ÚLTIMOS RESULTADOS* 🏆\n\n{title}\n\n" + "\n".join(results)

async def start(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        welcome_message = (
            f"🐆🔥 *{escape_markdown(random.choice(SAUDACOES))}* 🔥🐆\n\n"
            f"🤖 *Eu sou o FURIA Bot\\, seu pitaco eletrônico sobre tudo da Pantera\\!*\n\n"
            "⚡ *Vamo nessa\\! O que você quer saber hoje\\?*\n\n"
            "• 🎮 _CS\\:GO 2 \\- Elenco e informações_ \n"
            "• 💥 _Valorant \\- Time brasileiro no VCT_ \n"
            "• 📅 _Próximos jogos \\- Quando a FURIA vai comer\\?_ \n"
            "• 🏆 _Resultados recentes \\- Vitórias e aprendizados_ \n"
            "• 📰 _Notícias quentinhas direto do draft5_ \n"
            "• 🔥 _Gritos de guerra \\- Pra botar pra quebrar\\!_ \n"
            "• 🛍️ _Loja oficial \\- Mostra que você é furioso_ \n\n"
            "🎙️ *Dica\\:* Me chame no privado ou use os botões abaixo\\!"
        )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=InlineKeyboardMarkup(main_keyboard()),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Erro no /start: {e}")
        await error_handler(update, context)

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu_principal':
        await show_main_menu(query)
        return
    
    if query.data == 'loja':
        await query.edit_message_text(
            text="🛒 *Loja Oficial da FURIA*\n\nConfira nossos produtos em: [furia\\.gg](https\\://www\\.furia\\.gg)",
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup(with_back_button())
        )
        return
    
    if query.data == 'instagram':
        await query.edit_message_text(
            text="📸 *Instagram Oficial*\n\nAcesse\\: [\\@furiagg](https\\://www\\.instagram\\.com/furiagg)",
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup(with_back_button())
        )
        return
    
    if query.data == 'csgo':
        response = format_csgo_players()
    elif query.data == 'valorant':
        response = format_valorant_players()
    elif query.data == 'proximos_jogos':
        response = format_next_matches()
    elif query.data == 'ultimos_resultados':
        csgo_results = format_results('csgo')
        valorant_results = format_results('valorant')
        response = f"{csgo_results}\n\n{valorant_results}"
    elif query.data == 'noticias':
        response = "📰 *ÚLTIMAS NOTÍCIAS* 📰\n\n" + "\n".join(
            f"➤ {escape_markdown(noticia)}\n"
            for noticia in FURIA_DATA['noticias']
        ) + "\n\n🔍 _Mais em\\:_ [Draft5\\.gg](https\\://draft5\\.gg/equipe/330\\-FURIA)"
    elif query.data == 'grito':
        response = f"🔥 *GRITO DE GUERRA* 🔥\n\n*{random.choice(FURIA_DATA['gritos'])}*"
    
    await query.edit_message_text(
        text=response,
        reply_markup=InlineKeyboardMarkup(with_back_button()),
        parse_mode='MarkdownV2',
        disable_web_page_preview=True
    )

async def text_handler(update: Update, context: CallbackContext) -> None:
    try:
        text = update.message.text.lower()
        
        if any(word in text for word in ['csgo', 'cs2', 'cs:go', 'counter strike']):
            response = format_csgo_players()
        elif any(word in text for word in ['valorant', 'val']):
            response = format_valorant_players()
        elif any(word in text for word in ['jogador', 'jogadores', 'time', 'elenc']):
            response = "Escolha o jogo:\n\n" + format_csgo_players() + "\n" + format_valorant_players()
        elif any(word in text for word in ['próximo', 'proximo', 'jogo', 'jogos', 'calendário']):
            response = format_next_matches()
        elif any(word in text for word in ['resultado', 'ultimo', 'último', 'partida', 'partidas']):
            csgo_results = format_results('csgo')
            valorant_results = format_results('valorant')
            response = f"{csgo_results}\n\n{valorant_results}"
        elif any(word in text for word in ['noticia', 'notícia', 'novidade']):
            response = "📰 *ÚLTIMAS NOTÍCIAS* 📰\n\n" + "\n".join(
                f"➤ {escape_markdown(noticia)}\n"
                for noticia in FURIA_DATA['noticias']
            ) + "\n\n🔍 _Mais em:_ [Draft5\\.gg](https://draft5.gg/equipe/330-FURIA)"
        elif any(word in text for word in ['grito', 'gritar', 'war cry', 'vamo']):
            response = f"🔥 *GRITO DE GUERRA* 🔥\n\n*{random.choice(FURIA_DATA['gritos'])}*"
        elif any(word in text for word in ['instagram', 'foto', 'rede social']):
            response = "📸 *Instagram Oficial*\n\nAcesse: [@furiagg](https://www.instagram.com/furiagg)"
        elif any(word in text for word in ['loja', 'produtos', 'comprar']):
            response = "🛒 *Loja Oficial da FURIA*\n\nConfira nossos produtos em: [furia.gg](https://www.furia.gg)"
        else:
            response = escape_markdown(random.choice(RESPOSTAS_ALEATORIAS))
        
        await update.message.reply_text(
            text=response,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(with_back_button())
        )
    except Exception as e:
        logger.error(f"Erro no text_handler: {e}")
        await error_handler(update, context)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Ocorreu um erro inesperado. Tente novamente mais tarde."
            )
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro: {e}")

async def on_startup(app: Application) -> None:
    logger.info("Bot inicializado com segurança")
    await app.bot.set_my_commands([
        ('start', 'Inicia o bot'),
        ('help', 'Mostra ajuda')
    ])

def build_application(token: str) -> Application:
    rate_limiter = AIORateLimiter(
        overall_max_rate=30,
        overall_time_period=60,
        group_max_rate=20,
        group_time_period=60
    )
    
    return (
        Application.builder()
        .token(token)
        .rate_limiter(rate_limiter)
        .post_init(on_startup)
        .build()
    )

async def main() -> None:
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        raise ValueError("Token do Telegram não configurado!")

    application = build_application(TOKEN)
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_error_handler(error_handler)

    logger.info("Iniciando bot...")
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        while True:
            await asyncio.sleep(3600)
            
    except asyncio.CancelledError:
        logger.info("Recebido sinal de desligamento")
    except Exception as e:
        logger.critical(f"Erro durante execução: {e}")
    finally:
        logger.info("Encerrando bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot encerrado com sucesso")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
    except Exception as e:
        logger.critical(f"Erro fatal: {e}")