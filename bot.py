import os
import re
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "TON_TOKEN_ICI")
UUID = "d8a6b1c2-3f4e-4a5b-8c9d-1e2f3a4b5c6d"
IP = "192.179.18.100"
PORT = 443
SNI = "crashlyticsreports-pa.googleapis.com"
PATH = "/@kcorp237"
REMARK = "@KCORP-TECH"
# ================================================

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "KCORP Bot Live"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def extraire_host(texte: str) -> str | None:
    texte = texte.strip().lower()
    m = re.search(r"host=([a-z0-9\-]+\.run\.app)", texte)
    if m: return m.group(1)
    m = re.search(r"([a-z0-9\-]+\.[a-z0-9\-]+\.run\.app)", texte, re.IGNORECASE)
    if m: return m.group(1).lower()
    return None

def generer_lien_vless(host: str) -> str:
    path_encoded = PATH.replace("/", "%2F")
    return f"vless://{UUID}@{IP}:{PORT}?encryption=none&security=tls&sni={SNI}&type=ws&host={host}&path={path_encoded}#{REMARK}"

# ======== MESSAGE /START BEAU ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📞 Contact DEV", url="https://t.me/metajeady")]]
    text = (
        "🚀 *KCORP VLESS GENERATOR* 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 Salut ! Bienvenue sur le bot officiel *KCORP-TECH*\n\n"
        "⚙️ *Fonction :*\n"
        "Je convertis ton host Cloud Run `.run.app` en lien VLESS ultra-rapide.\n\n"
        "📝 *Utilisation :*\n"
        "1️⃣ Envoie ton host : `xxxx-xxxx.run.app`\n"
        "2️⃣ Reçois ton lien VLESS dans un cadre prêt à copier\n"
        "3️⃣ Colle dans V2rayNG / Xray\n\n"
        "🔒 _100% Gratuit | Rapide | Stable_\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 *Envoie ton host pour commencer*"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ======== TRAITEMENT VLESS ========
async def traiter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    host = extraire_host(update.message.text or "")
    if not host:
        await update.message.reply_text("❌ Host `.run.app` non trouvé\n\nEx: `xxxx.run.app`", parse_mode="Markdown")
        return

    lien = generer_lien_vless(host)
    kb = [[InlineKeyboardButton("📞 Contact DEV", url="https://t.me/metajeady")]]

    text = (
        f"✅ *Host validé :* `{host}`\n\n"
        f"```\n{lien}\n```\n\n"
        "⚠️ *NB :* RASSUREZ-VOUS D'AVOIR UTILISÉ LE DORKER DE KCORP TECH\n"
        "Si t'as pas encore de dorker, contact DEV 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, traiter))
    await app.initialize()
    await app.start()
    print("🚀 KCORP Bot démarré...")
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
