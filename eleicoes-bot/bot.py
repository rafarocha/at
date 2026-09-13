from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import gspread, datetime, asyncio, os, tempfile
from faster_whisper import WhisperModel

# --- conecta nas abas da planilha, usando a chave do passo 4 ---
PLANILHA = gspread.service_account(filename="creds.json").open("checkpoints-150ze")
SHEET_CHECKPOINTS = PLANILHA.worksheet("checkpoints")
SHEET_OCORRENCIAS = PLANILHA.worksheet("ocorrencias")
SHEET_RONDAS = PLANILHA.worksheet("rondas")

# Tipos de ocorrência disponíveis no fluxo rápido de reporte (1 toque + nome + texto curto).
TIPOS_OCORRENCIA = [
    ("FILA", "🚶 Fila grande"),
    ("URNA", "🗳️ Problema na urna"),
    ("ENERGIA", "⚡ Energia/bateria"),
    ("SEGURANCA", "🚨 Segurança/ordem"),
    ("OUTRO", "⚠️ Outro"),
]

# Transcrição de observações por áudio — roda local (sem custo, sem depender de outra API além
# do Telegram/Sheets). O modelo (~150MB) é baixado sozinho na 1ª vez que o bot roda (precisa de
# internet só nesse instante); depois disso funciona offline. Num computador mais fraco, troque
# "small" por "base" (mais rápido, um pouco menos preciso).
MODELO_VOZ = WhisperModel("small", device="cpu", compute_type="int8")

def teclado_secoes(prefixo):
    botoes = [InlineKeyboardButton(f"Seção {i:02d}", callback_data=f"{prefixo}:{i:02d}") for i in range(1, 21)]
    return InlineKeyboardMarkup([botoes[i:i + 4] for i in range(0, len(botoes), 4)])

def teclado_tipos():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"tipo:{cod}")] for cod, label in TIPOS_OCORRENCIA])

def contar_palavras(texto):
    return len([p for p in texto.strip().split() if p])

def transcrever(caminho):
    # roda em thread separada (veja audio_recebido) porque é uma chamada bloqueante/pesada de CPU
    segmentos, _info = MODELO_VOZ.transcribe(caminho, language="pt", beam_size=1)
    return " ".join(seg.text.strip() for seg in segmentos).strip()

async def start(update: Update, ctx):
    # chamado ao tocar em "📲 Confirmar T##", "📲 Registrar Ronda" ou "📢 Reportar Ocorrência" do guia de bolso
    # (o Telegram abre com /start T07, /start RONDA, /start OCORRENCIA, /start G01, etc. — o app do
    # Telegram às vezes só MOSTRA "/start" na tela, sem o código, mas o código chega certinho aqui
    # em ctx.args; se a próxima pergunta for "Qual seção?"/"Quem confirmou?", está tudo certo)
    code = ctx.args[0] if ctx.args else None
    if not code:
        await update.message.reply_text("Use o botão do guia de bolso para abrir com o código certo.")
        return
    ctx.user_data.clear()
    ctx.user_data["codigo"] = code

    if code == "OCORRENCIA":
        ctx.user_data["fluxo"] = "ocorrencia"
        await update.message.reply_text("Em qual seção aconteceu?", reply_markup=teclado_secoes("osec"))
        return

    ctx.user_data["fluxo"] = "checkpoint"
    # T## e RONDA são por seção; G## é único para o local inteiro (pula a pergunta de seção)
    if code.startswith("T") or code == "RONDA":
        await update.message.reply_text("Qual seção?", reply_markup=teclado_secoes("sec"))
    else:
        ctx.user_data["secao"] = ""
        ctx.user_data["etapa"] = "nomes"
        await update.message.reply_text("Quem confirmou? (nomes separados por 'e', nunca por vírgula)")

async def secao_escolhida(update: Update, ctx):
    query = update.callback_query
    ctx.user_data["secao"] = query.data.split(":")[1]
    ctx.user_data["etapa"] = "nomes"
    await query.answer()
    await query.edit_message_text(
        f"Seção {ctx.user_data['secao']} — quem confirmou? (nomes separados por 'e', nunca por vírgula)"
    )

async def ocorrencia_secao_escolhida(update: Update, ctx):
    query = update.callback_query
    ctx.user_data["secao"] = query.data.split(":")[1]
    await query.answer()
    await query.edit_message_text(
        f"Seção {ctx.user_data['secao']} — qual o tipo de ocorrência?", reply_markup=teclado_tipos()
    )

async def ocorrencia_tipo_escolhido(update: Update, ctx):
    query = update.callback_query
    ctx.user_data["tipo"] = query.data.split(":")[1]
    ctx.user_data["etapa"] = "nome_ocorrencia"
    await query.answer()
    await query.edit_message_text("Quem está reportando? (seu nome)")

async def gravar_checkpoint_e_responder(update: Update, ctx):
    codigo = ctx.user_data.get("codigo")
    agora = datetime.datetime.now()
    SHEET_CHECKPOINTS.append_row([
        codigo, ctx.user_data.get("secao", ""), "", "", "concluido",
        ctx.user_data.get("nomes", ""), agora.strftime("%Y-%m-%d %H:%M"), ctx.user_data.get("observacao", ""),
    ])
    # RONDA também alimenta a aba "rondas" com os números (fila/votados) usados no mapa e nos gráficos
    if codigo == "RONDA":
        SHEET_RONDAS.append_row([
            ctx.user_data.get("secao", ""), agora.strftime("%H:%M"),
            ctx.user_data.get("fila", ""), ctx.user_data.get("votados", ""), "",
            ctx.user_data.get("observacao", ""), ctx.user_data.get("nomes", ""),
        ])
    await update.message.reply_text(f"✅ {codigo} confirmado às {agora:%H:%M}. Obrigado!")
    ctx.user_data.clear()

