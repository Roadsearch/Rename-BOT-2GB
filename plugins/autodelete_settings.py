"""
plugins/autodelete_settings.py
Fonctionnalité 5 — /autodelete : configure la durée d'auto-suppression.
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import set_auto_delete, get_auto_delete

logger = logging.getLogger(__name__)

# Délai 0 = désactivé
PRESETS = [
    ("1 min",   60),
    ("5 min",   300),
    ("15 min",  900),
    ("1 heure", 3600),
    ("Jamais",  0),
]


@Client.on_message(filters.private & filters.command("autodelete"))
async def autodelete_cmd(bot: Client, msg: Message):
    user_id    = msg.from_user.id
    current    = await get_auto_delete(user_id)
    current_txt = (
        "Désactivé" if current == 0
        else f"{current // 60} min" if current >= 60
        else f"{current} s"
    )

    # Si l'utilisateur passe un nombre en argument
    if len(msg.command) == 2:
        try:
            secs = int(msg.command[1])
            await set_auto_delete(user_id, secs)
            txt = "désactivée" if secs == 0 else f"**{secs} secondes**"
            await msg.reply_text(f"✅ **Auto-suppression réglée à {txt}.**")
            return
        except ValueError:
            pass

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"adel_{secs}")]
        for label, secs in PRESETS
    ] + [[InlineKeyboardButton("🔙 Fermer", callback_data="adel_close")]])

    await msg.reply_text(
        f"⏱️ **Auto-suppression des messages**\n\n"
        f"Réglage actuel : **{current_txt}**\n\n"
        f"Les messages envoyés par le bot seront supprimés automatiquement après le délai choisi.\n"
        f"Choisis un délai :",
        reply_markup=btn
    )


@Client.on_callback_query(filters.regex(r"^adel_(\d+|close)$"))
async def adel_cb(bot, cb):
    data = cb.data.split("_", 1)[1]

    if data == "close":
        await cb.message.delete()
        return

    secs    = int(data)
    user_id = cb.from_user.id
    await set_auto_delete(user_id, secs)

    txt = "désactivée" if secs == 0 else (
        f"{secs // 60} min" if secs >= 60 else f"{secs} s"
    )
    await cb.message.edit_text(
        f"✅ **Auto-suppression réglée à {txt}.**\n\n"
        f"Tous tes prochains fichiers seront supprimés après ce délai."
    )
    logger.info(f"[AutoDelete] {user_id} → {secs}s")
