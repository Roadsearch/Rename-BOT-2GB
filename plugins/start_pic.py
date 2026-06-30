"""
plugins/start_pic.py
Gestion de l'image/GIF de démarrage du bot.
— L'admin envoie une photo ou un GIF avec la légende /setpic
— Stocké dans Supabase (table bot_settings)
— Affiché à chaque /start pour tous les utilisateurs
— Modifiable à tout moment avec /setpic
— Supprimable avec /delpic
— Visualisable avec /viewpic
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helper.database import set_bot_setting, get_bot_setting, del_bot_setting

logger = logging.getLogger(__name__)
admin_filter = filters.user(Config.ADMIN)


# ── /setpic — envoi d'une photo ou GIF avec légende ─────────────────────────

@Client.on_message(
    filters.private & admin_filter
    & (filters.photo | filters.animation)
    & filters.caption
    & filters.regex(r"^/setpic")
)
async def setpic_with_caption(bot: Client, msg: Message):
    """
    L'admin envoie une photo ou GIF avec la légende /setpic
    → stocke le file_id + type dans Supabase.
    """
    if msg.photo:
        file_id   = msg.photo.file_id
        media_type = "photo"
    elif msg.animation:
        file_id   = msg.animation.file_id
        media_type = "animation"
    else:
        await msg.reply_text("❌ Envoie une **photo** ou un **GIF** avec la légende `/setpic`.")
        return

    await set_bot_setting("start_pic_id",   file_id)
    await set_bot_setting("start_pic_type", media_type)
    logger.info(f"[StartPic] Défini par {msg.from_user.id} — type={media_type}")

    await msg.reply_text(
        f"✅ **Image de démarrage enregistrée !**\n\n"
        f"Type : `{media_type}`\n"
        f"Elle sera affichée à chaque `/start`.\n\n"
        f"Pour la changer : envoie une nouvelle photo/GIF avec `/setpic`\n"
        f"Pour la supprimer : `/delpic`"
    )


# ── /setpic seul (sans média) — rappel d'usage ───────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("setpic"))
async def setpic_cmd(bot: Client, msg: Message):
    """Si /setpic est envoyé sans photo attachée, affiche les instructions."""
    if msg.photo or msg.animation:
        return  # déjà géré par le handler au-dessus
    await msg.reply_text(
        "📸 **Comment définir l'image de démarrage :**\n\n"
        "1. Envoie une **photo** ou un **GIF**\n"
        "2. Dans la légende, écris `/setpic`\n"
        "3. Envoie ✅\n\n"
        "L'image sera stockée dans Supabase et affichée à chaque `/start`."
    )


# ── /viewpic — voir l'image actuelle ─────────────────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("viewpic"))
async def viewpic_cmd(bot: Client, msg: Message):
    file_id    = await get_bot_setting("start_pic_id")
    media_type = await get_bot_setting("start_pic_type") or "photo"

    if not file_id:
        await msg.reply_text(
            "❌ **Aucune image de démarrage définie.**\n\n"
            "Envoie une photo ou un GIF avec la légende `/setpic`."
        )
        return

    caption = f"🖼️ **Image de démarrage actuelle**\nType : `{media_type}`"

    if media_type == "animation":
        await msg.reply_animation(animation=file_id, caption=caption)
    else:
        await msg.reply_photo(photo=file_id, caption=caption)


# ── /delpic — supprimer l'image ──────────────────────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("delpic"))
async def delpic_cmd(bot: Client, msg: Message):
    file_id = await get_bot_setting("start_pic_id")
    if not file_id:
        await msg.reply_text("❌ **Aucune image à supprimer.**")
        return

    await del_bot_setting("start_pic_id")
    await del_bot_setting("start_pic_type")
    logger.info(f"[StartPic] Supprimée par {msg.from_user.id}")
    await msg.reply_text(
        "🗑️ **Image de démarrage supprimée !**\n\n"
        "Le `/start` affichera désormais uniquement le texte."
    )