async def processar_observacao(update: Update, ctx, texto):
    # chamado tanto por texto (texto_recebido) quanto por áudio já transcrito (audio_recebido)
    observacao = "" if texto.lower() in ("não", "nao", "n", "-") else texto
    if contar_palavras(observacao) > 20:
        await update.message.reply_text("Observação muito longa — resuma em até 20 palavras, por favor (pode ser um novo áudio curto):")
        return
    ctx.user_data["observacao"] = observacao
    if ctx.user_data.get("codigo") == "RONDA":
        # Ronda também pede os dois números usados no mapa/gráficos da home
        ctx.user_data["etapa"] = "fila"
        await update.message.reply_text("Quantas pessoas estão na fila da seção agora? (só o número, ex.: 8)")
        return
    await gravar_checkpoint_e_responder(update, ctx)

async def processar_descricao_ocorrencia(update: Update, ctx, texto):
    # chamado tanto por texto (texto_recebido) quanto por áudio já transcrito (audio_recebido)
    if contar_palavras(texto) > 20:
        await update.message.reply_text("Muito longo — resuma em até 20 palavras, por favor (pode ser um novo áudio curto):")
        return
    SHEET_OCORRENCIAS.append_row([
        ctx.user_data.get("tipo", "OUTRO"), ctx.user_data.get("secao", ""), texto,
        ctx.user_data.get("nome", ""), datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "aberta",
    ])
    await update.message.reply_text("📢 Ocorrência registrada — os administradores vão ver no painel. Obrigado!")
    ctx.user_data.clear()

async def texto_recebido(update: Update, ctx):
    etapa = ctx.user_data.get("etapa")
    if not etapa:
        return
    texto = update.message.text.strip()

    if etapa == "nomes":
        nomes = texto.replace(",", " e ")  # rede de segurança contra vírgula (quebraria o CSV)
        ctx.user_data["nomes"] = nomes
        ctx.user_data["etapa"] = "observacao"
        await update.message.reply_text('Alguma observação sobre este item? Pode digitar (até 20 palavras) ou mandar um áudio curto — ou envie "não" para pular.')
        return

    if etapa == "observacao":
        await processar_observacao(update, ctx, texto)
        return

    if etapa == "fila":
        if not texto.isdigit():
            await update.message.reply_text("Envie só o número de pessoas na fila agora (ex.: 8):")
            return
        ctx.user_data["fila"] = texto
        ctx.user_data["etapa"] = "votados"
        await update.message.reply_text("Quantos eleitores já votaram nesta seção até agora (segundo o terminal)?")
        return

    if etapa == "votados":
        if not texto.isdigit():
            await update.message.reply_text("Envie só o número de eleitores que já votaram (ex.: 180):")
            return
        ctx.user_data["votados"] = texto
        await gravar_checkpoint_e_responder(update, ctx)
        return

    if etapa == "nome_ocorrencia":
        ctx.user_data["nome"] = texto
        ctx.user_data["etapa"] = "descricao_ocorrencia"
        await update.message.reply_text("Descreva em até 20 palavras o que aconteceu (pode digitar ou mandar um áudio curto):")
        return

    if etapa == "descricao_ocorrencia":
        await processar_descricao_ocorrencia(update, ctx, texto)
        return

async def audio_recebido(update: Update, ctx):
    # observação (do checkpoint/ronda) e descrição de ocorrência aceitam um áudio curto no lugar
    # do texto — transcrevemos localmente (Whisper) e seguimos o fluxo normal com o texto obtido
    etapa = ctx.user_data.get("etapa")
    if etapa not in ("observacao", "descricao_ocorrencia"):
        await update.message.reply_text("Não esperava um áudio agora — responda por texto, por favor.")
        return

    aviso = await update.message.reply_text("🎤 Ouvindo o áudio…")
    arquivo = await update.message.voice.get_file()
    caminho = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False).name
    await arquivo.download_to_drive(caminho)
    try:
        texto = await asyncio.to_thread(transcrever, caminho)
    finally:
        os.remove(caminho)

    if not texto:
        await aviso.edit_text("Não consegui entender o áudio — pode digitar a observação por texto?")
        return

    await aviso.edit_text(f'🎤 Entendi: "{texto}"')
    if etapa == "observacao":
        await processar_observacao(update, ctx, texto)
    else:
        await processar_descricao_ocorrencia(update, ctx, texto)

with open("token.txt") as _f:
    BOT_TOKEN = _f.read().strip()  # nunca commitar este arquivo — veja .gitignore

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(secao_escolhida, pattern="^sec:"))
app.add_handler(CallbackQueryHandler(ocorrencia_secao_escolhida, pattern="^osec:"))
app.add_handler(CallbackQueryHandler(ocorrencia_tipo_escolhido, pattern="^tipo:"))
app.add_handler(MessageHandler(filters.VOICE, audio_recebido))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_recebido))

print("Bot rodando... deixe este terminal aberto (Ctrl+C para parar).")
app.run_polling()
