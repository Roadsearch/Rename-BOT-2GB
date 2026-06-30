"""
plugins/rename.py — Pipeline de renommage.

CORRECTIONS :
- Bug 1 : callback_data limité à 64 octets → stockage en dict mémoire,
          callback_data = clé courte uniquement
- Bug 2 : bot.listen() → syntaxe pyromod correcte (args positionnels)
- Bug 3 : ProgressUpdater.__call__ est maintenant synchrone (voir helper/progress.py)
"""
import os, time, asyncio, logging, uuid
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

from helper.database import (
    get_thumbnail, get_caption, get_prefix, get_suffix,
    increment_files_count, get_auto_delete,
)
from helper.queue_manager import acquire, release
from helper.flood_control import is_flood, remaining_wait
from helper.cleanup import cleanup_files
from helper.auto_delete import schedule_delete
from helper.progress import ProgressUpdater

logger       = logging.getLogger(__name__)
DOWNLOAD_DIR = "downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

# ── Stockage en mémoire (clé courte → données) ───────────────────────────────
# Résout le Bug 1 : on ne met jamais file_id ni new_name dans callback_data
_pending: dict[str, dict] = {}


def _new_key() -> str:
    """Génère une clé de 8 caractères unique."""
    return uuid.uuid4().hex[:8]


def human_size(num):
    for u in ["o", "Ko", "Mo", "Go"]:
        if num < 1024: return f"{num:.1f} {u}"
        num /= 1024
    return f"{num:.1f} To"


# ── Réception du fichier ──────────────────────────────────────────────────────

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def receive_file(bot: Client, msg: Message):
    user_id = msg.from_user.id
    media   = msg.document or msg.video or msg.audio
    if not media:
        return

    if is_flood(user_id):
        wait = remaining_wait(user_id)
        err  = await msg.reply_text(f"⏳ **Trop de requêtes !** Attends **{wait}s**.")
        schedule_delete(err, 30)
        return

    file_size = getattr(media, "file_size", 0) or 0
    if file_size > MAX_FILE_SIZE:
        await msg.reply_text(
            f"❌ **Fichier trop volumineux !**\n\n"
            f"Taille : `{human_size(file_size)}`\nMaximum : `2 Go`"
        )
        return

    try:
        await acquire(user_id)
    except RuntimeError:
        err = await msg.reply_text("⚠️ **Un fichier est déjà en cours.** Attends la fin.")
        schedule_delete(err, 30)
        return

    file_id   = media.file_id
    file_name = getattr(media, "file_name", None) or ""
    # Nettoie : si pas de nom lisible, utilise un nom générique
    if not file_name or not os.path.splitext(file_name)[1]:
        ext       = ""
        file_name = f"fichier_{media.file_unique_id[:8]}"
    else:
        _, ext = os.path.splitext(file_name)

    prefix    = await get_prefix(user_id) or ""
    suffix    = await get_suffix(user_id) or ""
    name, _   = os.path.splitext(file_name)
    suggested = f"{prefix}{name}{suffix}{ext}"

    # Stocke les données en mémoire avec une clé courte
    key = _new_key()
    _pending[key] = {
        "file_id":   file_id,
        "file_name": file_name,
        "file_size": file_size,
        "user_id":   user_id,
    }

    # Bouton inline pour skip (évite le bug /skip intercepté)
    prompt = await msg.reply_text(
        f"📁 **Fichier reçu :** `{file_name}`\n"
        f"📦 **Taille :** `{human_size(file_size)}`\n\n"
        f"✏️ **Envoie le nouveau nom** (sans extension)\n"
        f"ou appuie sur le bouton ci-dessous pour garder l'original.\n\n"
        f"**Suggéré :** `{suggested}`",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Garder le nom original", callback_data=f"rn_skip_{key}"),
        ]])
    )
    _pending[key]["prompt_id"] = prompt.id

    # ── Bug 2 corrigé : syntaxe pyromod exacte ───────────────────────────────
    # bot.listen(chat_id, filters, timeout) — args positionnels, pas keyword
    try:
        answer: Message = await bot.listen(
            msg.chat.id,
            filters.text,   # positional, pas filters=
            timeout=120,
        )
        # Supprime le prompt
        try:
            await prompt.delete()
        except:
            pass
    except asyncio.TimeoutError:
        _pending.pop(key, None)
        release(user_id)
        try:
            await prompt.edit_text("⏰ **Délai dépassé !** Renvoie le fichier pour réessayer.")
        except:
            pass
        return

    # Détermine le nouveau nom
    raw = (answer.text or "").strip()
    if raw.lower() in ("skip", "/skip"):
        new_name = file_name
    elif raw:
        new_name = raw
        _, orig_ext = os.path.splitext(file_name)
        _, new_ext  = os.path.splitext(new_name)
        if not new_ext and orig_ext:
            new_name += orig_ext
    else:
        new_name = file_name

    name2, ext2 = os.path.splitext(new_name)
    new_name = f"{prefix}{name2}{suffix}{ext2}"

    # Met à jour le pending avec le nouveau nom
    _pending[key]["new_name"] = new_name

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Document", callback_data=f"rn_doc_{key}"),
            InlineKeyboardButton("🎬 Vidéo",    callback_data=f"rn_vid_{key}"),
        ],
        [
            InlineKeyboardButton("🎵 Audio",    callback_data=f"rn_aud_{key}"),
            InlineKeyboardButton("❌ Annuler",  callback_data=f"rn_cancel_{key}"),
        ]
    ])
    await answer.reply_text(
        f"📤 **Choisis le format de sortie pour :**\n`{new_name}`",
        reply_markup=btn
    )


