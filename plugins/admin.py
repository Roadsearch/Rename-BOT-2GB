"""
plugins/admin.py — Commandes admin avec barre de progression broadcast.
"""
import asyncio, logging, time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helper.database import get_all_users, total_users_count
from helper.progress import _human_size

logger       = logging.getLogger(__name__)
admin_filter = filters.user(Config.ADMIN)


def _eta(sec):
    sec = int(sec)
    if sec < 60: return f"{sec}s"
    m, s = divmod(sec, 60)
    return f"{m}m {s:02d}s"


@Client.on_message(filters.private & admin_filter & filters.command("broadcast"))
async def broadcast_cmd(bot: Client, msg: Message):
    if not msg.reply_to_message:
        await msg.reply_text("**Réponds à un message pour le diffuser.**")
        return

    users  = await get_all_users()
    total  = len(users)
    done   = failed = 0
    start  = time.time()

    status = await msg.reply_text(
        f"📡 **Diffusion lancée**\n\n"
        f"👥 Utilisateurs : `{total}`\n"
        f"⏳ En cours..."
    )
    logger.info(f"[Broadcast] Lancé par {msg.from_user.id} — {total} users")

    for i, uid in enumerate(users, 1):
        try:
            await msg.reply_to_message.copy(uid)
            done += 1
        except Exception as e:
            failed += 1
            logger.debug(f"[Broadcast] Échec {uid} : {e}")
        await asyncio.sleep(0.05)

        # Mise à jour statut toutes les 20 itérations
        if i % 20 == 0 or i == total:
            elapsed   = time.time() - start
            speed     = i / elapsed if elapsed > 0 else 0
            remaining = (total - i) / speed if speed > 0 else 0
            pct       = i * 100 / total
            from helper.progress import _build_bar
            bar = _build_bar(pct)
            try:
                await status.edit_text(
                    f"📡 **Diffusion en cours...**\n\n"
                    f"<code>[{bar}]</code> <b>{pct:.1f}%</b>\n\n"
                    f"✔️ Envoyés  : `{done}`\n"
                    f"❌ Échoués  : `{failed}`\n"
                    f"👥 Total    : `{total}`\n"
                    f"⏱️ Reste    : `{_eta(remaining)}`\n"
                    f"⏳ Écoulé  : `{_eta(elapsed)}`"
                )
            except: pass

    logger.info(f"[Broadcast] Terminé — {done} envoyés, {failed} échoués")
    await status.edit_text(
        f"✅ **Diffusion terminée !**\n\n"
        f"👥 Total    : `{total}`\n"
        f"✔️ Envoyés  : `{done}`\n"
        f"❌ Échoués  : `{failed}`\n"
        f"⏳ Durée   : `{_eta(time.time() - start)}`"
    )


@Client.on_message(filters.private & admin_filter & filters.command("status"))
async def status_cmd(bot: Client, msg: Message):
    count = await total_users_count()
    logger.info(f"[Admin] Status par {msg.from_user.id}")
    await msg.reply_text(
        f"📊 **Statut du bot**\n\n"
        f"👥 Utilisateurs : `{count}`\n"
        f"💾 Base de données : Supabase ✅\n"
        f"🌐 Serveur : Render Web Service ✅"
    )


@Client.on_message(filters.private & admin_filter & filters.command("restart"))
async def restart_cmd(bot: Client, msg: Message):
    logger.warning(f"[Admin] Redémarrage par {msg.from_user.id}")
    await msg.reply_text("♻️ **Redémarrage en cours...**")
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)
