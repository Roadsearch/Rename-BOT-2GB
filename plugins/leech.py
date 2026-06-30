"""
plugins/leech.py — Leech URL direct + yt-dlp + extraction archive avec barre pro.
"""
import os, time, logging, asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image

from helper.downloader import (
    download_direct, download_ytdlp,
    extract_archive, is_ytdlp_url, is_archive, DOWNLOAD_DIR
)
from helper.flood_control import is_flood, remaining_wait
from helper.queue_manager import acquire, release
from helper.cleanup import cleanup_files
from helper.auto_delete import schedule_delete
from helper.progress import ProgressUpdater
from helper.database import (
    get_thumbnail, get_caption, get_prefix, get_suffix,
    get_auto_delete, increment_files_count
)
from plugins.cookies import get_cookies_path

logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

_pending_archives: dict[int, dict] = {}


def human_size(num):
    for u in ["o","Ko","Mo","Go"]:
        if num < 1024: return f"{num:.1f} {u}"
        num /= 1024
    return f"{num:.1f} To"


async def _upload_file(bot, user_id, path, status_msg, caption="", thumb_path=None):
    prog = ProgressUpdater(status_msg, phase="upload", filename=os.path.basename(path))
    sent = await bot.send_document(
        user_id,
        document=path,
        file_name=os.path.basename(path),
        caption=caption,
        thumb=thumb_path,
        progress=prog,
    )
    return sent


async def _leech_pipeline(bot: Client, msg: Message, url: str, audio_only=False):
    user_id = msg.from_user.id

    if is_flood(user_id):
        wait = remaining_wait(user_id)
        err = await msg.reply_text(f"⏳ **Trop de requêtes !** Attends **{wait}s**.")
        schedule_delete(err, 30); return

    try:
        await acquire(user_id)
    except RuntimeError:
        err = await msg.reply_text("⚠️ **Un téléchargement est déjà en cours.**")
        schedule_delete(err, 30); return

    status     = await msg.reply_text("🔍 **Analyse du lien...**")
    dl_path    = None
    thumb_path = None
    extracted  = []

    try:
        # ── Détection & téléchargement ──
        if is_ytdlp_url(url) or audio_only:
            cookies = await get_cookies_path()
            prog = ProgressUpdater(status, phase="download", filename=url.split("/")[-1][:40])
            dl_path = await download_ytdlp(url, DOWNLOAD_DIR, prog, audio_only, cookies_path=cookies)
        else:
            prog = ProgressUpdater(status, phase="download")
            dl_path = await download_direct(url, DOWNLOAD_DIR, prog)

        if not dl_path or not os.path.exists(dl_path):
            await status.edit_text("❌ **Fichier introuvable après téléchargement.**"); return

        file_size = os.path.getsize(dl_path)
        if file_size > MAX_FILE_SIZE:
            await status.edit_text(
                f"❌ **Trop volumineux :** `{human_size(file_size)}` (max 2 Go)"
            ); return

        logger.info(f"[Leech] {url} → {dl_path} ({human_size(file_size)})")

        # ── Archive ? ──
        if is_archive(dl_path):
            btn = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📂 Extraire et envoyer", callback_data=f"leech_extract_{user_id}"),
                    InlineKeyboardButton("📄 Envoyer tel quel",    callback_data=f"leech_raw_{user_id}"),
                ],
                [InlineKeyboardButton("❌ Annuler", callback_data=f"leech_cancel_{user_id}")]
            ])
            await status.edit_text(
                f"📦 **Archive détectée :** `{os.path.basename(dl_path)}`\n"
                f"📏 **Taille :** `{human_size(file_size)}`\n\n"
                "Que veux-tu faire ?",
                reply_markup=btn
            )
            _pending_archives[user_id] = {"dl_path": dl_path, "status": status}
            return

        # ── Préférences utilisateur ──
        prefix    = await get_prefix(user_id) or ""
        suffix    = await get_suffix(user_id) or ""
        caption_t = await get_caption(user_id) or ""
        thumb_id  = await get_thumbnail(user_id)
        auto_del  = await get_auto_delete(user_id)

        filename  = os.path.basename(dl_path)
        name, ext = os.path.splitext(filename)
        final_name = f"{prefix}{name}{suffix}{ext}"
        final_path = os.path.join(DOWNLOAD_DIR, final_name)
        os.rename(dl_path, final_path)
        dl_path = final_path

        final_caption = ""
        if caption_t:
            try:
                final_caption = caption_t.format(
                    filename=final_name,
                    filesize=human_size(file_size),
                    duration="—",
                )
            except: final_caption = caption_t

        # ── Miniature ──
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
                logger.warning(f"[Leech] Miniature ignorée : {e}")
                cleanup_files(thumb_path); thumb_path = None

        # ── Upload ──
        await prog.set_phase("upload", filename=final_name)
        sent = await _upload_file(bot, user_id, dl_path, status, final_caption, thumb_path)
        await increment_files_count(user_id)
        await status.delete()
        schedule_delete(sent, auto_del)

    except Exception as e:
        logger.error(f"[Leech] Erreur pour {user_id} : {e}")
        err = await status.edit_text(f"❌ **Erreur :**\n`{e}`")
        schedule_delete(err, 60)
    finally:
        cleanup_files(dl_path, thumb_path)
        for f in extracted: cleanup_files(f)
        release(user_id)


