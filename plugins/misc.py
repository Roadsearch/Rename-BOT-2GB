"""
plugins/misc.py — /ping, /help, /donate
"""
import time, logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Txt

logger = logging.getLogger(__name__)


@Client.on_message(filters.private & filters.command("ping"))
async def ping_cmd(bot: Client, msg: Message):
    start = time.time()
    sent  = await msg.reply_text("🏓 **Pong !**")
    ms    = (time.time() - start) * 1000
    if ms < 100:   quality = "🟢 Excellente"
    elif ms < 300: quality = "🟡 Bonne"
    else:          quality = "🔴 Lente"
    await sent.edit_text(
        f"🏓 **Pong !**\n\n"
        f"⚡ **Latence :** `{ms:.0f} ms`\n"
        f"📶 **Qualité :** {quality}"
    )


@Client.on_message(filters.private & filters.command("donate"))
async def donate_cmd(bot: Client, msg: Message):
    await msg.reply_text(Txt.DONATE_TXT)


@Client.on_message(filters.private & filters.command("help"))
async def help_cmd(bot: Client, msg: Message):
    await msg.reply_text(Txt.HELP_TXT)
