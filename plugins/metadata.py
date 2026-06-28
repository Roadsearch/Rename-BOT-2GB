from pyrogram import Client, filters
from pyrogram.types import Message
from config import Txt
from helper.database import set_metadata, get_metadata, del_metadata


@Client.on_message(filters.private & filters.command("metadata"))
async def cmd_metadata(bot: Client, msg: Message):
    if len(msg.command) < 2:
        # Affiche les instructions si pas d'argument
        await msg.reply_text(Txt.SEND_METADATA)
        return
    meta = msg.text.split(None, 1)[1]
    await set_metadata(msg.from_user.id, meta)
    await msg.reply_text(f"✅ **Metadata saved!**\n\n`{meta}`")


@Client.on_message(filters.private & filters.command("see_metadata"))
async def cmd_see_metadata(bot: Client, msg: Message):
    meta = await get_metadata(msg.from_user.id)
    if not meta:
        await msg.reply_text("❌ **No metadata set.**")
        return
    await msg.reply_text(f"📋 **Your metadata :** `{meta}`")


@Client.on_message(filters.private & filters.command("del_metadata"))
async def cmd_del_metadata(bot: Client, msg: Message):
    await del_metadata(msg.from_user.id)
    await msg.reply_text("🗑️ **Metadata deleted!**")
