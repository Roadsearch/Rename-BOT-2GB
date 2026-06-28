from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import (
    set_caption, get_caption, del_caption,
    set_prefix, get_prefix, del_prefix,
    set_suffix, get_suffix, del_suffix,
)


# ── Caption ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("set_caption"))
async def cmd_set_caption(bot: Client, msg: Message):
    if len(msg.command) < 2:
        await msg.reply_text(
            "**Usage :** `/set_caption Your caption here`\n\n"
            "**Variables disponibles :**\n"
            "`{filename}` `{filesize}` `{duration}`"
        )
        return
    caption = msg.text.split(None, 1)[1]
    await set_caption(msg.from_user.id, caption)
    await msg.reply_text(f"✅ **Caption saved!**\n\n`{caption}`")


@Client.on_message(filters.private & filters.command("see_caption"))
async def cmd_see_caption(bot: Client, msg: Message):
    caption = await get_caption(msg.from_user.id)
    if not caption:
        await msg.reply_text("❌ **No custom caption set.**")
        return
    await msg.reply_text(f"📝 **Your caption:**\n\n`{caption}`")


@Client.on_message(filters.private & filters.command("del_caption"))
async def cmd_del_caption(bot: Client, msg: Message):
    await del_caption(msg.from_user.id)
    await msg.reply_text("🗑️ **Caption deleted!**")


# ── Prefix ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("set_prefix"))
async def cmd_set_prefix(bot: Client, msg: Message):
    if len(msg.command) < 2:
        await msg.reply_text("**Usage :** `/set_prefix YourPrefix`")
        return
    prefix = msg.text.split(None, 1)[1]
    await set_prefix(msg.from_user.id, prefix)
    await msg.reply_text(f"✅ **Prefix saved :** `{prefix}`")


@Client.on_message(filters.private & filters.command("see_prefix"))
async def cmd_see_prefix(bot: Client, msg: Message):
    prefix = await get_prefix(msg.from_user.id)
    if not prefix:
        await msg.reply_text("❌ **No prefix set.**")
        return
    await msg.reply_text(f"🔤 **Your prefix :** `{prefix}`")


@Client.on_message(filters.private & filters.command("del_prefix"))
async def cmd_del_prefix(bot: Client, msg: Message):
    await del_prefix(msg.from_user.id)
    await msg.reply_text("🗑️ **Prefix deleted!**")


# ── Suffix ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("set_suffix"))
async def cmd_set_suffix(bot: Client, msg: Message):
    if len(msg.command) < 2:
        await msg.reply_text("**Usage :** `/set_suffix YourSuffix`")
        return
    suffix = msg.text.split(None, 1)[1]
    await set_suffix(msg.from_user.id, suffix)
    await msg.reply_text(f"✅ **Suffix saved :** `{suffix}`")


@Client.on_message(filters.private & filters.command("see_suffix"))
async def cmd_see_suffix(bot: Client, msg: Message):
    suffix = await get_suffix(msg.from_user.id)
    if not suffix:
        await msg.reply_text("❌ **No suffix set.**")
        return
    await msg.reply_text(f"🔤 **Your suffix :** `{suffix}`")


@Client.on_message(filters.private & filters.command("del_suffix"))
async def cmd_del_suffix(bot: Client, msg: Message):
    await del_suffix(msg.from_user.id)
    await msg.reply_text("🗑️ **Suffix deleted!**")
