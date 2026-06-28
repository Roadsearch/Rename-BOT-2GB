"""
plugins/rename.py
Pipeline de renommage : réception fichier → choix format → download → rename → upload.
"""
import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

from config import Config, Txt
from helper.database import (
    get_thumbnail, get_caption, get_prefix, get_suffix, get_metadata
)

# Dossier de travail temporaire
DOWNLOAD_DIR = "downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Stockage temporaire en mémoire (file_id → {user_id, file_name})
pending_renames: dict[str, dict] = {}


def human_size(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def eta_str(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"


async def progress(current: int, total: int, msg: Message, start: float, action: str):
    now = time.time()
    elapsed = now - start
    speed = current / elapsed if elapsed > 0 else 0
    percent = current * 100 / total
    remaining = (total - current) / speed if speed > 0 else 0
    bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
    try:
        await msg.edit_text(
            f"**{action}...**\n"
            f"`[{bar}]` **{percent:.1f}%**\n\n"
            + Txt.PROGRESS_BAR.format(
                f"{percent:.1f}",
                human_size(current),
                human_size(total),
                human_size(speed),
                eta_str(remaining),
            )
        )
    except:
        pass


# ── Réception du fichier ─────────────────────────────────────────────────────

@Client.on_message(
    filters.private
    & (filters.document | filters.video | filters.audio)
)
async def receive_file(bot: Client, msg: Message):
    media = msg.document or msg.video or msg.audio
    if not media:
        return

    file_id   = media.file_id
    file_name = getattr(media, "file_name", None) or f"file_{media.file_unique_id}"

    # Récupère prefix/suffix de l'utilisateur
    prefix = await get_prefix(msg.from_user.id) or ""
    suffix = await get_suffix(msg.from_user.id) or ""

    # Nom proposé = prefix + nom actuel (sans extension) + suffix + extension
    name, ext = os.path.splitext(file_name)
    suggested  = f"{prefix}{name}{suffix}{ext}"

    pending_renames[f"{msg.from_user.id}_{file_id}"] = {
        "user_id":   msg.from_user.id,
        "file_id":   file_id,
        "file_name": file_name,
        "msg_id":    msg.id,
    }

    await msg.reply_text(
        f"📁 **File :** `{file_name}`\n\n"
        f"✏️ **Send me the new name** (without extension) or type `/skip` to keep the original.\n\n"
        f"**Suggested :** `{suggested}`"
    )

    # Attend la réponse du nom
    try:
        answer: Message = await bot.listen(msg.chat.id, timeout=60)
    except asyncio.TimeoutError:
        pending_renames.pop(f"{msg.from_user.id}_{file_id}", None)
        await msg.reply_text("⏰ **Timeout!** Send the file again.")
        return

    if answer.text and answer.text.strip().lower() == "/skip":
        new_name = file_name
    elif answer.text:
        new_name = answer.text.strip()
        # Ajoute l'extension si absente
        _, orig_ext = os.path.splitext(file_name)
        _, new_ext  = os.path.splitext(new_name)
        if not new_ext:
            new_name += orig_ext
    else:
        new_name = file_name

    # Applique prefix/suffix
    name2, ext2 = os.path.splitext(new_name)
    new_name = f"{prefix}{name2}{suffix}{ext2}"

    # Propose le format d'envoi
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Document", callback_data=f"fmt_doc_{file_id}_{new_name}"),
            InlineKeyboardButton("🎬 Video",    callback_data=f"fmt_vid_{file_id}_{new_name}"),
        ],
        [
            InlineKeyboardButton("🎵 Audio",    callback_data=f"fmt_aud_{file_id}_{new_name}"),
        ]
    ])
    await answer.reply_text(
        f"📤 **Choose output format for :** `{new_name}`",
        reply_markup=btn
    )


# ── Callback choix de format ─────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^fmt_(doc|vid|aud)_(.+)_(.+)$"))
async def format_chosen(bot: Client, cb: CallbackQuery):
    parts    = cb.data.split("_", 3)
    fmt      = parts[1]           # doc / vid / aud
    file_id  = parts[2]
    new_name = parts[3]
    user_id  = cb.from_user.id

    await cb.message.edit_text("⬇️ **Downloading...**")

    tmp_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{file_id}_{new_name}")
    start    = time.time()

    try:
        dl_path = await bot.download_media(
            file_id,
            file_name=tmp_path,
            progress=progress,
            progress_args=(cb.message, start, "Downloading"),
        )
    except Exception as e:
        await cb.message.edit_text(f"❌ **Download failed:** `{e}`")
        return

    # Récupère miniature & métadonnées utilisateur
    thumb_id = await get_thumbnail(user_id)
    meta     = await get_metadata(user_id)
    caption  = await get_caption(user_id)

    # Prépare la miniature locale si disponible
    thumb_path = None
    if thumb_id:
        thumb_path = await bot.download_media(thumb_id, file_name=os.path.join(DOWNLOAD_DIR, f"thumb_{user_id}.jpg"))
        # Redimensionne à 320×320 max
        try:
            img = Image.open(thumb_path)
            img.thumbnail((320, 320))
            img.save(thumb_path)
        except:
            thumb_path = None

    # Durée du fichier (vidéo/audio)
    duration = 0
    try:
        parser = createParser(dl_path)
        if parser:
            hm = extractMetadata(parser)
            if hm and hm.has("duration"):
                duration = int(hm.get("duration").seconds)
    except:
        pass

    # Caption formatée
    final_caption = ""
    if caption:
        size_bytes = os.path.getsize(dl_path)
        final_caption = caption.format(
            filename=new_name,
            filesize=human_size(size_bytes),
            duration=f"{duration//60}:{duration%60:02d}",
        )

    await cb.message.edit_text("⬆️ **Uploading...**")
    start = time.time()

    try:
        if fmt == "doc":
            await bot.send_document(
                user_id,
                document=dl_path,
                file_name=new_name,
                caption=final_caption,
                thumb=thumb_path,
                progress=progress,
                progress_args=(cb.message, start, "Uploading"),
            )
        elif fmt == "vid":
            await bot.send_video(
                user_id,
                video=dl_path,
                caption=final_caption,
                thumb=thumb_path,
                duration=duration,
                supports_streaming=True,
                progress=progress,
                progress_args=(cb.message, start, "Uploading"),
            )
        elif fmt == "aud":
            await bot.send_audio(
                user_id,
                audio=dl_path,
                caption=final_caption,
                thumb=thumb_path,
                duration=duration,
                progress=progress,
                progress_args=(cb.message, start, "Uploading"),
            )
    except Exception as e:
        await cb.message.edit_text(f"❌ **Upload failed:** `{e}`")
        return
    finally:
        # Nettoyage
        try:
            os.remove(dl_path)
        except:
            pass
        if thumb_path:
            try:
                os.remove(thumb_path)
            except:
                pass

    await cb.message.delete()
