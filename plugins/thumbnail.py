"""
plugins/thumbnail.py

CORRECTION : Évite le double déclenchement avec start_pic.py.
- Si la photo a une caption qui commence par /setpic → laissé à start_pic.py
- Sinon → sauvegardé comme miniature utilisateur
"""
import os, logging
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from helper.database import set_thumbnail, get_thumbnail, del_thumbnail
from helper.progress import ProgressUpdater

logger       = logging.getLogger(__name__)
DOWNLOAD_DIR = "downloads/"


def _is_setpic(msg: Message) -> bool:
    """Retourne True si la caption est une commande /setpic."""
    cap = (msg.caption or "").strip()
    return cap.startswith("/setpic")


@Client.on_message(filters.private & filters.photo)
async def save_thumb(bot: Client, msg: Message):
    # Laisse start_pic.py gérer les photos avec /setpic
    if _is_setpic(msg):
        return

    status = await msg.reply_text("⬇️ **Enregistrement de la miniature...**")
    prog   = ProgressUpdater(status, phase="download", filename="miniature.jpg")
    file_id = msg.photo.file_id

    try:
        path = await bot.download_media(
            file_id,
            file_name=os.path.join(DOWNLOAD_DIR, f"thumb_preview_{msg.from_user.id}.jpg"),
            progress=prog,
        )
        img = Image.open(path)
        img.thumbnail((320, 320))
        img.save(path)
        os.remove(path)
    except Exception as e:
        logger.warning(f"[Thumb] Aperçu ignoré : {e}")

    await set_thumbnail(msg.from_user.id, file_id)
    await status.edit_text("✅ **Miniature sauvegardée définitivement !**")
    logger.info(f"[Thumb] Définie pour {msg.from_user.id}")


@Client.on_message(filters.private & filters.command(["viewthumb", "view_thumb"]))
async def view_thumb(bot: Client, msg: Message):
    thumb = await get_thumbnail(msg.from_user.id)
    if not thumb:
        await msg.reply_text("❌ **Aucune miniature définie.** Envoie une photo d'abord.")
        return
    await msg.reply_photo(photo=thumb, caption="🖼️ **Ta miniature actuelle**")


@Client.on_message(filters.private & filters.command(["delthumb", "del_thumb"]))
async def delete_thumb(bot: Client, msg: Message):
    thumb = await get_thumbnail(msg.from_user.id)
    if not thumb:
        await msg.reply_text("❌ **Aucune miniature à supprimer.**")
        return
    await del_thumbnail(msg.from_user.id)
    await msg.reply_text("🗑️ **Miniature supprimée !**")
    logger.info(f"[Thumb] Supprimée pour {msg.from_user.id}")
