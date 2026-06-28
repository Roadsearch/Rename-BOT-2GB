import os
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import set_thumbnail, get_thumbnail, del_thumbnail


@Client.on_message(filters.private & filters.photo)
async def save_thumb(bot: Client, msg: Message):
    """Toute photo reçue en privé est sauvegardée comme miniature."""
    file_id = msg.photo.file_id
    await set_thumbnail(msg.from_user.id, file_id)
    await msg.reply_text("✅ **Thumbnail saved permanently!**")


@Client.on_message(filters.private & filters.command(["viewthumb", "view_thumb"]))
async def view_thumb(bot: Client, msg: Message):
    thumb = await get_thumbnail(msg.from_user.id)
    if not thumb:
        await msg.reply_text("❌ **No thumbnail set!** Send a photo first.")
        return
    await msg.reply_photo(photo=thumb, caption="🖼️ **Your current thumbnail**")


@Client.on_message(filters.private & filters.command(["delthumb", "del_thumb"]))
async def delete_thumb(bot: Client, msg: Message):
    thumb = await get_thumbnail(msg.from_user.id)
    if not thumb:
        await msg.reply_text("❌ **No thumbnail to delete.**")
        return
    await del_thumbnail(msg.from_user.id)
    await msg.reply_text("🗑️ **Thumbnail deleted!**")
