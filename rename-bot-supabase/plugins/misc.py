import time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Txt


@Client.on_message(filters.private & filters.command("ping"))
async def ping_cmd(bot: Client, msg: Message):
    start = time.time()
    sent  = await msg.reply_text("🏓 **Pong!**")
    ms    = (time.time() - start) * 1000
    await sent.edit_text(f"🏓 **Pong!** `{ms:.2f} ms`")


@Client.on_message(filters.private & filters.command("donate"))
async def donate_cmd(bot: Client, msg: Message):
    await msg.reply_text(Txt.DONATE_TXT)


@Client.on_message(filters.private & filters.command("help"))
async def help_cmd(bot: Client, msg: Message):
    await msg.reply_text(Txt.HELP_TXT)