# ── Commandes ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("leech"))
async def leech_cmd(bot: Client, msg: Message):
    if len(msg.command) < 2:
        await msg.reply_text(
            "**Usage :** `/leech <url>`\n\n"
            "📎 Lien direct vers un fichier.\n"
            "🎬 Pour YouTube/TikTok/etc → `/ytdl`"
        ); return
    await _leech_pipeline(bot, msg, msg.command[1].strip())


@Client.on_message(filters.private & filters.command("ytdl"))
async def ytdl_cmd(bot: Client, msg: Message):
    if len(msg.command) < 2:
        await msg.reply_text(
            "**Usage :** `/ytdl <url>`\n\n"
            "🎬 YouTube, TikTok, Instagram, Dailymotion, 1000+ sites\n"
            "🎵 Audio uniquement : `/ytdl <url> audio`"
        ); return
    parts      = msg.text.split(None, 2)
    url        = parts[1].strip()
    audio_only = len(parts) > 2 and parts[2].strip().lower() == "audio"
    await _leech_pipeline(bot, msg, url, audio_only=audio_only)


# ── Callbacks archives ────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^leech_extract_(\d+)$"))
async def cb_extract(bot, cb):
    user_id = int(cb.data.split("_")[2])
    pending = _pending_archives.pop(user_id, None)
    if not pending:
        await cb.answer("❌ Session expirée.", show_alert=True); return

    dl_path   = pending["dl_path"]
    status    = pending["status"]
    extracted = []

    try:
        prog = ProgressUpdater(status, phase="extract", filename=os.path.basename(dl_path))
        await status.edit_text("📂 **Extraction en cours...**")
        extracted = await extract_archive(dl_path, DOWNLOAD_DIR)

        if not extracted:
            await status.edit_text("❌ **Aucun fichier extrait.**"); return

        prefix   = await get_prefix(user_id) or ""
        suffix   = await get_suffix(user_id) or ""
        auto_del = await get_auto_delete(user_id)

        await status.edit_text(
            f"✅ **{len(extracted)} fichier(s) extrait(s)**\n⬆️ Upload en cours..."
        )

        for fpath in extracted:
            if os.path.getsize(fpath) > MAX_FILE_SIZE:
                await cb.message.reply_text(f"⚠️ `{os.path.basename(fpath)}` ignoré (> 2 Go)")
                continue
            fname      = os.path.basename(fpath)
            name, ext  = os.path.splitext(fname)
            final_name = f"{prefix}{name}{suffix}{ext}"
            prog_up    = ProgressUpdater(status, phase="upload", filename=final_name)
            sent = await bot.send_document(
                user_id, document=fpath, file_name=final_name, progress=prog_up
            )
            schedule_delete(sent, auto_del)
            await increment_files_count(user_id)

        await status.delete()

    except Exception as e:
        logger.error(f"[Extract CB] {e}")
        await status.edit_text(f"❌ **Erreur extraction :** `{e}`")
    finally:
        cleanup_files(dl_path)
        for f in extracted: cleanup_files(f)
        release(user_id)


@Client.on_callback_query(filters.regex(r"^leech_raw_(\d+)$"))
async def cb_raw(bot, cb):
    user_id = int(cb.data.split("_")[2])
    pending = _pending_archives.pop(user_id, None)
    if not pending:
        await cb.answer("❌ Session expirée.", show_alert=True); return

    dl_path = pending["dl_path"]
    status  = pending["status"]
    try:
        auto_del = await get_auto_delete(user_id)
        sent     = await _upload_file(bot, user_id, dl_path, status)
        await increment_files_count(user_id)
        await status.delete()
        schedule_delete(sent, auto_del)
    except Exception as e:
        await status.edit_text(f"❌ **Erreur :** `{e}`")
    finally:
        cleanup_files(dl_path)
        release(user_id)


@Client.on_callback_query(filters.regex(r"^leech_cancel_(\d+)$"))
async def cb_cancel(bot, cb):
    user_id = int(cb.data.split("_")[2])
    pending = _pending_archives.pop(user_id, None)
    if pending:
        cleanup_files(pending.get("dl_path"))
        release(user_id)
    await cb.message.edit_text("❌ **Téléchargement annulé.**")