# ── Callback : bouton Skip ────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^rn_skip_([a-f0-9]{8})$"))
async def skip_btn_cb(bot: Client, cb: CallbackQuery):
    key  = cb.data.split("_")[2]
    data = _pending.get(key)
    if not data:
        await cb.answer("❌ Session expirée.", show_alert=True)
        return
    if cb.from_user.id != data["user_id"]:
        await cb.answer("❌ Ce n'est pas ton fichier.", show_alert=True)
        return

    await cb.answer("⏭ Nom original conservé")

    file_name = data["file_name"]
    prefix    = await get_prefix(data["user_id"]) or ""
    suffix    = await get_suffix(data["user_id"]) or ""
    name, ext = os.path.splitext(file_name)
    new_name  = f"{prefix}{name}{suffix}{ext}"
    _pending[key]["new_name"] = new_name

    # Annule le listen en cours (si pyromod le permet)
    try:
        bot.stop_listening(cb.message.chat.id)
    except:
        pass

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Document", callback_data=f"rn_doc_{key}"),
            InlineKeyboardButton("🎬 Vidéo",    callback_data=f"rn_vid_{key}"),
        ],
        [
            InlineKeyboardButton("🎵 Audio",    callback_data=f"rn_aud_{key}"),
            InlineKeyboardButton("❌ Annuler",  callback_data=f"rn_cancel_{key}"),
        ]
    ])
    await cb.message.edit_text(
        f"📤 **Choisis le format de sortie pour :**\n`{new_name}`",
        reply_markup=btn
    )


# ── Callback : annulation ─────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^rn_cancel_([a-f0-9]{8})$"))
async def cancel_rename(bot: Client, cb: CallbackQuery):
    key  = cb.data.split("_")[2]
    data = _pending.pop(key, None)
    if data:
        if cb.from_user.id != data["user_id"]:
            await cb.answer("❌ Ce n'est pas ton fichier.", show_alert=True)
            return
        release(data["user_id"])
    await cb.message.edit_text("❌ **Renommage annulé.**")
    await cb.answer()


# ── Callback : choix du format ────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^rn_(doc|vid|aud)_([a-f0-9]{8})$"))
async def format_chosen(bot: Client, cb: CallbackQuery):
    parts = cb.data.split("_")
    fmt   = parts[1]
    key   = parts[2]
    data  = _pending.pop(key, None)

    if not data:
        await cb.answer("❌ Session expirée.", show_alert=True)
        return
    if cb.from_user.id != data["user_id"]:
        await cb.answer("❌ Ce n'est pas ton fichier.", show_alert=True)
        return

    await cb.answer()
    user_id  = data["user_id"]
    file_id  = data["file_id"]
    new_name = data.get("new_name", data["file_name"])

    dl_path = thumb_path = None
    status  = await cb.message.edit_text("⏳ **Préparation...**")
    # Bug 3 corrigé : ProgressUpdater.__call__ est maintenant synchrone
    prog    = ProgressUpdater(status, phase="download", filename=new_name)

    try:
        # ── Download ──
        tmp_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{int(time.time())}_{new_name}")
        try:
            dl_path = await bot.download_media(file_id, file_name=tmp_path, progress=prog)
            logger.info(f"[Rename] Download OK : {new_name}")
        except Exception as e:
            logger.error(f"[Rename] Download échoué : {e}")
            await status.edit_text(f"❌ **Échec du téléchargement :**\n`{e}`")
            return

        # ── Miniature ──
        thumb_id = await get_thumbnail(user_id)
        if thumb_id:
            try:
                thumb_path = await bot.download_media(
                    thumb_id,
                    file_name=os.path.join(DOWNLOAD_DIR, f"thumb_{user_id}.jpg")
                )
                img = Image.open(thumb_path)
                img.thumbnail((320, 320))
                img.save(thumb_path)
            except Exception as e:
                logger.warning(f"[Rename] Miniature ignorée : {e}")
                cleanup_files(thumb_path)
                thumb_path = None

        # ── Durée ──
        duration = 0
        try:
            parser = createParser(dl_path)
            if parser:
                hm = extractMetadata(parser)
                if hm and hm.has("duration"):
                    duration = int(hm.get("duration").seconds)
        except:
            pass

        # ── Légende ──
        caption_t     = await get_caption(user_id)
        final_caption = ""
        if caption_t:
            size_bytes = os.path.getsize(dl_path)
            try:
                final_caption = caption_t.format(
                    filename=new_name,
                    filesize=human_size(size_bytes),
                    duration=f"{duration//60}:{duration%60:02d}",
                )
            except:
                final_caption = caption_t

        # ── Upload ──
        await prog.set_phase("upload", filename=new_name)
        try:
            if fmt == "doc":
                sent = await bot.send_document(
                    user_id, document=dl_path, file_name=new_name,
                    caption=final_caption, thumb=thumb_path, progress=prog,
                )
            elif fmt == "vid":
                sent = await bot.send_video(
                    user_id, video=dl_path, caption=final_caption,
                    thumb=thumb_path, duration=duration,
                    supports_streaming=True, progress=prog,
                )
            elif fmt == "aud":
                sent = await bot.send_audio(
                    user_id, audio=dl_path, caption=final_caption,
                    thumb=thumb_path, duration=duration, progress=prog,
                )
            logger.info(f"[Rename] Upload OK : {new_name} ({fmt})")
            await increment_files_count(user_id)
            auto_del = await get_auto_delete(user_id)
            if auto_del:
                schedule_delete(sent, auto_del)
        except Exception as e:
            logger.error(f"[Rename] Upload échoué : {e}")
            await status.edit_text(f"❌ **Échec de l'upload :**\n`{e}`")
            return

        await status.delete()

    finally:
        cleanup_files(dl_path, thumb_path)
        release(user_id)
