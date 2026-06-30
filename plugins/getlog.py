"""
plugins/getlog.py — /getlog et /clearlog (admin uniquement).
"""
import logging, os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

logger       = logging.getLogger(__name__)
admin_filter = filters.user(Config.ADMIN)
LOG_FILE     = "bot.log"


@Client.on_message(filters.private & admin_filter & filters.command("getlog"))
async def getlog_cmd(bot: Client, msg: Message):
    n = 50
    if len(msg.command) == 2:
        try: n = min(int(msg.command[1]), 200)
        except ValueError: pass

    if not os.path.exists(LOG_FILE):
        await msg.reply_text("❌ **Fichier de log introuvable.**"); return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last   = lines[-n:]
        content = "".join(last).strip()

        if not content:
            await msg.reply_text("📋 **Le fichier de log est vide.**"); return

        if len(content) > 4096:
            await msg.reply_document(
                document=LOG_FILE,
                caption=f"📋 **Logs complets** (`{len(lines)}` lignes)"
            )
        else:
            await msg.reply_text(
                f"📋 **Dernières `{len(last)}` lignes :**\n\n```\n{content}\n```"
            )
    except Exception as e:
        await msg.reply_text(f"❌ **Erreur :** `{e}`")


@Client.on_message(filters.private & admin_filter & filters.command("clearlog"))
async def clearlog_cmd(bot: Client, msg: Message):
    try:
        open(LOG_FILE, "w").close()
        await msg.reply_text("🗑️ **Fichier de log vidé.**")
        logger.info(f"[Log] Vidé par {msg.from_user.id}")
    except Exception as e:
        await msg.reply_text(f"❌ **Erreur :** `{e}`")
